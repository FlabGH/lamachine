SELECT count(*) AS documents_total
FROM documents;

SELECT count(*) AS chunks_total
FROM document_chunks;

SELECT count(*) AS documents_without_source_code
FROM documents
WHERE metadata->>'source_code' IS NULL
   OR metadata->>'source_code' = '';

SELECT count(*) AS chunks_without_source_code
FROM document_chunks
WHERE metadata->>'source_code' IS NULL
   OR metadata->>'source_code' = '';

SELECT count(*) AS chunks_without_content_hash
FROM document_chunks
WHERE metadata->>'content_hash' IS NULL
   OR metadata->>'content_hash' = '';

SELECT count(*) AS chunks_without_title
FROM document_chunks
WHERE metadata->>'title' IS NULL
   OR metadata->>'title' = '';

SELECT count(*) AS chunks_without_chunking_strategy
FROM document_chunks
WHERE metadata->>'chunking_strategy' IS NULL
   OR metadata->>'chunking_strategy' = '';

SELECT metadata->>'content_hash' AS content_hash, count(*) AS count
FROM document_chunks
GROUP BY metadata->>'content_hash'
HAVING count(*) > 1
ORDER BY count DESC, content_hash;
