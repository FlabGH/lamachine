#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml


REPO_ROOT = Path(os.getenv("PHASE3_REPO_ROOT", Path(__file__).resolve().parents[1]))
API_ROOT = Path(os.getenv("PHASE3_API_ROOT", REPO_ROOT / "apps" / "api"))
DEFAULT_MANIFEST = REPO_ROOT / "corpus" / "poc_ia" / "manifest.yaml"
DEFAULT_FILES_DIR = REPO_ROOT / "corpus" / "poc_ia" / "files"
DEFAULT_QUERY_CANDIDATES = [
    REPO_ROOT / "corpus" / "poc_ia" / "evaluation_queries.yaml",
    REPO_ROOT / "corpus" / "evaluation_queries.yaml",
]
DEFAULT_REPORT = REPO_ROOT / "artifacts" / "phase3_retrieval_eval_report.md"


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    query: str
    intent: str
    expected_source_codes: set[str]
    expected_document_ids: set[str]
    expected_theme_tags: set[str]
    expected_pages: set[int]


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _normalize_local_service_urls() -> None:
    if Path("/.dockerenv").exists():
        return

    database_url = os.environ.get("DATABASE_URL", "")
    if "@postgres:" in database_url:
        os.environ["DATABASE_URL"] = database_url.replace("@postgres:", "@localhost:")

    qdrant_url = os.environ.get("QDRANT_URL", "")
    if "://qdrant:" in qdrant_url:
        os.environ["QDRANT_URL"] = qdrant_url.replace("://qdrant:", "://localhost:")


def _configure_imports() -> None:
    sys.path.insert(0, str(API_ROOT))


def _log(message: str) -> None:
    print(message, flush=True)


def _resolve_queries_path(path: str | None) -> Path:
    if path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else REPO_ROOT / candidate

    for candidate in DEFAULT_QUERY_CANDIDATES:
        if candidate.exists():
            return candidate
    return DEFAULT_QUERY_CANDIDATES[0]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML object: {path}")
    return data


def _validate_manifest(manifest_path: Path, files_dir: Path) -> list[dict[str, Any]]:
    data = _load_yaml(manifest_path)
    documents = data.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("manifest must contain a non-empty documents list")

    normalized_documents = []
    errors = []
    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            errors.append(f"document[{index}] must be an object")
            continue

        file_name = document.get("file")
        if not isinstance(file_name, str) or not file_name.strip():
            errors.append(f"document[{index}] missing file")
            continue

        file_path = files_dir / file_name
        if not file_path.exists():
            errors.append(f"{file_name}: file not found in {files_dir}")
            continue

        metadata = {key: value for key, value in document.items() if key != "file"}
        if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
            errors.append(f"{file_name}: title must be a non-empty string")
            continue
        if (
            not isinstance(metadata.get("source_code"), str)
            or not metadata["source_code"].strip()
        ):
            errors.append(f"{file_name}: source_code must be a non-empty string")
            continue

        normalized_documents.append(
            {
                "file": file_name,
                "file_path": file_path,
                "metadata": metadata,
            }
        )

    if errors:
        raise ValueError("Manifest validation failed:\n- " + "\n- ".join(errors))

    return normalized_documents


def _load_queries(path: Path) -> list[QuerySpec]:
    data = _load_yaml(path)
    queries = data.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("evaluation queries file must contain a non-empty queries list")

    result = []
    for item in queries:
        if not isinstance(item, dict):
            raise ValueError("query entries must be objects")
        result.append(
            QuerySpec(
                query_id=str(item["id"]),
                query=str(item["query"]),
                intent=str(item.get("intent", "")),
                expected_source_codes={str(v).lower() for v in item.get("expected_source_codes", [])},
                expected_document_ids={str(v) for v in item.get("expected_document_ids", [])},
                expected_theme_tags={str(v) for v in item.get("expected_theme_tags", [])},
                expected_pages=_normalize_expected_pages(item.get("expected_pages", [])),
            )
        )
    return result


