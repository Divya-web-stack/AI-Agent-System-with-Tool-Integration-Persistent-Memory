"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


type Source = { title: string; url: string };
type ChatResponse = {
  session_id: number;
  answer: string;
  verified?: boolean;
  sources: Source[];
  steps?: string[];
};
type SessionItem = { id: number; title: string; created_at: string };

type Msg = { role: "user" | "assistant"; content: string; verified?: boolean; sources?: Source[] };

export default function Home() {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  const [userId, setUserId] = useState("diu");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [useWeb, setUseWeb] = useState(true);
  const [sessions, setSessions] = useState<SessionItem[]>([]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<string[]>([]);
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: "Hi! Ask me anything. Toggle 'Use Web' for verified answers with sources." },
  ]);

  useEffect(() => {
    const stored = localStorage.getItem("lai_session_id");
    if (stored) setSessionId(Number(stored));
  }, []);

  useEffect(() => {
    if (sessionId != null) localStorage.setItem("lai_session_id", String(sessionId));
  }, [sessionId]);

  useEffect(() => {
    fetchSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function send() {
    if (!canSend) return;

    const userText = input.trim();
    setInput("");
    setLoading(true);
    setSteps(useWeb ? ["🔍 Searching the web…"] : ["🧠 Generating answer…"]);

    setMessages((m) => [...m, { role: "user", content: userText }]);

    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          message: userText,
          use_web: useWeb,
        }),
      });

      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || `HTTP ${res.status}`);
      }

      // create a placeholder assistant message we will update live
      let assistantIndex = -1;
      setMessages((m) => {
        assistantIndex = m.length;
        return [...m, { role: "assistant", content: "", verified: false, sources: [] }];
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE events are separated by blank lines
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data: "));
          if (!line) continue;

          const dataStr = line.replace("data: ", "").trim();
          if (dataStr === "[DONE]") continue;

          const payload = JSON.parse(dataStr);

          if (payload.type === "session") {
            setSessionId(payload.session_id);
          }

          if (payload.type === "steps") {
            setSteps(payload.steps || []);
          }

          if (payload.type === "token") {
            setMessages((prev) => {
              const copy = [...prev];
              const msg = copy[assistantIndex];
              copy[assistantIndex] = { ...msg, content: (msg.content || "") + payload.token };
              return copy;
            });
          }

          if (payload.type === "final") {
            setMessages((prev) => {
              const copy = [...prev];
              const msg = copy[assistantIndex];
              copy[assistantIndex] = {
                ...msg,
                verified: payload.verified,
                sources: payload.sources || [],
              };
              return copy;
            });
          }
        }
      }

      await fetchSessions();
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `⚠️ Error: ${e.message || "Something went wrong"}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function resetChat() {
    // 1) Reset session so backend creates a new chat session
    setSessionId(null);

    // 2) Remove stored session id so refresh doesn't bring old conversation back
    localStorage.removeItem("lai_session_id");

    // 3) Clear UI messages (short-term conversation reset)
    setMessages([
      {
        role: "assistant",
        content: "New chat started. How can I help you?",
      },
    ]);

    // 4) Clear pipeline steps UI (optional)
    setSteps([]);
  }

  async function fetchSessions() {
    const res = await fetch(`${API_BASE}/sessions?user_id=${encodeURIComponent(userId)}`);
    const data = await res.json();
    setSessions(data);
  }

  async function deleteSession(id: number) {
  if (!confirm("Delete this chat?")) return;

  try {
    const res = await fetch(`${API_BASE}/sessions/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    // if deleting currently open chat, reset UI
    if (sessionId === id) {
      resetChat();
    }

    await fetchSessions();
  } catch (err) {
    console.error(err);
    alert("Failed to delete session");
  }
}



  async function loadSession(id: number) {
    const res = await fetch(`${API_BASE}/sessions/${id}/messages`);
    const data = await res.json();

    setSessionId(id);
    localStorage.setItem("lai_session_id", String(id));

    const mapped: Msg[] = data
      .filter((m: any) => m.role === "user" || m.role === "assistant")
      .map((m: any) => ({ role: m.role, content: m.content }));

    setMessages(mapped.length ? mapped : [{ role: "assistant", content: "Empty chat." }]);
  }

  return (
    <main className="min-h-screen p-4 md:p-10">
      <div className="mx-auto max-w-6xl grid grid-cols-1 md:grid-cols-[280px_1fr] gap-6">

        {/* Sidebar */}
        <aside className="rounded border p-3 h-[80vh] overflow-auto">
          <div className="flex items-center justify-between mb-3">
            <div className="font-semibold">Chats</div>
            <button className="rounded border px-2 py-1 text-xs" onClick={fetchSessions}>
              Refresh
            </button>
          </div>

          <button className="w-full rounded border px-3 py-2 text-sm mb-3" onClick={resetChat}>
            + New Chat
          </button>

          <div className="space-y-2">
            {sessions.map((s) => (
  <div
    key={s.id}
    className={`w-full text-left rounded-xl border px-3 py-3 text-sm transition ${
  sessionId === s.id
    ? "bg-zinc-900 border-zinc-700"
    : "bg-zinc-950 border-zinc-800 hover:bg-zinc-900"
}`}

  >
    <div className="flex-1 cursor-pointer" onClick={() => loadSession(s.id)}>
      <div className="flex items-center gap-2">
        <span>💬</span>
        <div className="font-medium truncate">{s.title || `Chat ${s.id}`}</div>
      </div>
    <div className="text-xs text-zinc-500">Session #{s.id}</div>
    </div>

    <button
      onClick={(e) => {
        e.stopPropagation();
        deleteSession(s.id);
      }}
      className="rounded border px-2 py-1 text-xs opacity-80 hover:opacity-100"
      title="Delete chat"
    >
      🗑
    </button>
  </div>
))}



            {sessions.length === 0 && (
              <div className="text-sm opacity-70">No chats yet.</div>
            )}
          </div>
        </aside>

        {/* Main Chat Area */}
        <div>
          <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Live AI Assistant</h1>
            <p className="text-sm opacity-70">Smarter Than a Search Bar</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-sm opacity-80">User</label>
              <input
                className="rounded border px-2 py-1 text-sm"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useWeb}
                onChange={(e) => setUseWeb(e.target.checked)}
              />
              Use Web
            </label>

            <button className="rounded border px-3 py-1 text-sm" onClick={resetChat}>
              New Chat
            </button>
          </div>
        </header>

        <section className="mt-6 space-y-4 rounded-2xl border border-zinc-800 bg-black/30 p-5 backdrop-blur">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
