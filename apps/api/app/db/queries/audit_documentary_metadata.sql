-- Non-destructive documentary metadata audit queries.

SELECT count(*) AS total_chunks
FROM document_chunks;

SELECT count(*) AS chunks_without_source_id
FROM document_chunks
WHERE metadata->>'source_id' IS NULL
   OR metadata->>'source_id' = '';

SELECT count(*) AS chunks_without_document_title
FROM document_chunks
WHERE metadata->>'document_title' IS NULL
   OR metadata->>'document_title' = '';

SELECT count(*) AS chunks_without_source_code
FROM document_chunks
WHERE metadata->>'source_code' IS NULL
   OR metadata->>'source_code' = '';

SELECT count(*) AS chunks_without_page_or_section
FROM document_chunks
WHERE metadata->>'section' IS NULL
  AND metadata->>'page_start' IS NULL
  AND metadata->>'page_end' IS NULL;

SELECT count(*) AS chunks_without_vector_collection
FROM document_chunks
WHERE metadata->>'vector_collection' IS NULL
   OR metadata->>'vector_collection' = '';

SELECT count(*) AS chunks_without_parent_document_id
FROM document_chunks
WHERE metadata->>'parent_document_id' IS NULL
   OR metadata->>'parent_document_id' = '';

SELECT count(*) AS chunks_without_content_hash
FROM document_chunks
WHERE metadata->>'content_hash' IS NULL
   OR metadata->>'content_hash' = '';

SELECT count(*) AS chunks_without_chunking_version
FROM document_chunks
WHERE metadata->>'chunking_version' IS NULL
   OR metadata->>'chunking_version' = '';

SELECT count(*) AS chunks_without_split_strategy
FROM document_chunks
WHERE metadata->>'split_strategy' IS NULL
   OR metadata->>'split_strategy' = '';

SELECT count(*) AS chunks_without_role_documentaire
FROM document_chunks
WHERE metadata->>'role_documentaire' IS NULL
   OR metadata->>'role_documentaire' = '';

SELECT count(*) AS chunks_without_statut_metadonnees
FROM document_chunks
WHERE metadata->>'statut_metadonnees' IS NULL
   OR metadata->>'statut_metadonnees' = '';

SELECT count(*) AS invalid_index_version_chunking_config
FROM index_versions
WHERE chunking_version IS NULL
   OR chunking_version = ''
   OR split_strategy IS NULL
   OR split_strategy = ''
   OR chunk_size <= 0
   OR chunk_overlap < 0
   OR chunk_overlap >= chunk_size
   OR min_chunk_size <= 0
   OR min_chunk_size > chunk_size
   OR max_chunk_size < chunk_size;

SELECT
    document_chunks.id AS chunk_id,
    document_chunks.chunk_index,
    documents.id AS document_id,
    documents.title AS document_title,
    sources.id AS source_id,
    sources.code AS source_code,
    document_chunks.page_start,
    document_chunks.page_end,
    index_versions.chunking_version,
    index_versions.split_strategy,
    document_chunks.metadata
FROM document_chunks
JOIN documents ON documents.id = document_chunks.document_id
JOIN sources ON sources.id = documents.source_id
JOIN index_versions ON index_versions.id = document_chunks.index_version_id
ORDER BY document_chunks.created_at DESC
LIMIT 20;
