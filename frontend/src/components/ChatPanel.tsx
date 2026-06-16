import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "../lib/api";
import { sessionKeys, useMessages } from "../hooks/sessions";

export function ChatPanel({ sessionId }: { sessionId: string }) {
  const qc = useQueryClient();
  const { data: messages } = useMessages(sessionId, true);
  const [input, setInput] = useState("");
  // While a question is in flight we render optimistic bubbles: the user's
  // question and the assistant's answer as it streams in token-by-token.
  const [pendingUser, setPendingUser] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const streaming = pendingUser !== null;

  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Abort an in-flight stream if the component unmounts mid-answer.
  useEffect(() => () => abortRef.current?.abort(), []);

  // Keep the latest message / token in view.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, draft, pendingUser]);

  async function handleSend(e: React.SyntheticEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;

    setInput("");
    setError(null);
    setDraft("");
    setPendingUser(text);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await api.streamChat(
        sessionId,
        text,
        {
          onDelta: (t) => setDraft((d) => d + t),
          onError: (m) => setError(m),
        },
        controller.signal,
      );
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof ApiError ? err.message : "Something went wrong.");
      }
    } finally {
      // Refetch the canonical persisted turns, then drop the optimistic ones —
      // awaiting the refetch first avoids a flash of duplicated bubbles.
      await qc.invalidateQueries({ queryKey: sessionKeys.messages(sessionId) });
      setPendingUser(null);
      setDraft("");
      abortRef.current = null;
    }
  }

  return (
    <div className="flex flex-col rounded-xl border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-5 py-3">
        <h2 className="text-sm font-semibold text-slate-700">
          Follow-up chat
        </h2>
        <p className="text-xs text-slate-400">
          Ask questions grounded in this report.
        </p>
      </div>

      <div ref={scrollRef} className="max-h-96 flex-1 space-y-3 overflow-y-auto p-5">
        {(!messages || messages.length === 0) && !streaming && (
          <p className="text-sm text-slate-400">
            No messages yet — try “What should I lead with in the meeting?”
          </p>
        )}
        {messages?.map((m) => (
          <Bubble key={m.id} role={m.role} content={m.content} />
        ))}

        {/* Optimistic, live-streaming turn (cleared once the refetch lands). */}
        {pendingUser !== null && <Bubble role="user" content={pendingUser} />}
        {streaming && (
          <Bubble
            role="assistant"
            content={draft}
            placeholder={draft.length === 0}
            cursor={draft.length > 0}
          />
        )}

        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
            {error}
          </p>
        )}
      </div>

      <form onSubmit={handleSend} className="flex gap-2 border-t border-slate-100 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a follow-up question…"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-500"
        />
        <button
          type="submit"
          disabled={streaming || !input.trim()}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function Bubble({
  role,
  content,
  placeholder = false,
  cursor = false,
}: {
  role: string;
  content: string;
  placeholder?: boolean;
  cursor?: boolean;
}) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm ${
          role === "user"
            ? "bg-slate-900 text-white"
            : "bg-slate-100 text-slate-700"
        }`}
      >
        {placeholder ? (
          <span className="text-slate-400">thinking…</span>
        ) : (
          <>
            {content}
            {cursor && (
              <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-slate-400 align-middle" />
            )}
          </>
        )}
      </div>
    </div>
  );
}
