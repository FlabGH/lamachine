-- Current LaPythie schema for database reinitialization.
-- This file consolidates the base documentary schema and structured objects
-- storage so a reset can apply one SQL file.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE document_status AS ENUM ('uploaded', 'parsed', 'chunked', 'indexed', 'failed');
CREATE TYPE run_status AS ENUM ('pending', 'running', 'succeeded', 'failed');
CREATE TYPE model_call_type AS ENUM ('llm', 'embedding', 'reranking');
CREATE TYPE output_status AS ENUM ('draft', 'fact_validated', 'politically_validated', 'published', 'rejected');

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL,
    source_type TEXT NOT NULL,
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
    name TEXT NOT NULL UNIQUE,
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
    run_type TEXT NOT NULL,
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

CREATE TABLE structured_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    object_type TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    source_span JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    producer JSONB NOT NULL DEFAULT '{}',
    confidence DOUBLE PRECISION,
    qdrant_point_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (btrim(object_type) <> ''),
    CHECK (btrim(content) <> ''),
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE TABLE structured_object_chunks (
    structured_object_id UUID NOT NULL REFERENCES structured_objects(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (structured_object_id, chunk_id)
);

CREATE INDEX idx_documents_source_id ON documents(source_id);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_index_version_id ON document_chunks(index_version_id);
CREATE INDEX idx_chunks_content_sha256 ON document_chunks(content_sha256);
CREATE INDEX idx_chunks_qdrant_point_id ON document_chunks(qdrant_point_id);
CREATE INDEX idx_runs_type_status ON runs(run_type, status);
CREATE INDEX idx_model_calls_run_id ON model_calls(run_id);
CREATE INDEX idx_retrieval_hits_run_id ON retrieval_hits(run_id);
CREATE INDEX idx_structured_objects_document_id ON structured_objects (document_id);
CREATE INDEX idx_structured_objects_object_type ON structured_objects (object_type);
CREATE INDEX idx_structured_objects_metadata ON structured_objects USING GIN (metadata);
CREATE INDEX idx_structured_objects_qdrant_point_id ON structured_objects (qdrant_point_id);
CREATE INDEX idx_structured_object_chunks_chunk_id ON structured_object_chunks (chunk_id);
