const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ModelConfigPayload = {
  config_type: "text" | "image";
  provider_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  image_size?: string;
  remark?: string;
  enabled?: boolean;
};

export type ProjectPayload = {
  title?: string;
  idea: string;
  target_platform?: string;
  genre?: string;
  episode_count: number;
  episode_duration: number;
  target_audience?: string;
  style?: string;
  remark?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createModelConfig(payload: ModelConfigPayload) {
  return request("/api/model-configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function testModelConfig(configId: string) {
  return request(`/api/model-configs/${configId}/test`, {
    method: "POST"
  });
}

export function createProject(payload: ProjectPayload) {
  return request("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

