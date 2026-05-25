-- Phase 3 step 1: documentary metadata contract helpers.
-- This migration is intentionally limited to JSONB expression indexes.
-- It does not add columns or constraints to avoid breaking existing POC data.

CREATE INDEX IF NOT EXISTS idx_chunks_metadata_source_id
ON document_chunks ((metadata->>'source_id'));

CREATE INDEX IF NOT EXISTS idx_chunks_metadata_vector_collection
ON document_chunks ((metadata->>'vector_collection'));

CREATE INDEX IF NOT EXISTS idx_chunks_metadata_document_title
ON document_chunks ((metadata->>'document_title'));
