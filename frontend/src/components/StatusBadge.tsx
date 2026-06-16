import type { SessionStatus } from "../lib/types";

const STYLES: Record<SessionStatus, string> = {
  created: "bg-slate-100 text-slate-600",
  running: "bg-blue-100 text-blue-700 animate-pulse",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

const LABELS: Record<SessionStatus, string> = {
  created: "Not started",
  running: "Researching…",
  completed: "Completed",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: SessionStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
