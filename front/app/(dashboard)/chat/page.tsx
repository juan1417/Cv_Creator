"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { useAuth } from "@/app/lib/auth";
import {
  listSessions,
  createChatSession,
  getSessionMessages,
  sendMessage,
  deleteSession,
} from "@/app/lib/api";
import type { ChatSession, ChatMessage } from "@/app/lib/types";

const Markdown = dynamic(() => import("@/app/components/Markdown"), {
  ssr: false,
  loading: () => <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-700" />,
});

export default function ChatPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [chatError, setChatError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const justCreatedSession = useRef(false);

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fetchSessions = useCallback(async () => {
    if (!user) return;
    try {
      const data = await listSessions(user.id);
      setSessions(data.sessions);
    } catch {
      // ignore
    } finally {
      setLoadingSessions(false);
    }
  }, [user]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const fetchMessages = useCallback(
    async (sessionId: string) => {
      if (!user) return;
      setLoadingMessages(true);
      try {
        const data = await getSessionMessages(sessionId, user.id);
        setMessages(data.messages);
      } catch {
        setMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    },
    [user],
  );

  useEffect(() => {
    if (activeSessionId) {
      if (justCreatedSession.current) {
        justCreatedSession.current = false;
        return;
      }
      fetchMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId, fetchMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!user || !input.trim() || sending) return;

    const content = input.trim();
    setInput("");
    setSending(true);

    const optimisticUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content,
      at_Created: new Date().toISOString(),
    };

    try {
      let sessionId = activeSessionId;

      if (!sessionId) {
        const session = await createChatSession({ user_id: user.id });
        sessionId = session.session_id;
        justCreatedSession.current = true;
        setSessions((prev) => [session, ...prev]);
        setActiveSessionId(sessionId);
      }

      setMessages((prev) => [...prev, optimisticUserMsg]);

      const response = await sendMessage(sessionId, {
        user_id: user.id,
        content,
      });

      setChatError("");

      const assistantMsg: ChatMessage = {
        id: `resp-${Date.now()}`,
        role: "assistant",
        content: response.response,
        at_Created: new Date().toISOString(),
      };
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUserMsg.id),
        { ...optimisticUserMsg, id: `user-${Date.now()}` },
        assistantMsg,
      ]);

      if (sessions.length === 0 || !sessions.find(s => s.session_id === sessionId)) {
        const newSession: ChatSession = {
          session_id: sessionId!,
          title: content.slice(0, 60),
          target_job: response.target_job,
          created_at: new Date().toISOString(),
        };
        setSessions((prev) => {
          const exists = prev.find(s => s.session_id === sessionId);
          if (exists) return prev;
          return [newSession, ...prev];
        });
      }
    } catch (err: unknown) {
      setInput(content);
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMsg.id));
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("Completa tu CV") || msg.includes("CV no encontrado")) {
        setChatError("Necesitás completar tu CV primero. Ve a \"Editar CV\" para agregar tu información.");
      } else if (msg.includes("502") || msg.includes("Error del asistente")) {
        setChatError("El asistente está teniendo problemas. Intentá de nuevo en un momento.");
      } else {
        setChatError(`Error: ${msg}`);
      }
    } finally {
      setSending(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!user) return;
    await deleteSession(sessionId, user.id);
    setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
      setMessages([]);
    }
  };

  return (
    <div className="relative flex h-[calc(100vh-4rem)] gap-4">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sessions sidebar */}
      <aside
        className={`
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-72
          flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-xl shadow-2xl
          transition-transform duration-200
          md:static md:translate-x-0 md:z-auto md:h-auto md:rounded-2xl
        `}
      >
        <div className="border-b border-zinc-800 p-4">
          <button
            onClick={async () => {
              if (!user) return;
              const session = await createChatSession({ user_id: user.id });
              setSessions((prev) => [session, ...prev]);
              setActiveSessionId(session.session_id);
              setSidebarOpen(false);
            }}
            className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-indigo-500 hover:shadow-indigo-500/40"
          >
            + Nueva conversación
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingSessions ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-zinc-500">
              Sin conversaciones
            </p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                className={`group flex items-center justify-between border-b border-zinc-800/50 px-4 py-3 transition-colors ${
                  activeSessionId === session.session_id
                    ? "bg-indigo-500/10 border-l-2 border-l-indigo-500"
                    : "hover:bg-zinc-800/40"
                }`}
              >
                <button
                  onClick={() => {
                    setActiveSessionId(session.session_id);
                    setSidebarOpen(false);
                  }}
                  className="min-w-0 flex-1 text-left"
                >
                  <p className="truncate text-sm font-medium text-white">
                    {session.title}
                  </p>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {new Date(session.created_at).toLocaleDateString("es-AR")}
                  </p>
                </button>
                <button
                  onClick={() => handleDeleteSession(session.session_id)}
                  className="ml-2 hidden rounded p-1 text-zinc-500 hover:text-red-400 group-hover:block transition-colors"
                  title="Eliminar"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Chat panel */}
      <div className="flex flex-1 flex-col rounded-2xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-3 border-b border-zinc-800 px-4 py-3 md:hidden">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <span className="text-sm font-medium text-zinc-300">Sesiones</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-4">
          {!activeSessionId && messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <p className="text-lg font-medium text-zinc-400">
                Iniciá una nueva conversación
              </p>
              <p className="mt-1 text-sm text-zinc-500">
                Preguntale al asistente sobre tu CV
              </p>
            </div>
          ) : loadingMessages ? (
            <div className="flex justify-center py-20">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <ChatBubble key={msg.id} message={msg} />
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="rounded-2xl rounded-bl-md bg-zinc-800 px-4 py-3">
                    <div className="flex gap-1">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:-0.3s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500 [animation-delay:-0.15s]" />
                      <span className="h-2 w-2 animate-bounce rounded-full bg-zinc-500" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-zinc-800 p-4">
          {chatError && (
            <div className="mb-3 rounded-xl bg-amber-500/10 border border-amber-500/20 px-4 py-2.5 text-sm text-amber-400">
              {chatError}
            </div>
          )}
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Escribí tu mensaje..."
              rows={1}
              className="max-h-32 min-h-[40px] flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-2.5 text-sm text-white placeholder-zinc-500 transition-all duration-200 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            <button
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-indigo-500 disabled:opacity-50 disabled:shadow-none"
            >
              Enviar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-3 py-2.5 text-sm sm:px-4 sm:py-3 ${
          isUser
            ? "rounded-br-md bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
            : "rounded-bl-md bg-zinc-800 text-zinc-100 border border-zinc-700/50"
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
        ) : (
          <div className="break-words">
            <Markdown content={message.content} />
          </div>
        )}
        <p
          className={`mt-1 text-[10px] ${
            isUser ? "text-indigo-200" : "text-zinc-500"
          }`}
        >
          {new Date(message.at_Created).toLocaleTimeString("es-AR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}
