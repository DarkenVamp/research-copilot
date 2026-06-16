import { NewSessionForm } from "../components/NewSessionForm";

export function HomePage() {
  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-bold text-slate-900">
        Prepare for your next meeting
      </h1>
      <p className="mt-2 text-sm text-slate-500">
        Give the copilot a company and your objective. It runs a multi-step
        research workflow — plan, research, analyze, quality-check, and report —
        then lets you chat with the briefing.
      </p>

      <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <NewSessionForm />
      </div>
    </div>
  );
}