def _normalize_expected_pages(value: Any) -> set[int]:
    if value is None:
        return set()
    if not isinstance(value, list):
        raise ValueError("expected_pages must be a list")

    pages: set[int] = set()
    for item in value:
        if isinstance(item, int):
            pages.add(item)
            continue
        if isinstance(item, str):
            raw = item.strip()
            if not raw:
                continue
            if "-" in raw:
                start_raw, end_raw = raw.split("-", 1)
                start = int(start_raw.strip())
                end = int(end_raw.strip())
                pages.update(range(min(start, end), max(start, end) + 1))
            else:
                pages.add(int(raw))
            continue
        raise ValueError("expected_pages entries must be integers or page ranges")
    return pages


def _short_excerpt(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _first_hit_rank(results: list[dict[str, Any]], key: str, expected: set[str]) -> int | None:
    for result in results:
        value = result.get(key)
        if isinstance(value, list):
            if expected & set(value):
                return int(result["rank"])
        elif value in expected:
            return int(result["rank"])
    return None


def _recall_at(results: list[dict[str, Any]], key: str, expected: set[str], k: int) -> bool:
    if not expected:
        return True
    return _first_hit_rank(results[:k], key, expected) is not None


def _reciprocal_rank(results: list[dict[str, Any]], key: str, expected: set[str], k: int) -> float:
    if not expected:
        return 1.0
    rank = _first_hit_rank(results[:k], key, expected)
    return 0.0 if rank is None else 1.0 / rank


def _page_hit_at(results: list[dict[str, Any]], expected_pages: set[int], k: int) -> bool:
    if not expected_pages:
        return True

    for result in results[:k]:
        page_start = result.get("page_start")
        page_end = result.get("page_end")
        if page_start is None or page_end is None:
            continue
        covered_pages = set(range(int(page_start), int(page_end) + 1))
        if covered_pages & expected_pages:
            return True
    return False


def _page_coverage_rate(results: list[dict[str, Any]], k: int) -> float:
    if not results[:k]:
        return 0.0
    with_pages = sum(
        1
        for result in results[:k]
        if result.get("page_start") is not None and result.get("page_end") is not None
    )
    return with_pages / len(results[:k])


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


async def _ingest_document(document: dict[str, Any]) -> UUID:
    from app.db import get_connection
    from app.services.ai.factory import get_ocr_client
    from app.services.documentary.ingestion import (
        extract_pdf_with_optional_ocr,
        save_uploaded_file,
        sha256_bytes,
    )
    from app.services.documentary.metadata_registry import MetadataScope, get_metadata_registry
    from app.services.documentary.metadata_validation import validate_metadata

    metadata = dict(document["metadata"])
    file_path: Path = document["file_path"]
    content = file_path.read_bytes()
    digest = sha256_bytes(content)
    storage_path, _ = save_uploaded_file(file_path.name, content)
    extraction = await extract_pdf_with_optional_ocr(storage_path, ocr_client=get_ocr_client())
    source_id = uuid4()
    document_id = uuid4()
    document_metadata = validate_metadata(
        {
            **metadata,
            "source_id": str(source_id),
            "document_id": str(document_id),
            "mime_type": "application/pdf",
            "filename": file_path.name,
        },
        scope=MetadataScope.document,
        registry=get_metadata_registry(),
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (id, code, source_type, origin)
                VALUES (%s, %s, 'pdf', %s)
                RETURNING id
                """,
                (source_id, metadata["source_code"], "phase3_step7_manifest"),
            )
            source_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO documents (
                    id, source_id, title, filename, mime_type,
                    storage_path, sha256, status, raw_text, metadata
                )
                VALUES (%s, %s, %s, %s, 'application/pdf', %s, %s, 'parsed', %s, %s::jsonb)
                RETURNING id
                """,
                (
                    document_id,
                    source_id,
                    metadata["title"],
                    file_path.name,
                    storage_path,
                    digest,
                    extraction.raw_text,
                    json.dumps(document_metadata, ensure_ascii=False),
                ),
            )
            document_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO runs (run_type, status, input, output, finished_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, now())
                """,
                (
                    "ingestion",
                    "succeeded",
                    json.dumps(
                        {
                            "filename": file_path.name,
                            "source_code": metadata["source_code"],
                            "metadata": document_metadata,
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "document_id": str(document_id),
                            **extraction.metadata(),
                        },
                        ensure_ascii=False,
                    ),
                ),
            )

    return document_id


def _create_index_version(
    index_name: str,
    vector_collection: str,
    chunking_config,
) -> UUID:
    from app.db import get_connection
    from app.services.ai.factory import get_embedding_client

    embedding_client = get_embedding_client()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO index_versions (
                    name,
                    embedding_provider,
                    embedding_model,
                    embedding_dimension,
                    vector_collection,
                    chunking_strategy,
                    chunking_version,
                    split_strategy,
                    chunk_size,
                    chunk_overlap,
                    min_chunk_size,
                    max_chunk_size,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false)
                ON CONFLICT (name) DO UPDATE
                SET embedding_provider = EXCLUDED.embedding_provider,
                    embedding_model = EXCLUDED.embedding_model,
                    embedding_dimension = EXCLUDED.embedding_dimension,
                    vector_collection = EXCLUDED.vector_collection,
                    chunking_strategy = EXCLUDED.chunking_strategy,
                    chunking_version = EXCLUDED.chunking_version,
                    split_strategy = EXCLUDED.split_strategy,
                    chunk_size = EXCLUDED.chunk_size,
                    chunk_overlap = EXCLUDED.chunk_overlap,
                    min_chunk_size = EXCLUDED.min_chunk_size,
                    max_chunk_size = EXCLUDED.max_chunk_size
                RETURNING id
                """,
                (
                    index_name,
                    embedding_client.provider,
                    embedding_client.model,
                    embedding_client.dimension,
                    vector_collection,
                    chunking_config.chunking_version,
                    chunking_config.chunking_version,
                    chunking_config.split_strategy,
                    chunking_config.chunk_size,
                    chunking_config.chunk_overlap,
                    chunking_config.min_chunk_size,
                    chunking_config.max_chunk_size,
                ),
            )
            return cur.fetchone()["id"]


