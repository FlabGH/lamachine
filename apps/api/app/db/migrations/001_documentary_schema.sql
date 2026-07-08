CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE document_status AS ENUM ('uploaded', 'parsed', 'chunked', 'indexed', 'failed');
CREATE TYPE run_status AS ENUM ('pending', 'running', 'succeeded', 'failed');
CREATE TYPE model_call_type AS ENUM ('llm', 'embedding', 'reranking');
CREATE TYPE output_status AS ENUM ('draft', 'fact_validated', 'politically_validated', 'published', 'rejected');

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL,
    source_type TEXT NOT NULL, -- pdf, text, url_later, manual_note
    origin TEXT,
    author TEXT,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    filename TEXT,
    mime_type TEXT NOT NULL,
    storage_path TEXT,
    sha256 TEXT NOT NULL,
    status document_status NOT NULL DEFAULT 'uploaded',
    raw_text TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sha256)
);

CREATE TABLE index_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE, -- ex: bge-m3-v1-2026-05
    embedding_provider TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    vector_collection TEXT NOT NULL,
    chunking_strategy TEXT NOT NULL,
    chunking_version TEXT NOT NULL,
    split_strategy TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    chunk_overlap INTEGER NOT NULL,
    min_chunk_size INTEGER NOT NULL,
    max_chunk_size INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    index_version_id UUID NOT NULL REFERENCES index_versions(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    token_count INTEGER,
    qdrant_point_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, index_version_id, chunk_index),
    UNIQUE (index_version_id, content_sha256)
);

CREATE TABLE runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type TEXT NOT NULL, -- ingestion, indexing, retrieval, generation
    status run_status NOT NULL DEFAULT 'pending',
    index_version_id UUID REFERENCES index_versions(id),
    input JSONB NOT NULL DEFAULT '{}',
    output JSONB NOT NULL DEFAULT '{}',
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE model_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES runs(id) ON DELETE SET NULL,
    call_type model_call_type NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT,
    input_hash TEXT,
    parameters JSONB NOT NULL DEFAULT '{}',
    response_metadata JSONB NOT NULL DEFAULT '{}',
    latency_ms INTEGER,
    token_input INTEGER,
    token_output INTEGER,
    cost_estimate NUMERIC(12,6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE retrieval_hits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id),
    rank_initial INTEGER,
    rank_final INTEGER,
    dense_score DOUBLE PRECISION,
    lexical_score DOUBLE PRECISION,
    rerank_score DOUBLE PRECISION,
    model_call_id UUID REFERENCES model_calls(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_source_id ON documents(source_id);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_index_version_id ON document_chunks(index_version_id);
CREATE INDEX idx_chunks_content_sha256 ON document_chunks(content_sha256);
CREATE INDEX idx_chunks_qdrant_point_id ON document_chunks(qdrant_point_id);
CREATE INDEX idx_runs_type_status ON runs(run_type, status);
CREATE INDEX idx_model_calls_run_id ON model_calls(run_id);
CREATE INDEX idx_retrieval_hits_run_id ON retrieval_hits(run_id);
