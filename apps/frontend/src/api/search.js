import { api } from "./client";

export function searchDocuments(payload) {
  return api.post("/search", payload);
}

export function searchStructuredObjects(payload) {
  return api.post("/structured-objects/search", payload);
}
