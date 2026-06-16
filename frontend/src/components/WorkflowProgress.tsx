import { NODES } from "../lib/nodes";
import { useEventStream, type NodeState } from "../lib/useEventStream";
import type { SessionStatus } from "../lib/types";

type Display = "completed" | "running" | "pending" | "failed";

function dataFacts(data: Record<string, unknown> | null): string[] {
  if (!data) return [];
  const facts: string[] = [];
  for (const [k, v] of Object.entries(data)) {
    if (Array.isArray(v)) {
      if (v.length && typeof v[0] !== "object") {
        facts.push(`${k.replace(/_/g, " ")}: ${v.length}`);
      }
    } else if (typeof v === "number" || typeof v === "boolean") {
      facts.push(`${k.replace(/_/g, " ")}: ${v}`);
    }
  }
  return facts;
}

const DOT: Record<Display, string> = {
  completed: "bg-emerald-500",
  running: "bg-blue-500 animate-pulse",
  pending: "bg-slate-300",
  failed: "bg-red-500",
};

export function WorkflowProgress({
  sessionId,
  enabled,
  status,
  onFinished,
  onStarted,
}: {
  sessionId: string;
  enabled: boolean;
  status: SessionStatus;
  onFinished: () => void;
  onStarted?: () => void;
}) {
  const { byNode, finished, error } = useEventStream(
    sessionId,
    enabled,
    onFinished,
    onStarted,
  );

  // The first not-yet-completed node is the one currently running.
  const firstPending = NODES.findIndex((n) => !byNode[n.key]);
  const running =
    enabled && !finished && status !== "completed" && status !== "failed";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-700">
          Workflow progress
        </h2>
        {running && <span className="text-xs text-blue-600">running…</span>}
      </div>

      {error && (
        <div className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <ol className="space-y-4">
        {NODES.map((node, idx) => {
          const state: NodeState | undefined = byNode[node.key];
          let display: Display = "pending";
          if (state) display = state.status;
          else if (running && idx === firstPending) display = "running";

          return (
            <li key={node.key} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span className={`mt-1 h-3 w-3 rounded-full ${DOT[display]}`} />
                {idx < NODES.length - 1 && (
                  <span className="mt-1 h-full w-px flex-1 bg-slate-200" />
                )}
              </div>
              <div className="flex-1 pb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {node.label}
                  </span>
                  {state && state.runs > 1 && (
                    <span className="rounded bg-amber-100 px-1.5 text-xs text-amber-700">
                      ×{state.runs}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500">
                  {state?.message ?? node.description}
                </p>
                {state && dataFacts(state.data).length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {dataFacts(state.data).map((f) => (
                      <span
                        key={f}
                        className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
