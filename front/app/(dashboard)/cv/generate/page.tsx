"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/app/lib/auth";
import { getFullCV } from "@/app/lib/api";
import type { FullCV } from "@/app/lib/types";
import Link from "next/link";

// ─── Generate CV Page ────────────────────────────────────────────────────────

export default function CVGeneratePage() {
  const { user } = useAuth();
  const [cv, setCv] = useState<FullCV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCV = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getFullCV(user.id);
      setCv(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar el CV");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchCV();
  }, [fetchCV]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchCV}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
        Generar CV
      </h1>

      {/* ── Notice ─────────────────────────────────────────────────────── */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
        <p className="font-medium">Nota</p>
        <p className="mt-1">
          La generación se realiza en el servidor. El archivo se descargará
          automáticamente.
        </p>
      </div>

      {/* ── CV Preview ─────────────────────────────────────────────────── */}
      {cv && (
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
            Vista previa
          </h2>

          {/* Personal info */}
          <div className="mb-6">
            <h3 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Información Personal
            </h3>
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
              <PreviewField label="Nombre" value={cv.cv.name} />
              <PreviewField label="Email" value={cv.cv.email} />
              <PreviewField label="Teléfono" value={cv.cv.phone} />
              <PreviewField label="Dirección" value={cv.cv.address} />
              {cv.cv.porfolio && (
                <PreviewField label="Portfolio" value={cv.cv.porfolio} />
              )}
              {cv.cv.linkedin && (
                <PreviewField label="LinkedIn" value={cv.cv.linkedin} />
              )}
            </div>
            {cv.cv.about && (
              <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-400">
                {cv.cv.about}
              </p>
            )}
          </div>

          {/* Experiences */}
          {cv.experiences.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Experiencia
              </h3>
              <div className="mt-2 space-y-3">
                {cv.experiences.map((exp) => (
                  <div
                    key={exp.id}
                    className="rounded-lg border border-zinc-100 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-800/50"
                  >
                    <p className="font-medium text-zinc-900 dark:text-white">
                      {exp.title}
                    </p>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      {exp.company} · {exp.start_date ?? "—"} —{" "}
                      {exp.end_date ?? "Presente"}
                    </p>
                    {exp.description && (
                      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-500">
                        {exp.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills */}
          {cv.skills.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Habilidades
              </h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {cv.skills.map((skill) => (
                  <span
                    key={skill.id}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-sm text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {skill.name}{" "}
                    <span className="text-zinc-400">· {skill.level}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {cv.education.length > 0 && (
            <div>
              <h3 className="text-sm font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Formación
              </h3>
              <div className="mt-2 space-y-3">
                {cv.education.map((edu) => (
                  <div
                    key={edu.id}
                    className="rounded-lg border border-zinc-100 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-800/50"
                  >
                    <p className="font-medium text-zinc-900 dark:text-white">
                      {edu.degree}
                    </p>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400">
                      {edu.institution} · {edu.start_date ?? "—"} —{" "}
                      {edu.end_date ?? "Presente"}
                    </p>
                    {edu.description && (
                      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-500">
                        {edu.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* ── Generate buttons ───────────────────────────────────────────── */}
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
          Descargar
        </h2>
        <div className="flex gap-3">
          <button
            disabled
            className="rounded-lg bg-zinc-200 px-6 py-3 text-sm font-medium text-zinc-500 cursor-not-allowed dark:bg-zinc-700 dark:text-zinc-400"
          >
            Generar PDF
          </button>
          <button
            disabled
            className="rounded-lg bg-zinc-200 px-6 py-3 text-sm font-medium text-zinc-500 cursor-not-allowed dark:bg-zinc-700 dark:text-zinc-400"
          >
            Generar DOCX
          </button>
        </div>
        <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-500">
          TODO: Implementar endpoint de generación en el backend (Prefect flow).
        </p>
      </section>

      {/* ── Back button ────────────────────────────────────────────────── */}
      <div className="flex justify-start">
        <Link
          href="/cv/edit"
          className="rounded-lg bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-white dark:hover:bg-zinc-600"
        >
          ← Volver al editor
        </Link>
      </div>
    </div>
  );
}

// ─── Preview Field ───────────────────────────────────────────────────────────

function PreviewField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  if (!value) return null;
  return (
    <div>
      <span className="text-xs text-zinc-500 dark:text-zinc-500">{label}</span>
      <p className="text-zinc-900 dark:text-white">{value}</p>
    </div>
  );
}
