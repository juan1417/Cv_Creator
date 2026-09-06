"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/app/lib/auth";
import { getFullCV, listSessions } from "@/app/lib/api";
import type { FullCV, ChatSessionListResponse } from "@/app/lib/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [cv, setCv] = useState<FullCV | null>(null);
  const [sessions, setSessions] = useState<ChatSessionListResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      try {
        const [cvData, sessionsData] = await Promise.allSettled([
          getFullCV(user.id),
          listSessions(user.id),
        ]);

        if (cvData.status === "fulfilled") setCv(cvData.value);
        if (sessionsData.status === "fulfilled") setSessions(sessionsData.value);
      } catch {
        // silently fail - dashboard still renders
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  if (!user) return null;

  const hasCv = !!cv;
  const cvCompleteness = hasCv
    ? Math.round(
        ((cv!.cv.name ? 1 : 0) +
          (cv!.cv.email ? 1 : 0) +
          (cv!.cv.phone ? 1 : 0) +
          (cv!.cv.about ? 1 : 0) +
          (cv!.experiences.length > 0 ? 1 : 0) +
          (cv!.skills.length > 0 ? 1 : 0) +
          (cv!.education.length > 0 ? 1 : 0)) /
          7 *
          100
      )
    : 0;

  const recentSessions = sessions?.sessions?.slice(0, 5) ?? [];

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-zinc-900">
          Bienvenido, {user.username}
        </h2>
        <p className="text-zinc-500 mt-1">
          Gestiona tu CV y potencia tu busqueda laboral
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h3 className="font-semibold text-zinc-900">Estado del CV</h3>
          </div>
          {loading ? (
            <p className="text-sm text-zinc-400">Cargando...</p>
          ) : hasCv ? (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      cvCompleteness >= 70 ? "bg-green-500" : cvCompleteness >= 40 ? "bg-yellow-500" : "bg-red-500"
                    }`}
                    style={{ width: `${cvCompleteness}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-zinc-700">{cvCompleteness}%</span>
              </div>
              <p className="text-xs text-zinc-500">
                {cvCompleteness === 100
                  ? "Tu CV esta completo"
                  : "Agrega mas secciones para completar tu CV"}
              </p>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">No tienes un CV creado aun</p>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
          <h3 className="font-semibold text-zinc-900 mb-4">Acciones rapidas</h3>
          <div className="space-y-2">
            <Link
              href="/cv/edit"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              Editar CV
            </Link>
            <Link
              href="/chat"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              Hablar con asistente
            </Link>
            <Link
              href="/cv/analysis"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              Analizar CV
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
          <h3 className="font-semibold text-zinc-900 mb-4">Sesiones recientes</h3>
          {loading ? (
            <p className="text-sm text-zinc-400">Cargando...</p>
          ) : recentSessions.length > 0 ? (
            <ul className="space-y-2">
              {recentSessions.map((s) => (
                <li key={s.session_id}>
                  <Link
                    href={`/chat?session=${s.session_id}`}
                    className="text-sm text-zinc-700 hover:text-blue-600 transition-colors block truncate"
                  >
                    {s.title || "Sesion sin titulo"}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-zinc-500">No hay sesiones recientes</p>
          )}
        </div>
      </div>
    </div>
  );
}
