import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { WorkflowEvent } from "./types";

export interface NodeState {
  status: "running" | "completed" | "failed";
  message: string | null;
  data: Record<string, unknown> | null;
  runs: number;
}

export interface StreamState {
  events: WorkflowEvent[];
  byNode: Record<string, NodeState>;
  finished: boolean;
  error: string | null;
}

/**
 * Subscribe to the backend SSE stream for a session. The stream replays any
 * already-persisted events (catch-up) and then delivers live ones, so this hook
 * works whether the workflow is still running or already finished.
 */
export function useEventStream(
  sessionId: string,
  enabled: boolean,
  onFinished?: () => void,
): StreamState {
  const [state, setState] = useState<StreamState>({
    events: [],
    byNode: {},
    finished: false,
    error: null,
  });
  const finishedRef = useRef(false);

  useEffect(() => {
    if (!enabled) return;
    finishedRef.current = false;
    setState({ events: [], byNode: {}, finished: false, error: null });

    const es = new EventSource(api.streamUrl(sessionId));

    const handleNode = (raw: MessageEvent) => {
      const msg = JSON.parse(raw.data) as WorkflowEvent;
      setState((prev) => {
        const prevNode = prev.byNode[msg.node];
        return {
          ...prev,
          events: [...prev.events, msg],
          byNode: {
            ...prev.byNode,
            [msg.node]: {
              status: msg.status as NodeState["status"],
              message: msg.message,
              data: msg.data,
              runs: (prevNode?.runs ?? 0) + 1,
            },
          },
        };
      });
    };

    const finish = (error: string | null) => {
      if (finishedRef.current) return;
      finishedRef.current = true;
      setState((prev) => ({ ...prev, finished: true, error }));
      es.close();
      onFinished?.();
    };

    es.addEventListener("node", handleNode);
    es.addEventListener("done", () => finish(null));
    es.addEventListener("error", (e) => {
      const m = e as MessageEvent;
      let detail: string | null = null;
      try {
        detail = m.data ? (JSON.parse(m.data).message ?? null) : null;
      } catch {
        detail = null;
      }
      // A network drop also lands here; only treat explicit error events or a
      // closed connection as terminal.
      if (detail || es.readyState === EventSource.CLOSED) finish(detail);
    });

    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, enabled]);

  return state;
}
