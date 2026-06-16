import { NavLink } from "react-router-dom";
import { useSessions } from "../hooks/sessions";
import { StatusBadge } from "./StatusBadge";

export function SessionList() {
  const { data: sessions, isLoading, isError } = useSessions();

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-4">
        <h1 className="text-lg font-semibold text-slate-800">Research Copilot</h1>
      </div>
      <NavLink
        to="/"
        className="mx-4 mb-3 rounded-lg bg-slate-900 px-3 py-2 text-center text-sm font-medium text-white hover:bg-slate-700"
      >
        + New research
      </NavLink>

      <div className="px-4 pb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
        History
      </div>
      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {isLoading && <p className="px-2 text-sm text-slate-400">Loading…</p>}
        {isError && (
          <p className="px-2 text-sm text-red-500">Could not load sessions.</p>
        )}
        {sessions?.length === 0 && (
          <p className="px-2 text-sm text-slate-400">No sessions yet.</p>
        )}
        <ul className="space-y-1">
          {sessions?.map((s) => (
            <li key={s.id}>
              <NavLink
                to={`/sessions/${s.id}`}
                className={({ isActive }) =>
                  `block rounded-lg px-3 py-2 text-sm transition ${
                    isActive
                      ? "bg-slate-200 text-slate-900"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                <div className="truncate font-medium">{s.company_name}</div>
                <div className="mt-1 flex items-center justify-between gap-2">
                  <span className="truncate text-xs text-slate-400">
                    {s.objective}
                  </span>
                  <StatusBadge status={s.status} />
                </div>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
