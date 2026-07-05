export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export const HEALTH_ENDPOINTS = {
  api: "/health",
  db: "/health/db",
  qdrant: "/health/qdrant",
};
