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
  const totalSessions = sessions?.sessions?.length ?? 0;

  const stats = hasCv
    ? [
        { label: "Experiencias", value: cv!.experiences.length, icon: BriefcaseIcon, color: "text-blue-400", bg: "bg-blue-500/10" },
        { label: "Skills", value: cv!.skills.length, icon: WrenchIcon, color: "text-emerald-400", bg: "bg-emerald-500/10" },
        { label: "Formación", value: cv!.education.length, icon: GraduationIcon, color: "text-amber-400", bg: "bg-amber-500/10" },
        { label: "Idiomas", value: cv!.languages.length, icon: GlobeIcon, color: "text-purple-400", bg: "bg-purple-500/10" },
        { label: "Sesiones IA", value: totalSessions, icon: ChatIcon2, color: "text-rose-400", bg: "bg-rose-500/10" },
      ]
    : [];

  const cvSections = hasCv
    ? [
        { name: "Datos personales", filled: !!(cv!.cv.name && cv!.cv.email), href: "/cv/edit" },
        { name: "Experiencia", filled: cv!.experiences.length > 0, href: "/cv/edit" },
        { name: "Skills técnicas", filled: cv!.skills.some((s) => s.type !== "soft"), href: "/cv/edit" },
        { name: "Skills blandas", filled: cv!.skills.some((s) => s.type === "soft"), href: "/cv/edit" },
        { name: "Formación", filled: cv!.education.length > 0, href: "/cv/edit" },
        { name: "Logros", filled: cv!.achievements.length > 0, href: "/cv/edit" },
        { name: "Programas", filled: cv!.programs.length > 0, href: "/cv/edit" },
        { name: "Idiomas", filled: cv!.languages.length > 0, href: "/cv/edit" },
      ]
    : [];

  const filledSections = cvSections.filter((s) => s.filled).length;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Bienvenido, {user.username}
        </h2>
        <p className="text-zinc-400 mt-1">
          Gestiona tu CV y potencíá tu búsqueda laboral
        </p>
      </div>

      {/* Top cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* CV Status */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h3 className="font-semibold text-white">Estado del CV</h3>
          </div>
          {loading ? (
            <div className="space-y-2">
              <div className="h-2 bg-zinc-800 rounded-full animate-pulse" />
              <div className="h-3 w-2/3 bg-zinc-800 rounded animate-pulse" />
            </div>
          ) : hasCv ? (
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="flex-1 h-2.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      cvCompleteness >= 70 ? "bg-emerald-500" : cvCompleteness >= 40 ? "bg-amber-500" : "bg-red-500"
                    }`}
                    style={{ width: `${cvCompleteness}%` }}
                  />
                </div>
                <span className="text-sm font-bold text-white">{cvCompleteness}%</span>
              </div>
              <p className="text-xs text-zinc-500">
                {cvCompleteness === 100
                  ? "Tu CV está completo"
                  : `${7 - Math.round(cvCompleteness / 100 * 7)} secciones pendientes`}
              </p>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">No tenés un CV creado aún</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-xl">
          <h3 className="font-semibold text-white mb-4">Acciones rápidas</h3>
          <div className="space-y-1.5">
            <Link
              href="/cv/edit"
              className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800/60 hover:text-indigo-400 font-medium transition-all duration-200 group"
            >
              <span className="w-8 h-8 rounded-lg bg-zinc-800/60 flex items-center justify-center group-hover:bg-indigo-500/10 transition-colors">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </span>
              Editar CV
            </Link>
            <Link
              href="/chat"
              className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800/60 hover:text-indigo-400 font-medium transition-all duration-200 group"
            >
              <span className="w-8 h-8 rounded-lg bg-zinc-800/60 flex items-center justify-center group-hover:bg-indigo-500/10 transition-colors">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </span>
              Hablar con asistente
            </Link>
            <Link
              href="/cv/analysis"
              className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800/60 hover:text-indigo-400 font-medium transition-all duration-200 group"
            >
              <span className="w-8 h-8 rounded-lg bg-zinc-800/60 flex items-center justify-center group-hover:bg-indigo-500/10 transition-colors">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </span>
              Analizar CV
            </Link>
          </div>
        </div>

        {/* Recent Sessions */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white">Sesiones recientes</h3>
            {totalSessions > 0 && (
              <span className="text-xs text-zinc-500">{totalSessions} total</span>
            )}
          </div>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-8 bg-zinc-800 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : recentSessions.length > 0 ? (
            <ul className="space-y-1">
              {recentSessions.map((s) => (
                <li key={s.session_id}>
                  <Link
                    href={`/chat?session=${s.session_id}`}
                    className="flex items-center gap-2 text-sm text-zinc-400 hover:text-indigo-400 transition-colors rounded-lg px-2.5 py-2 hover:bg-zinc-800/40"
                  >
                    <svg className="w-3.5 h-3.5 flex-shrink-0 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    <span className="truncate">{s.title || "Sesión sin título"}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-center">
              <div className="w-10 h-10 rounded-xl bg-zinc-800/60 flex items-center justify-center mb-3">
                <svg className="w-5 h-5 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <p className="text-sm text-zinc-500">Empezá una conversación</p>
              <Link
                href="/chat"
                className="mt-2 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                Abrir asistente →
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Stats row */}
      {hasCv && !loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-3.5 flex items-center gap-3">
              <div className={`w-9 h-9 rounded-lg ${stat.bg} flex items-center justify-center flex-shrink-0`}>
                <stat.icon className={`w-4 h-4 ${stat.color}`} />
              </div>
              <div>
                <p className="text-lg font-bold text-white leading-tight">{stat.value}</p>
                <p className="text-xs text-zinc-500">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CV Sections Overview + Tips */}
      {hasCv && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Sections grid */}
          <div className="lg:col-span-2 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-white">Secciones del CV</h3>
                <p className="text-xs text-zinc-500 mt-0.5">{filledSections}/{cvSections.length} completadas</p>
              </div>
              <Link
                href="/cv/edit"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                Editar todo →
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {cvSections.map((section) => (
                <Link
                  key={section.name}
                  href={section.href}
                  className={`relative rounded-xl border p-3.5 transition-all duration-200 group ${
                    section.filled
                      ? "border-zinc-800 bg-zinc-800/30 hover:border-zinc-700"
                      : "border-dashed border-zinc-700/50 hover:border-zinc-600 hover:bg-zinc-800/20"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {section.filled ? (
                      <span className="w-5 h-5 rounded-full bg-emerald-500/15 flex items-center justify-center">
                        <svg className="w-3 h-3 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </span>
                    ) : (
                      <span className="w-5 h-5 rounded-full bg-zinc-800 flex items-center justify-center">
                        <svg className="w-3 h-3 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                      </span>
                    )}
                    <span className={`text-xs font-medium ${section.filled ? "text-zinc-300" : "text-zinc-500"}`}>
                      {section.name}
                    </span>
                  </div>
                  <p className={`text-[11px] ${section.filled ? "text-zinc-500" : "text-zinc-600"}`}>
                    {section.filled ? "Completado" : "Pendiente"}
                  </p>
                </Link>
              ))}
            </div>
          </div>

          {/* Tips panel */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5 shadow-xl">
            <h3 className="font-semibold text-white mb-4">Mejorá tu CV</h3>
            <div className="space-y-3">
              {cvCompleteness < 100 && (
                <TipCard
                  icon={<svg className="w-4 h-4 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>}
                  title="Completá las secciones faltantes"
                  description="Un CV completo tiene más chances de ser elegido."
                />
              )}
              {!cv!.cv.about && (
                <TipCard
                  icon={<svg className="w-4 h-4 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0zM12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z" /></svg>}
                  title="Agregá un perfil profesional"
                  description="Un resumen breve de tu perfil ayuda al reclutador."
                />
              )}
              {cv!.experiences.length > 0 && cv!.experiences.length < 3 && (
                <TipCard
                  icon={<svg className="w-4 h-4 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></svg>}
                  title="Sumá más experiencias"
                  description="Mostrá tu trayectoria completa."
                />
              )}
              <TipCard
                icon={<svg className="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>}
                title="Consultá al asistente IA"
                description="Preguntale cómo mejorar tu CV para un puesto específico."
              />
            </div>
          </div>
        </div>
      )}

      {/* No CV state */}
      {!hasCv && !loading && (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-10 shadow-xl text-center">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center mx-auto mb-5">
            <svg className="w-8 h-8 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Empezá creando tu CV</h3>
          <p className="text-sm text-zinc-400 max-w-md mx-auto mb-6">
            Completá tu información para que el asistente IA pueda ayudarte a mejorar tu perfil y compararlo con ofertas laborales.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/cv/edit"
              className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-500 transition-all"
            >
              Crear mi CV
            </Link>
            <Link
              href="/chat"
              className="rounded-xl border border-zinc-700 bg-zinc-800/60 px-6 py-2.5 text-sm font-medium text-zinc-300 hover:border-zinc-600 hover:text-white transition-all"
            >
              Hablar con asistente
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function TipCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-800/30 p-3.5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex-shrink-0">{icon}</span>
        <div>
          <p className="text-sm font-medium text-zinc-200">{title}</p>
          <p className="text-xs text-zinc-500 mt-0.5">{description}</p>
        </div>
      </div>
    </div>
  );
}

function BriefcaseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );
}

function WrenchIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

function GraduationIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
      <path d="M6 12v5c3 3 6 3 6 3s3 0 6-3v-5" />
    </svg>
  );
}

function GlobeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function ChatIcon2({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}
