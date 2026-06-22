#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS_DIR = REPO_ROOT / "artifacts"
METRIC_RE = re.compile(r"^- (?P<name>[^:]+): (?P<value>.+)$")


def _run_eval(report_path: Path, *, structural: bool, args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "retrieval_eval.py"),
        "--report",
        str(report_path.relative_to(REPO_ROOT)),
        "--top-k",
        str(args.top_k),
        "--rerank-top-k",
        str(args.rerank_top_k),
    ]
    if args.manifest:
        command.extend(["--manifest", args.manifest])
    if args.queries:
        command.extend(["--queries", args.queries])
    if args.files_dir:
        command.extend(["--files-dir", args.files_dir])
    if structural:
        command.extend(
            [
                "--index-name",
                f"chunking-structural-eval-{args.timestamp}",
                "--vector-collection",
                f"chunking_structural_eval_{args.timestamp}",
                "--split-strategy",
                "section_aware_window",
                "--chunking-version",
                "section_aware_window_v1",
            ]
        )
    else:
        command.extend(
            [
                "--index-name",
                f"chunking-baseline-eval-{args.timestamp}",
                "--vector-collection",
                f"chunking_baseline_eval_{args.timestamp}",
            ]
        )

    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _parse_report(report_path: Path) -> dict[str, str]:
    metrics: dict[str, str] = {}
    current_query: str | None = None
    failed_queries: set[str] = set()
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            current_query = line.removeprefix("### ").strip()
            continue
        metric = METRIC_RE.match(line)
        if metric and current_query is None:
            metrics[metric.group("name")] = metric.group("value")
        if current_query and (
            "Hit source_code @" in line
        ) and line.endswith("no"):
            failed_queries.add(current_query)
    metrics["Failed source queries"] = ", ".join(sorted(failed_queries)) or "none"
    return metrics


def _write_comparison(
    report_path: Path,
    *,
    baseline_report: Path,
    structural_report: Path,
) -> None:
    baseline = _parse_report(baseline_report)
    structural = _parse_report(structural_report)
    metric_names = sorted(set(baseline) | set(structural))
    lines = [
        "# Chunking Comparison",
        "",
        f"Generated at: `{datetime.now(UTC).isoformat()}`",
        f"Baseline report: `{baseline_report.relative_to(REPO_ROOT)}`",
        f"Structural report: `{structural_report.relative_to(REPO_ROOT)}`",
        "",
        "| Metric | word_window_v1 | section_aware_window_v1 |",
        "|---|---:|---:|",
    ]
    for metric_name in metric_names:
        lines.append(
            "| "
            + " | ".join(
                [
                    metric_name,
                    baseline.get(metric_name, ""),
                    structural.get(metric_name, ""),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation checklist",
            "",
            "- Check source recall and MRR before considering promotion.",
            "- Check total chunks and page coverage for cost and citation quality.",
            "- Inspect failed source queries before replacing the active index.",
            "- Do not promote this index automatically; use the internal promotion endpoint after validation.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    parser = argparse.ArgumentParser(
        description="Compare baseline and structural chunking reports."
    )
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--queries", default=None)
    parser.add_argument("--files-dir", default=None)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--rerank-top-k", type=int, default=20)
    parser.add_argument("--timestamp", default=timestamp)
    parser.add_argument("--baseline-report", default=None)
    parser.add_argument("--structural-report", default=None)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument(
        "--report",
        default=f"artifacts/chunking_comparison_{timestamp}.md",
    )
    args = parser.parse_args()

    baseline_report = Path(
        args.baseline_report
        or f"artifacts/chunking_baseline_{args.timestamp}.md"
    )
    structural_report = Path(
        args.structural_report
        or f"artifacts/chunking_structural_{args.timestamp}.md"
    )
    output_report = Path(args.report)
    if not baseline_report.is_absolute():
        baseline_report = REPO_ROOT / baseline_report
    if not structural_report.is_absolute():
        structural_report = REPO_ROOT / structural_report
    if not output_report.is_absolute():
        output_report = REPO_ROOT / output_report

    if not args.skip_run:
        _run_eval(baseline_report, structural=False, args=args)
        _run_eval(structural_report, structural=True, args=args)

    _write_comparison(
        output_report,
        baseline_report=baseline_report,
        structural_report=structural_report,
    )
    print(output_report)


if __name__ == "__main__":
    main()
