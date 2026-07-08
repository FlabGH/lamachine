import { api } from "./client";

function cleanFilters(filters = {}) {
  return Object.fromEntries(
    Object.entries(filters).filter(([, value]) => {
      if (value === null || value === undefined || value === "") return false;
      if (Array.isArray(value)) return value.length > 0;
      if (typeof value === "object") return Object.keys(value).length > 0;
      return true;
    }),
  );
}

function cleanPayload(payload) {
  const next = { ...(payload || {}) };
  if ("filters" in next) {
    const filters = cleanFilters(next.filters);
    if (Object.keys(filters).length) {
      next.filters = filters;
    } else {
      delete next.filters;
    }
  }
  for (const [key, value] of Object.entries(next)) {
    if (value === null || value === undefined || value === "") {
      delete next[key];
    }
  }
  return next;
}

export function searchDocuments(payload) {
  return api.post("/search", cleanPayload(payload));
}

export function searchStructuredObjects(payload) {
  return api.post("/structured-objects/search", cleanPayload(payload));
}
