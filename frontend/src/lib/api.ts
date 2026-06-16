import type {
  ChatResponse,
  ChatMessage,
  SessionDetail,
  SessionRead,
  WorkflowEvent,
} from "./types";

// Empty base in dev → relative URLs hit the Vite proxy. In prod the build is
// configured with VITE_API_BASE_URL pointing at the backend.
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(res.status, String(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listSessions: () => request<SessionRead[]>("/sessions"),
  getSession: (id: string) => request<SessionDetail>(`/sessions/${id}`),
  createSession: (body: {
    company_name: string;
    website?: string;
    objective: string;
  }) =>
    request<SessionRead>("/sessions", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  runWorkflow: (id: string) =>
    request<{ status: string }>(`/sessions/${id}/run`, { method: "POST" }),
  resumeWorkflow: (id: string) =>
    request<{ status: string }>(`/sessions/${id}/resume`, { method: "POST" }),
  getEvents: (id: string) => request<WorkflowEvent[]>(`/sessions/${id}/events`),
  getMessages: (id: string) =>
    request<ChatMessage[]>(`/sessions/${id}/messages`),
  sendChat: (id: string, message: string) =>
    request<ChatResponse>(`/sessions/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  streamUrl: (id: string) => `${BASE}/api/sessions/${id}/stream`,
};
