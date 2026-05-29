const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ModelConfigPayload = {
  config_type: "text" | "image";
  provider_mode?: "preset" | "custom";
  provider_preset?: string;
  provider_name: string;
  api_base_url: string;
  api_key: string;
  model_name: string;
  image_size?: string;
  endpoint_path?: string;
  supports_reference_image?: boolean;
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

export type ProjectSummary = ProjectPayload & {
  id: string;
  title: string;
  total_duration: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CharacterCardStatus = "draft" | "active" | "archived";
export type CharacterGender = "男" | "女";

export type CharacterCardPayload = {
  name: string;
  gender: CharacterGender;
  role_type: string;
  identity: string;
  background?: string;
  personality?: string;
  goal: string;
  motivation?: string;
  secret?: string;
  conflict_points?: string;
  relationship_notes?: string;
  speech_style?: string;
  catchphrases?: string;
  emotional_arc?: string;
  story_function?: string;
  visual_description?: string;
  image_keywords?: string;
  reference_image_url?: string;
  reference_local_path?: string;
  turnaround_prompt?: string;
  status: CharacterCardStatus;
};

export type CharacterCard = CharacterCardPayload & {
  id: string;
  version: number;
  turnaround_image_url?: string;
  turnaround_local_path?: string;
  turnaround_generation_prompt?: string;
  turnaround_status: "none" | "generated" | "confirmed" | "failed";
  turnaround_version: number;
  turnaround_confirmed_at?: string;
  created_at: string;
  updated_at: string;
};

export type CharacterImageAsset = {
  character_card_id: string;
  image_url: string;
  local_path: string;
  updated_at: string;
};

export type CharacterTurnaround = {
  character_card_id: string;
  image_url?: string;
  local_path?: string;
  generation_prompt?: string;
  status: "none" | "generated" | "confirmed" | "failed";
  version: number;
  confirmed_at?: string;
  updated_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      }
    });
  } catch (err) {
    // 浏览器在后端未启动、端口不可达或 CORS 被拦截时通常只给出 Load failed/Failed to fetch。
    throw new Error(normalizeNetworkError(err));
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function normalizeNetworkError(err: unknown) {
  const rawMessage = err instanceof Error ? err.message : "";
  if (rawMessage === "Load failed" || rawMessage === "Failed to fetch" || rawMessage.includes("NetworkError")) {
    return `无法连接后端服务，请确认 API 服务已启动并可访问：${API_BASE_URL}`;
  }
  return rawMessage || "请求后端服务失败，请稍后重试。";
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

export function listProjects() {
  return request<ProjectSummary[]>("/api/projects");
}

export function listCharacterCards(filters: { search?: string; gender?: CharacterGender; role_type?: string; status?: string } = {}) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.gender) params.set("gender", filters.gender);
  if (filters.role_type) params.set("role_type", filters.role_type);
  if (filters.status) params.set("status", filters.status);
  const query = params.toString();
  return request<CharacterCard[]>(`/api/character-cards${query ? `?${query}` : ""}`);
}

export function createCharacterCard(payload: CharacterCardPayload) {
  return request<CharacterCard>("/api/character-cards", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}`);
}

export function updateCharacterCard(cardId: string, payload: CharacterCardPayload) {
  return request<CharacterCard>(`/api/character-cards/${cardId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function archiveCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}/archive`, {
    method: "POST"
  });
}

export function activateCharacterCard(cardId: string) {
  return request<CharacterCard>(`/api/character-cards/${cardId}/activate`, {
    method: "POST"
  });
}

export function loadCharacterCardToProject(projectId: string, sourceCharacterCardId: string) {
  return request(`/api/projects/${projectId}/character-snapshots`, {
    method: "POST",
    body: JSON.stringify({
      source_character_card_id: sourceCharacterCardId,
      load_mode: "new"
    })
  });
}

export function uploadCharacterReferenceImage(
  cardId: string,
  payload: { filename: string; content_type: string; data_url: string }
) {
  return request<CharacterImageAsset>(`/api/character-cards/${cardId}/reference-images`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateCharacterTurnaround(cardId: string, prompt?: string) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images`, {
    method: "POST",
    body: JSON.stringify({ prompt: prompt || undefined })
  });
}

export function confirmCharacterTurnaround(cardId: string) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images/confirm`, {
    method: "POST"
  });
}

export function confirmCharacterTurnaroundByVersion(cardId: string, version: number) {
  return request<CharacterTurnaround>(`/api/character-cards/${cardId}/turnaround-images/${version}/confirm`, {
    method: "POST"
  });
}

export function resolveAssetUrl(url?: string) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  return `${API_BASE_URL}${url}`;
}