def _chunking_config_from_args(args: argparse.Namespace):
    from app.services.documentary.chunking import (
        DEFAULT_CHUNKING_VERSION,
        DEFAULT_SPLIT_STRATEGY,
        STRUCTURAL_CHUNKING_VERSION,
        STRUCTURAL_SPLIT_STRATEGY,
        ChunkingConfig,
    )

    split_strategy = args.split_strategy
    chunking_version = args.chunking_version
    if chunking_version is None:
        chunking_version = (
            STRUCTURAL_CHUNKING_VERSION
            if split_strategy == STRUCTURAL_SPLIT_STRATEGY
            else DEFAULT_CHUNKING_VERSION
        )

    return ChunkingConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        split_strategy=split_strategy or DEFAULT_SPLIT_STRATEGY,
        min_chunk_size=args.min_chunk_size,
        max_chunk_size=args.max_chunk_size,
        chunking_version=chunking_version,
    )


def _get_index_version(index_version_id: UUID) -> dict[str, Any]:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, vector_collection
                FROM index_versions
                WHERE id = %s
                """,
                (index_version_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown index_version_id: {index_version_id}")
            return row


async def _index_documents(document_ids: list[UUID], index_version_id: UUID) -> None:
    from app.api.documentary import IndexRequest, index_document

    for document_id in document_ids:
        await index_document(
            IndexRequest(document_id=document_id, index_version_id=index_version_id)
        )


async def _run_query(
    query: QuerySpec,
    index_version_id: UUID,
    top_k: int,
    rerank_top_k: int,
) -> dict[str, Any]:
    from app.api.documentary import SearchRequest, search_documents
    from app.db import get_connection

    start_time = time.perf_counter()
    response = await search_documents(
        SearchRequest(
            query=query.query,
            index_version_id=index_version_id,
            top_k=top_k,
            rerank_top_k=rerank_top_k,
        )
    )
    latency_ms = (time.perf_counter() - start_time) * 1000

    scores_by_chunk_id: dict[str, dict[str, Any]] = {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, rank_initial, rank_final, dense_score, lexical_score, rerank_score
                FROM retrieval_hits
                WHERE run_id = %s
                """,
                (response.run_id,),
            )
            for row in cur.fetchall():
                scores_by_chunk_id[str(row["chunk_id"])] = row

    results = []
    for hit in response.hits[:top_k]:
        metadata = hit.metadata or {}
        theme_tags = metadata.get("theme_tags") or []
        if not isinstance(theme_tags, list):
            theme_tags = []
        score_row = scores_by_chunk_id.get(str(hit.chunk_id), {})
        results.append(
            {
                "rank": hit.rank,
                "rank_initial": score_row.get("rank_initial"),
                "score": hit.score,
                "dense_score": score_row.get("dense_score"),
                "lexical_score": score_row.get("lexical_score"),
                "rerank_score": score_row.get("rerank_score"),
                "chunk_id": str(hit.chunk_id),
                "document_id": str(hit.document_id),
                "source_code": metadata.get("source_code"),
                "theme_tags": theme_tags,
                "page_start": metadata.get("page_start"),
                "page_end": metadata.get("page_end"),
                "excerpt": _short_excerpt(hit.content),
            }
        )

    return {
        "query": query,
        "run_id": str(response.run_id),
        "results": results,
        "source_hit": _recall_at(results, "source_code", query.expected_source_codes, top_k),
        "document_hit": (
            _recall_at(results, "document_id", query.expected_document_ids, top_k)
            if query.expected_document_ids
            else _recall_at(results, "source_code", query.expected_source_codes, top_k)
        ),
        "page_hit": _page_hit_at(results, query.expected_pages, top_k),
        "source_mrr": _reciprocal_rank(results, "source_code", query.expected_source_codes, top_k),
        "document_mrr": (
            _reciprocal_rank(results, "document_id", query.expected_document_ids, top_k)
            if query.expected_document_ids
            else _reciprocal_rank(results, "source_code", query.expected_source_codes, top_k)
        ),
        "page_coverage_rate": _page_coverage_rate(results, top_k),
        "latency_ms": latency_ms,
    }


