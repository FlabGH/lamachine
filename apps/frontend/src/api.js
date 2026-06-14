const API_BASE = "/api";

async function parseResponse(response) {
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const detail = payload?.detail ?? payload?.error ?? payload ?? response.statusText;
    const message =
      typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
    throw new Error(`${response.status} ${message}`);
  }

  return payload;
}

export async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  return parseResponse(response);
}

export async function apiPostJson(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  return parseResponse(response);
}

export async function apiPostForm(path, formData) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}
