import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { ChatPanel } from "../components/ChatPanel";
import { ReportView } from "../components/ReportView";
import { StatusBadge } from "../components/StatusBadge";
import { WorkflowProgress } from "../components/WorkflowProgress";
import {
  sessionKeys,
  useResumeWorkflow,
  useRunWorkflow,
  useSession,
} from "../hooks/sessions";

export function SessionDetailPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const { data: session, isLoading, isError, refetch } = useSession(id);
  const runWorkflow = useRunWorkflow(id);
  const resumeWorkflow = useResumeWorkflow(id);
  const [started, setStarted] = useState(false);

  // When a run finishes, refresh this session and the sidebar list (status badge).
  function handleFinished() {
    refetch();
    queryClient.invalidateQueries({ queryKey: sessionKeys.all });
  }

  if (isLoading) {
    return <div className="p-10 text-sm text-slate-400">Loading session…</div>;
  }
  if (isError || !session) {
    return (
      <div className="p-10 text-sm text-red-600">
        Session not found.
      </div>
    );
  }

  const showProgress = session.status !== "created" || started;

  async function handleStart() {
    setStarted(true);
    await runWorkflow.mutateAsync().catch(() => undefined);
  }

  async function handleResume() {
    setStarted(true);
    await resumeWorkflow.mutateAsync().catch(() => undefined);
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <header className="mb-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-2xl font-bold text-slate-900">
            {session.company_name}
          </h1>
          <StatusBadge status={session.status} />
        </div>
        {session.website && (
          <a
            href={session.website}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-blue-600 hover:underline"
          >
            {session.website}
          </a>
        )}
        <p className="mt-2 text-sm text-slate-600">
          <span className="font-medium text-slate-700">Objective: </span>
          {session.objective}
        </p>
      </header>

      {session.status === "created" && !started && (
        <button
          onClick={handleStart}
          disabled={runWorkflow.isPending}
          className="mb-6 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          Start research
        </button>
      )}

      {session.status === "failed" && (
        <div className="mb-6 rounded-lg bg-red-50 p-4">
          <p className="text-sm text-red-700">
            The workflow failed{session.error ? `: ${session.error}` : "."}
          </p>
          <button
            onClick={handleResume}
            disabled={resumeWorkflow.isPending}
            className="mt-2 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
          >
            Resume from last checkpoint
          </button>
        </div>
      )}

      <div className="space-y-6">
        {showProgress && (
          <WorkflowProgress
            sessionId={session.id}
            enabled={showProgress}
            status={session.status}
            onFinished={handleFinished}
          />
        )}

        {session.report && <ReportView report={session.report} />}
        {session.report && <ChatPanel sessionId={session.id} />}
      </div>
    </div>
  );
}
