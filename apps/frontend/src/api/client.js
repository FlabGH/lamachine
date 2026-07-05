import { API_BASE_URL } from "../config";
import { recordApiCall } from "./debugLog";

function normalizeUrl(path) {
  if (path.startsWith("http")) return path;
  if (path.startsWith("/health")) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function request(path, options = {}) {
  const url = normalizeUrl(path);
  const started = performance.now();
  const requestPayload = options.body;
  let status = 0;
  let responsePayload = null;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...(options.headers || {}),
      },
    });
    status = response.status;
    const contentType = response.headers.get("content-type") || "";
    responsePayload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
    if (!response.ok) {
      const error = new Error(`API ${response.status}`);
      error.status = response.status;
      error.payload = responsePayload;
      throw error;
    }
    return responsePayload;
  } finally {
    recordApiCall({
      method: options.method || "GET",
      url,
      status,
      durationMs: Math.round(performance.now() - started),
      request: requestPayload instanceof FormData ? "[FormData]" : requestPayload,
      response: responsePayload,
    });
  }
}

export const api = {
  get(path) {
    return request(path);
  },
  post(path, payload) {
    return request(path, {
      method: "POST",
      body: JSON.stringify(payload || {}),
    });
  },
  postForm(path, formData) {
    return request(path, {
      method: "POST",
      body: formData,
    });
  },
};