<div
  className={`max-w-[85%] rounded-2xl border px-4 py-3 shadow-sm ${
    m.role === "user"
      ? "bg-zinc-900 border-zinc-700 text-zinc-100"
      : "bg-zinc-950 border-zinc-800 text-zinc-100"
  }`}
>

                <div className="flex items-center justify-between gap-3">
                    <div className="text-xs text-zinc-400">
                    {m.role === "user" ? "You" : "Assistant"}
                  </div>

                  {m.role === "assistant" && typeof m.verified !== "undefined" && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full border ${
                          m.verified
                            ? "border-emerald-600/40 bg-emerald-600/10 text-emerald-300"
                            : "border-amber-600/40 bg-amber-600/10 text-amber-300"
                        }`}

                      title={m.verified ? "Verified using multiple sources" : "Not fully verified"}
                    >
                      {m.verified ? "Verified ✅" : "Unverified ⚠️"}
                    </span>
                  )}
                </div>

                <div className="mt-2 prose prose-sm max-w-none prose-pre:bg-zinc-900 prose-pre:text-zinc-100 prose-pre:border prose-pre:border-zinc-700">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.content}
                  </ReactMarkdown>
                </div>

                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div className="mt-3 border-t pt-2">
                    <div className="text-xs font-medium opacity-70 mb-1">Sources</div>
                    <ul className="list-disc pl-5 text-xs space-y-1">
                      {m.sources.map((s, i) => (
                        <li key={i}>
                          <a className="underline" href={s.url} target="_blank" rel="noreferrer">
                            {s.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-lg border p-3 bg-gray-50 text-sm text-gray-900">
                <div className="font-medium mb-1">Live pipeline</div>
                <ul className="list-disc pl-5 space-y-1">
                  {steps.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            </div>
          )}
        </section>

        <section className="mt-4 flex gap-2">
          <input
            className="flex-1 rounded border px-3 py-2"
            placeholder="Type your question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => (e.key === "Enter" ? send() : null)}
          />
          <button
            className="rounded border px-4 py-2 disabled:opacity-50"
            onClick={send}
            disabled={!canSend}
          >
            Send
          </button>
        </section>

        <p className="mt-3 text-xs opacity-60">
          Session ID: {sessionId ?? "none"} • API: {API_BASE}
        </p>
        </div>
      </div>
    </main>
  );
}
