"use client";

import { useState } from "react";
import Link from "next/link";

import { exportCV } from "@/app/lib/api";
import { cvCompleteness, sectionProgress } from "@/app/lib/cv-validation";
import {
  StepActions,
  StepError,
  type StepProps,
} from "../components/form-ui";

type ExportFormat = "pdf" | "docx";

interface ReviewStepProps extends StepProps {
  /** Cierra el asistente: borra el paso guardado y vuelve al dashboard. */
  onFinish: () => void;
}

/**
 * Paso final: qué tan completo está el CV, qué falta (con acceso directo a
 * cada sección) y la descarga en el formato ATS.
 */
export function ReviewStep({ userId, cv, onFinish }: ReviewStepProps) {
  const progress = sectionProgress(cv);
  const percent = cvCompleteness(cv);
  const [downloading, setDownloading] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | undefined>();
  const [notice, setNotice] = useState<string | undefined>();

  const handleDownload = async (format: ExportFormat) => {
    setDownloading(format);
    setError(undefined);
    setNotice(undefined);
    try {
      await exportCV({ user_id: userId, format });
      setNotice(`Se descargó tu CV en ${format.toUpperCase()}.`);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "No se pudo generar el archivo",
      );
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-5">
      {/* ── Estado general ─────────────────────────────────────────────── */}
      <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-sm font-medium text-[#F1F5F9]">
            {progress.filled} de {progress.total} secciones completas
          </p>
          <span className="text-lg font-bold text-[#818CF8]">{percent}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#0F172A] ring-1 ring-[#334155]">
          <div
            className="h-full rounded-full bg-[#6366F1] transition-all duration-500"
            style={{ width: `${percent}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-[#64748B]">
          {percent >= 80
            ? "Tu CV está listo para postularte."
            : "Completá lo que falte: cada sección suma para los filtros automáticos."}
        </p>
      </div>

      {/* ── Secciones ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {progress.sections.map((section) => (
          <div
            key={section.key}
            className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 ${
              section.filled
                ? "border-[#10B981]/25 bg-[#10B981]/5"
                : "border-dashed border-[#334155] bg-[#0F172A]"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                  section.filled
                    ? "bg-[#10B981]/20 text-[#10B981]"
                    : "bg-[#334155] text-[#94A3B8]"
                }`}
              >
                {section.filled ? "✓" : "!"}
              </span>
              <span className="text-sm text-[#CBD5E1]">{section.label}</span>
            </div>
            <Link
              href="/cv/edit"
              className="text-xs font-medium text-[#6366F1] transition-colors hover:text-[#818CF8]"
            >
              {section.filled ? "Revisar" : "Completar"}
            </Link>
          </div>
        ))}
      </div>

      {/* ── Descarga ───────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
        <h3 className="font-medium text-[#F8FAFC]">Descargar mi CV</h3>
        <p className="mt-0.5 text-xs text-[#64748B]">
          Formato Harvard, una columna y texto legible por los sistemas ATS.
        </p>
        <div className="mt-3 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="rounded-lg bg-[#6366F1] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
          >
            {downloading === "pdf" ? "Generando…" : "Descargar PDF"}
          </button>
          <button
            type="button"
            onClick={() => handleDownload("docx")}
            disabled={downloading !== null}
            className="rounded-lg border border-[#6366F1]/30 bg-[#6366F1]/10 px-5 py-2.5 text-sm font-medium text-[#818CF8] transition-colors hover:bg-[#6366F1]/20 disabled:opacity-50"
          >
            {downloading === "docx" ? "Generando…" : "Descargar DOCX"}
          </button>
          <Link
            href="/cv/analysis"
            className="rounded-lg border border-[#334155] bg-[#0F172A] px-5 py-2.5 text-sm font-medium text-[#F1F5F9] transition-colors hover:border-[#6366F1]/30 hover:bg-[#1E293B]"
          >
            Ver análisis ATS
          </Link>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <StepError message={error} />
          {notice && <p className="text-xs text-[#10B981]">{notice}</p>}
        </div>
      </div>

      <StepActions
        onNext={onFinish}
        nextLabel="Terminar y ir al dashboard"
      />
    </div>
  );
}
