-- Step 4: structured documentary objects.
-- The objects are stored separately from chunks to keep extraction units
-- distinct from retrieval chunks.

CREATE TABLE IF NOT EXISTS structured_objects (
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

CREATE TABLE IF NOT EXISTS structured_object_chunks (
    structured_object_id UUID NOT NULL REFERENCES structured_objects(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (structured_object_id, chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_structured_objects_document_id
ON structured_objects (document_id);

CREATE INDEX IF NOT EXISTS idx_structured_objects_object_type
ON structured_objects (object_type);

CREATE INDEX IF NOT EXISTS idx_structured_objects_metadata
ON structured_objects USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_structured_objects_qdrant_point_id
ON structured_objects (qdrant_point_id);

CREATE INDEX IF NOT EXISTS idx_structured_object_chunks_chunk_id
ON structured_object_chunks (chunk_id);
