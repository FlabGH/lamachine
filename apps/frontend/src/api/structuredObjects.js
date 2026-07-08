import { api } from "./client";

export function fetchStructuredObjects() {
  return api.get("/structured-objects");
}

export function fetchDocumentStructuredObjects(documentId) {
  return api.get(`/documents/${documentId}/structured-objects`);
}

export function fetchStructuredObject(objectId) {
  return api.get(`/structured-objects/${objectId}`);
}
