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

SELECT count(*) AS chunks_without_source_name
FROM document_chunks
WHERE metadata->>'source_name' IS NULL
   OR metadata->>'source_name' = '';

SELECT count(*) AS chunks_without_page_or_section
FROM document_chunks
WHERE metadata->>'section' IS NULL
  AND metadata->>'page_start' IS NULL
  AND metadata->>'page_end' IS NULL;

SELECT count(*) AS chunks_without_vector_collection
FROM document_chunks
WHERE metadata->>'vector_collection' IS NULL
   OR metadata->>'vector_collection' = '';

SELECT
    document_chunks.id AS chunk_id,
    document_chunks.chunk_index,
    documents.id AS document_id,
    documents.title AS document_title,
    sources.id AS source_id,
    sources.name AS source_name,
    document_chunks.page_start,
    document_chunks.page_end,
    document_chunks.metadata
FROM document_chunks
JOIN documents ON documents.id = document_chunks.document_id
JOIN sources ON sources.id = documents.source_id
ORDER BY document_chunks.created_at DESC
LIMIT 20;
