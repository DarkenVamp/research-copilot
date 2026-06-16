import type {
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

export interface ChatStreamHandlers {
  /** Called with each text delta as the answer is generated. */
  onDelta: (text: string) => void;
  /** Called once if the backend reports an error mid-stream. */
  onError?: (message: string) => void;
}

/**
 * POST a follow-up question and stream the answer back over Server-Sent Events.
 *
 * `EventSource` only does GET, so we read the `text/event-stream` body with
 * fetch + a ReadableStream reader and parse SSE frames by hand. Resolves when
 * the stream ends; rejects (ApiError) on a non-OK response (e.g. 404/409 raised
 * before streaming starts).
 */
async function streamChat(
  id: string,
  message: string,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/api/sessions/${id}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ message }),
    signal,
  });
  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new ApiError(res.status, String(detail));
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      let event = "message";
      const dataLines: string[] = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith(":")) continue; // comment / keepalive
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (dataLines.length === 0) continue;
      const data = dataLines.join("\n");

      if (event === "delta") handlers.onDelta(JSON.parse(data).text);
      else if (event === "error") handlers.onError?.(JSON.parse(data).message);
      else if (event === "done") return;
    }
  }
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
  streamChat,
  streamUrl: (id: string) => `${BASE}/api/sessions/${id}/stream`,
};
