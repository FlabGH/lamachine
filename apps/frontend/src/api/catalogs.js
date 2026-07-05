import { api } from "./client";

export function fetchSystemSummary() {
  return api.get("/system/summary");
}

export function fetchMetadataSchema() {
  return api.get("/metadata/schema");
}

export function fetchChunkingStrategies() {
  return api.get("/chunking/strategies");
}

export function fetchLoaders() {
  return api.get("/loaders");
}

export function fetchEnrichers() {
  return api.get("/enrichers");
}

export function fetchRetrievalPresets() {
  return api.get("/retrieval/presets");
}

export function fetchSearchCapabilities() {
  return api.get("/search/capabilities");
}

export function fetchProjectConfig() {
  return api.get("/project/config");
}
