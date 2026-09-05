/** API client — talks to FastAPI backend */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    let detail: unknown = text;
    try { detail = JSON.parse(text); } catch { /* keep text */ }
    throw new Error(`${res.status} ${res.statusText}: ${JSON.stringify(detail)}`);
  }
  // 204 no content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function healthCheck() {
  return request<{ status: string; version: string; environment: string; service: string }>("/health");
}

export async function uploadDataset(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t);
  }
  return res.json();
}

export async function getDataset(datasetId: string) {
  return request(`/datasets/${datasetId}`);
}

export async function getProfile(datasetId: string) {
  return request(`/datasets/${datasetId}/profile`);
}

export async function descriptive(datasetId: string, columns?: string[]) {
  return request("/analyses/descriptive", {
    method: "POST",
    body: JSON.stringify({ dataset_id: datasetId, columns }),
  });
}

export async function runTest(payload: {
  dataset_id: string;
  test_type: string;
  x_col?: string;
  y_col?: string;
  numeric_col?: string;
  group_col?: string;
  col1?: string;
  col2?: string;
  alpha?: number;
}) {
  return request("/analyses/test", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export const Api = {
  healthCheck,
  uploadDataset,
  getDataset,
  getProfile,
  descriptive,
  runTest,
  baseUrl: API_BASE,
};
