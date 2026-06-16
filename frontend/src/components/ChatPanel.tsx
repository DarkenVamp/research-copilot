import { useState } from "react";
import { useMessages, useSendChat } from "../hooks/sessions";

export function ChatPanel({ sessionId }: { sessionId: string }) {
  const { data: messages } = useMessages(sessionId, true);
  const sendChat = useSendChat(sessionId);
  const [input, setInput] = useState("");

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sendChat.isPending) return;
    setInput("");
    await sendChat.mutateAsync(text).catch(() => undefined);
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

      <div className="max-h-96 flex-1 space-y-3 overflow-y-auto p-5">
        {(!messages || messages.length === 0) && (
          <p className="text-sm text-slate-400">
            No messages yet — try “What should I lead with in the meeting?”
          </p>
        )}
        {messages?.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm ${
                m.role === "user"
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-700"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sendChat.isPending && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-slate-100 px-3.5 py-2 text-sm text-slate-400">
              thinking…
            </div>
          </div>
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
          disabled={sendChat.isPending || !input.trim()}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
