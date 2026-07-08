import { api } from "./client";

export function fetchRuns() {
  return api.get("/runs");
}

export function fetchRun(runId) {
  return api.get(`/runs/${runId}`);
}

export function fetchRetrievalHits(runId) {
  return api.get(`/runs/${runId}/retrieval-hits`);
}