def _chunk_quality_metrics(index_version_id: UUID) -> dict[str, float]:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE COALESCE(metadata->>'source_code', '') = ''
                    ) AS missing_source_code,
                    COUNT(*) FILTER (
                        WHERE page_start IS NULL OR page_end IS NULL
                    ) AS missing_page_range
                FROM document_chunks
                WHERE index_version_id = %s
                """,
                (index_version_id,),
            )
            row = cur.fetchone()

    total = int(row["total"] or 0)
    if total == 0:
        return {
            "total_chunks": 0,
            "missing_source_code_rate": 0.0,
            "missing_page_range_rate": 0.0,
        }

    return {
        "total_chunks": total,
        "missing_source_code_rate": int(row["missing_source_code"]) / total,
        "missing_page_range_rate": int(row["missing_page_range"]) / total,
    }


def _write_report(
    *,
    report_path: Path,
    manifest_path: Path,
    queries_path: Path,
    index_version_id: UUID,
    vector_collection: str,
    query_reports: list[dict[str, Any]],
    chunk_metrics: dict[str, float],
    top_k: int,
    rerank_top_k: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    query_count = len(query_reports)
    source_recall = sum(1 for item in query_reports if item["source_hit"]) / query_count
    document_recall = sum(1 for item in query_reports if item["document_hit"]) / query_count
    page_recall = sum(1 for item in query_reports if item["page_hit"]) / query_count
    source_mrr = sum(float(item["source_mrr"]) for item in query_reports) / query_count
    document_mrr = sum(float(item["document_mrr"]) for item in query_reports) / query_count
    average_page_coverage = _average(
        [float(item["page_coverage_rate"]) for item in query_reports]
    )
    average_latency_ms = _average([float(item["latency_ms"]) for item in query_reports])

    lines = [
        "# Phase 3 Retrieval Evaluation",
        "",
        f"Generated at: `{datetime.now(UTC).isoformat()}`",
        f"Manifest: `{manifest_path.relative_to(REPO_ROOT)}`",
        f"Evaluation queries: `{queries_path.relative_to(REPO_ROOT)}`",
        f"Index version id: `{index_version_id}`",
        f"Vector collection: `{vector_collection}`",
        f"Top k: `{top_k}`",
        f"Rerank top k: `{rerank_top_k}`",
        "",
        "## Metrics",
        "",
        f"- Recall@{top_k} source_code: {source_recall:.3f}",
        f"- Recall@{top_k} document: {document_recall:.3f}",
        f"- Recall@{top_k} page: {page_recall:.3f}",
        f"- MRR source_code: {source_mrr:.3f}",
        f"- MRR document: {document_mrr:.3f}",
        f"- Page coverage@{top_k}: {average_page_coverage:.3f}",
        f"- Latence moyenne recherche: {average_latency_ms:.1f} ms",
        f"- Total chunks: {int(chunk_metrics['total_chunks'])}",
        f"- Chunks sans source_code: {chunk_metrics['missing_source_code_rate']:.3f}",
        f"- Chunks sans page_start/page_end: {chunk_metrics['missing_page_range_rate']:.3f}",
        "",
        "## Query Results",
        "",
    ]

    for item in query_reports:
        query: QuerySpec = item["query"]
        lines.extend(
            [
                f"### {query.query_id}",
                "",
                f"- Query: {query.query}",
                f"- Intent: `{query.intent}`",
                f"- Expected source_codes: `{', '.join(sorted(query.expected_source_codes))}`",
                f"- Expected document_ids: `{', '.join(sorted(query.expected_document_ids))}`",
                f"- Expected theme_tags: `{', '.join(sorted(query.expected_theme_tags))}`",
                f"- Expected pages: `{', '.join(str(page) for page in sorted(query.expected_pages))}`",
                f"- Hit source_code @{top_k}: {'yes' if item['source_hit'] else 'no'}",
                f"- Hit document @{top_k}: {'yes' if item['document_hit'] else 'no'}",
                f"- Hit page @{top_k}: {'yes' if item['page_hit'] else 'no'}",
                f"- Page coverage @{top_k}: {item['page_coverage_rate']:.3f}",
                f"- Search latency: {item['latency_ms']:.1f} ms",
                "",
                "| rank | initial | score | dense | lexical | rerank | source_code | theme_tags | pages | document_id | extrait | commentaire |",
                "|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|",
            ]
        )

        for result in item["results"]:
            source_hit = result["source_code"] in query.expected_source_codes
            theme_hit = bool(set(result["theme_tags"]) & query.expected_theme_tags)
            comment = (
                f"source={'yes' if source_hit else 'no'}; "
                f"theme={'yes' if theme_hit else 'no'}"
            )
            pages = ""
            if result["page_start"] is not None or result["page_end"] is not None:
                pages = f"{result['page_start']}-{result['page_end']}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _markdown_escape(result["rank"]),
                        _markdown_escape(result["rank_initial"] or ""),
                        _markdown_escape(
                            f"{result['score']:.4f}"
                            if isinstance(result["score"], float)
                            else result["score"]
                        ),
                        _markdown_escape(
                            f"{result['dense_score']:.4f}"
                            if isinstance(result["dense_score"], float)
                            else result["dense_score"]
                        ),
                        _markdown_escape(
                            f"{result['lexical_score']:.4f}"
                            if isinstance(result["lexical_score"], float)
                            else result["lexical_score"]
                        ),
                        _markdown_escape(
                            f"{result['rerank_score']:.4f}"
                            if isinstance(result["rerank_score"], float)
                            else result["rerank_score"]
                        ),
                        _markdown_escape(result["source_code"]),
                        _markdown_escape(", ".join(result["theme_tags"])),
                        _markdown_escape(pages),
                        _markdown_escape(result["document_id"]),
                        _markdown_escape(result["excerpt"]),
                        _markdown_escape(comment),
                    ]
                )
                + " |"
            )
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


async def _run(args: argparse.Namespace) -> Path:
    _load_dotenv(REPO_ROOT / ".env")
    _normalize_local_service_urls()
    _configure_imports()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = REPO_ROOT / manifest_path
    files_dir = Path(args.files_dir)
    if not files_dir.is_absolute():
        files_dir = REPO_ROOT / files_dir
    queries_path = _resolve_queries_path(args.queries)
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path

    _log(f"Validating manifest: {manifest_path}")
    documents = _validate_manifest(manifest_path, files_dir)
    _log(f"Loading evaluation queries: {queries_path}")
    queries = _load_queries(queries_path)

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    index_name = args.index_name or f"phase3-step7-eval-{timestamp}"
    vector_collection = args.vector_collection or f"phase3_step7_eval_{timestamp}"
    chunking_config = _chunking_config_from_args(args)

    if args.reuse_index_version_id:
        index_version_id = UUID(args.reuse_index_version_id)
        index_version = _get_index_version(index_version_id)
        vector_collection = index_version["vector_collection"]
        _log(
            "Reusing index version: "
            f"{index_version['name']} ({index_version_id})"
        )
    else:
        document_ids = []
        for index, document in enumerate(documents, start=1):
            _log(
                f"Ingesting document {index}/{len(documents)}: "
                f"{document['metadata']['source_code']} ({document['file']})"
            )
            document_ids.append(await _ingest_document(document))

        _log(f"Creating index version: {index_name}")
        index_version_id = _create_index_version(
            index_name,
            vector_collection,
            chunking_config,
        )
        _log(f"Indexing {len(document_ids)} documents into {vector_collection}")
        await _index_documents(document_ids, index_version_id)

    query_reports = []
    for index, query in enumerate(queries, start=1):
        _log(f"Running query {index}/{len(queries)}: {query.query_id}")
        query_reports.append(
            await _run_query(
                query,
                index_version_id,
                args.top_k,
                args.rerank_top_k,
            )
        )

    _log("Computing chunk quality metrics")
    chunk_metrics = _chunk_quality_metrics(index_version_id)
    _log(f"Writing report: {report_path}")
    _write_report(
        report_path=report_path,
        manifest_path=manifest_path,
        queries_path=queries_path,
        index_version_id=index_version_id,
        vector_collection=vector_collection,
        query_reports=query_reports,
        chunk_metrics=chunk_metrics,
        top_k=args.top_k,
        rerank_top_k=args.rerank_top_k,
    )
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 3 retrieval evaluation.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST.relative_to(REPO_ROOT)))
    parser.add_argument("--queries", default=None)
    parser.add_argument("--files-dir", default=str(DEFAULT_FILES_DIR.relative_to(REPO_ROOT)))
    parser.add_argument("--report", default=str(DEFAULT_REPORT.relative_to(REPO_ROOT)))
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--rerank-top-k", type=int, default=20)
    parser.add_argument("--index-name", default=None)
    parser.add_argument("--vector-collection", default=None)
    parser.add_argument("--reuse-index-version-id", default=None)
    parser.add_argument(
        "--split-strategy",
        choices=["word_window", "section_aware_window"],
        default="word_window",
    )
    parser.add_argument("--chunking-version", default=None)
    parser.add_argument("--chunk-size", type=int, default=450)
    parser.add_argument("--chunk-overlap", type=int, default=80)
    parser.add_argument("--min-chunk-size", type=int, default=80)
    parser.add_argument("--max-chunk-size", type=int, default=650)
    args = parser.parse_args()

    report_path = asyncio.run(_run(args))
    print(report_path)


if __name__ == "__main__":
    main()
