import type {
  HealthResponse,
  LearningUIState,
  SessionCreateRequest,
  SessionCreateResponse,
} from "../types/game";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...init?.headers },
      ...init,
    });
  } catch {
    throw new Error(
      "無法連線 API。請確認已在 port 8000 啟動：uv run uvicorn api_main:app --reload --port 8000",
    );
  }
  if (!resp.ok) {
    let detail = await resp.text();
    try {
      const json = JSON.parse(detail) as Record<string, unknown>;
      if (typeof json.detail === "string") detail = json.detail;
    } catch {
      // keep raw
    }
    throw new Error(detail || `HTTP ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function createSession(
  body: SessionCreateRequest,
): Promise<SessionCreateResponse> {
  return request<SessionCreateResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getSession(sessionId: string): Promise<LearningUIState> {
  return request<LearningUIState>(`/sessions/${sessionId}`);
}

export function startHand(sessionId: string): Promise<LearningUIState> {
  return request<LearningUIState>(`/sessions/${sessionId}/hands`, {
    method: "POST",
  });
}

export function analyze(sessionId: string): Promise<LearningUIState> {
  return request<LearningUIState>(`/sessions/${sessionId}/analyze`, {
    method: "POST",
  });
}

export function nextStep(sessionId: string): Promise<LearningUIState> {
  return request<LearningUIState>(`/sessions/${sessionId}/next`, {
    method: "POST",
  });
}

export function submitAction(
  sessionId: string,
  index: number,
): Promise<LearningUIState> {
  return request<LearningUIState>(`/sessions/${sessionId}/actions`, {
    method: "POST",
    body: JSON.stringify({ index }),
  });
}
