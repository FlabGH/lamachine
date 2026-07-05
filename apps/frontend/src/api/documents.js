import { api } from "./client";

export function fetchSources() {
  return api.get("/sources");
}

export function fetchDocuments() {
  return api.get("/documents");
}

export function fetchDocument(documentId) {
  return api.get(`/documents/${documentId}`);
}

export function fetchDocumentChunks(documentId) {
  return api.get(`/documents/${documentId}/chunks?include_content=true`);
}

export function fetchChunk(chunkId) {
  return api.get(`/chunks/${chunkId}`);
}

export function fetchExtraction(documentId) {
  return api.get(`/documents/${documentId}/extraction`);
}

export function previewChunking(documentId, payload) {
  return api.post(`/documents/${documentId}/chunking/preview`, payload);
}

export function ingestPdf({ file, sourceCode, metadata, origin, author }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source_code", sourceCode);
  if (origin) formData.append("origin", origin);
  if (author) formData.append("author", author);
  if (metadata && Object.keys(metadata).length) {
    formData.append("metadata_json", JSON.stringify(metadata));
  }
  return api.postForm("/documents/pdf", formData);
}

export async function ingestText({ file, sourceCode, metadata, origin, author, title }) {
  const formData = new FormData();
  formData.append("title", title || file.name);
  formData.append("text", await file.text());
  formData.append("source_code", sourceCode);
  if (origin) formData.append("origin", origin);
  if (author) formData.append("author", author);
  if (metadata && Object.keys(metadata).length) {
    formData.append("metadata_json", JSON.stringify(metadata));
  }
  return api.postForm("/documents/text", formData);
}

export function indexDocument(payload) {
  return api.post("/index", payload);
}
