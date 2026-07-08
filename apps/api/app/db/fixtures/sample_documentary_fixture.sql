INSERT INTO sources (id, code, source_type, origin, author)
VALUES (
    '10000000-0000-0000-0000-000000000001',
    'sample',
    'text',
    'fixture',
    'LaPythie'
)
ON CONFLICT (code) DO NOTHING;

INSERT INTO documents (
    id,
    source_id,
    title,
    filename,
    mime_type,
    sha256,
    raw_text,
    metadata
)
VALUES (
    '10000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    'Sample document',
    'sample.txt',
    'text/plain',
    'sample-document-hash',
    'A sample document used to validate the generic documentary schema.',
    '{"title": "Sample document", "source_code": "sample", "theme_tags": ["sample"]}'::jsonb
)
ON CONFLICT (sha256) DO NOTHING;

INSERT INTO index_versions (
    id,
    name,
    embedding_provider,
    embedding_model,
    embedding_dimension,
    vector_collection,
    chunking_version,
    split_strategy,
    chunk_size,
    chunk_overlap,
    min_chunk_size,
    max_chunk_size,
    is_active
)
VALUES (
    '10000000-0000-0000-0000-000000000003',
    'sample_fixture',
    'local',
    'hash-embedding-v1',
    384,
    'sample_fixture',
    'generic_window_v1',
    'generic_window_v1',
    450,
    80,
    80,
    650,
    true
)
ON CONFLICT (name) DO NOTHING;
