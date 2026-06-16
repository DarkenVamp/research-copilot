import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateSession } from "../hooks/sessions";
import { api } from "../lib/api";

export function NewSessionForm() {
  const navigate = useNavigate();
  const createSession = useCreateSession();
  const [companyName, setCompanyName] = useState("");
  const [website, setWebsite] = useState("");
  const [objective, setObjective] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submitting = createSession.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!companyName.trim() || !objective.trim()) {
      setError("Company name and objective are required.");
      return;
    }
    try {
      const session = await createSession.mutateAsync({
        company_name: companyName.trim(),
        website: website.trim() || undefined,
        objective: objective.trim(),
      });
      // Kick off the workflow immediately, then open the detail view.
      await api.runWorkflow(session.id).catch(() => undefined);
      navigate(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Company name <span className="text-red-500">*</span>
        </label>
        <input
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="e.g. Acme Corp"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Website
        </label>
        <input
          value={website}
          onChange={(e) => setWebsite(e.target.value)}
          placeholder="https://acme.com"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Research objective <span className="text-red-500">*</span>
        </label>
        <textarea
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          rows={3}
          placeholder="e.g. Prepare for a discovery call to sell our CRM to their RevOps team"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      >
        {submitting ? "Creating…" : "Start research"}
      </button>
    </form>
  );
}
