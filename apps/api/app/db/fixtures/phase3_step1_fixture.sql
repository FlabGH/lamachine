-- Fictional documentary metadata contract fixture.
-- Intended for manual local/VPS checks only. Do not load into production data
-- without explicit validation.

INSERT INTO sources (
    id,
    code,
    source_type,
    origin,
    author
)
VALUES (
    '10000000-0000-0000-0000-000000000001',
    'source_fictive_phase_3',
    'text',
    'fixture',
    'LaMachine POC'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO documents (
    id,
    source_id,
    title,
    mime_type,
    sha256,
    status,
    raw_text,
    metadata
)
VALUES (
    '10000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000001',
    'Document fictif Phase 3',
    'text/plain',
    'phase3-step1-document-sha256',
    'indexed',
    '[PAGE 1] Premier passage fictif pour contrôler les métadonnées. [PAGE 2] Deuxième passage fictif.',
    '{"fixture": "phase3_step1"}'::jsonb
)
ON CONFLICT (sha256) DO NOTHING;

INSERT INTO index_versions (
    id,
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
VALUES (
    '10000000-0000-0000-0000-000000000003',
    'phase3-step1-fixture-local',
    'local',
    'hash-embedding-v1',
    384,
    'phase3_step1_fixture',
    'generic_window_v1',
    'generic_window_v1',
    'generic_window_v1',
    80,
    10,
    20,
    120,
    false
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO document_chunks (
    id,
    document_id,
    index_version_id,
    chunk_index,
    content,
    content_sha256,
    page_start,
    page_end,
    token_count,
    metadata
)
VALUES
(
    '10000000-0000-0000-0000-000000000004',
    '10000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000003',
    0,
    'Premier passage fictif pour contrôler les métadonnées.',
    'phase3-step1-chunk-0-sha256',
    1,
    1,
    7,
    '{
        "source_id": "10000000-0000-0000-0000-000000000001",
        "document_id": "10000000-0000-0000-0000-000000000002",
        "parent_document_id": "10000000-0000-0000-0000-000000000002",
        "document_title": "Document fictif Phase 3",
        "source_code": "source_fictive_phase_3",
        "role_documentaire": "source_factuelle",
        "statut_metadonnees": "brouillon",
        "page_start": 1,
        "page_end": 1,
        "content_sha256": "phase3-step1-chunk-0-sha256",
        "content_hash": "phase3-step1-chunk-0-sha256",
        "index_version_id": "10000000-0000-0000-0000-000000000003",
        "vector_collection": "phase3_step1_fixture",
        "chunking_version": "generic_window_v1",
        "split_strategy": "generic_window_v1"
    }'::jsonb
),
(
    '10000000-0000-0000-0000-000000000005',
    '10000000-0000-0000-0000-000000000002',
    '10000000-0000-0000-0000-000000000003',
    1,
    'Deuxième passage fictif.',
    'phase3-step1-chunk-1-sha256',
    NULL,
    NULL,
    3,
    '{
        "source_id": "10000000-0000-0000-0000-000000000001",
        "document_id": "10000000-0000-0000-0000-000000000002",
        "parent_document_id": "10000000-0000-0000-0000-000000000002",
        "document_title": "Document fictif Phase 3",
        "source_code": "source_fictive_phase_3",
        "role_documentaire": "source_factuelle",
        "statut_metadonnees": "brouillon",
        "section": "body",
        "content_sha256": "phase3-step1-chunk-1-sha256",
        "content_hash": "phase3-step1-chunk-1-sha256",
        "index_version_id": "10000000-0000-0000-0000-000000000003",
        "vector_collection": "phase3_step1_fixture",
        "chunking_version": "generic_window_v1",
        "split_strategy": "generic_window_v1"
    }'::jsonb
)
ON CONFLICT (document_id, index_version_id, chunk_index) DO NOTHING;
