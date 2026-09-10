"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/app/lib/auth";
import { analyzeCV } from "@/app/lib/api";
import { getDirtySections, clearDirtySections } from "@/app/lib/dirty-sections";
import type { CVAnalysis, MetricGroup } from "@/app/lib/types";
import Link from "next/link";

// ─── Analysis Page ───────────────────────────────────────────────────────────

export default function CVAnalysisPage() {
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState<CVAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reanalyzedSections, setReanalyzedSections] = useState<string[]>([]);

  const fetchAnalysis = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      // Obtener secciones modificadas desde el editor
      const dirty = getDirtySections();
      // Si hay secciones dirty, solo re-analizar esas
      // Si no hay, análisis completo (primera vez o todo limpio)
      const sections = dirty.length > 0 ? dirty : undefined;
      setReanalyzedSections(dirty);
      const data = await analyzeCV(user.id, sections);
      setAnalysis(data);
      // Limpiar dirty sections después del análisis exitoso
      if (dirty.length > 0) {
        clearDirtySections();
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Error al analizar el CV",
      );
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-[28px] font-bold text-[#F8FAFC]">
          Análisis del CV
        </h1>
        {/* Skeleton: Overall score */}
        <div className="rounded-2xl border border-[#334155] bg-[#1E293B] p-8 shadow-xl backdrop-blur-sm">
          <div className="flex flex-col items-center">
            <div className="h-[140px] w-[140px] animate-pulse rounded-full bg-[#0F172A]" />
            <div className="mt-4 h-4 w-64 animate-pulse rounded bg-[#0F172A]" />
          </div>
        </div>
        {/* Skeleton: Metric cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl backdrop-blur-sm">
              <div className="mb-3 flex items-center justify-between">
                <div className="h-4 w-32 animate-pulse rounded bg-[#0F172A]" />
                <div className="h-4 w-12 animate-pulse rounded bg-[#0F172A]" />
              </div>
              <div className="mb-4 h-2 animate-pulse rounded-full bg-[#0F172A]" />
              <div className="space-y-2">
                <div className="h-3 w-full animate-pulse rounded bg-[#0F172A]" />
                <div className="h-3 w-3/4 animate-pulse rounded bg-[#0F172A]" />
              </div>
            </div>
          ))}
        </div>
        <div className="flex justify-center">
          <p className="text-sm text-[#94A3B8] animate-pulse">
            La IA está analizando tu CV...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-[#EF4444]">{error}</p>
        <button
          onClick={fetchAnalysis}
          className="rounded-lg bg-[#6366F1] px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-[#6366F1]/90"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <h1 className="text-[28px] font-bold text-[#F8FAFC]">
          Análisis del CV
        </h1>
        {reanalyzedSections.length > 0 && (
          <span className="rounded-full bg-[#6366F1]/10 border border-[#6366F1]/20 px-3 py-1 text-xs font-medium text-[#6366F1]">
            Re-analizado: {reanalyzedSections.join(", ")}
          </span>
        )}
        {reanalyzedSections.length === 0 && analysis && (
          <span className="rounded-full bg-[#10B981]/10 border border-[#10B981]/20 px-3 py-1 text-xs font-medium text-[#10B981]">
            Desde cache
          </span>
        )}
      </div>

      {/* ── Overall Score ──────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-[#334155] bg-[#1E293B] p-8 shadow-xl backdrop-blur-sm">
        <div className="flex flex-col items-center">
          <ScoreGauge score={analysis.overall_score} />
          <p className="mt-4 max-w-lg text-center text-sm leading-relaxed text-[#94A3B8]">
            {analysis.summary}
          </p>
        </div>
      </section>

      {/* ── Metric Cards ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <MetricCard
          title="Completitud"
          metrics={analysis.completeness}
        />
        <MetricCard title="Contenido" metrics={analysis.content} />
        <MetricCard
          title="Compatibilidad ATS"
          metrics={analysis.ats_compatibility}
        />
        <MetricCard title="Estructura" metrics={analysis.structure} />
      </div>

      {/* ── Top Improvements ───────────────────────────────────────────── */}
      {analysis.top_improvements.length > 0 && (
        <section className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl backdrop-blur-sm">
          <h2 className="mb-4 text-lg font-semibold text-[#F1F5F9]">
            Mejoras recomendadas
          </h2>
          <ol className="space-y-2">
            {analysis.top_improvements.map((imp, i) => (
              <li
                key={i}
                className="flex gap-3 text-sm text-[#CBD5E1]"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#6366F1]/10 text-xs font-bold text-[#6366F1]">
                  {i + 1}
                </span>
                <span>{imp}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* ── Back button ────────────────────────────────────────────────── */}
      <div className="flex justify-start">
        <Link
          href="/cv/edit"
          className="rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-all duration-200 hover:border-[#6366F1]/30 hover:bg-[#0F172A]"
        >
          ← Volver al editor
        </Link>
      </div>
    </div>
  );
}

// ─── Score Gauge ─────────────────────────────────────────────────────────────

function ScoreGauge({ score }: { score: number }) {
  const color = getScoreColor(score);
  const glowColor = getGlowColor(score);
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle
          cx="70"
          cy="70"
          r="54"
          fill="none"
          stroke="#334155"
          strokeWidth="10"
        />
        <circle
          cx="70"
          cy="70"
          r="54"
          fill="none"
          stroke={glowColor}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
          style={{ filter: `drop-shadow(0 0 8px ${glowColor}40)` }}
        />
      </svg>
      <span className={`absolute text-3xl font-bold ${color}`}>
        {score}
      </span>
    </div>
  );
}

function getScoreColor(score: number): string {
  if (score >= 80) return "text-[#10B981]";
  if (score >= 50) return "text-[#F59E0B]";
  return "text-[#EF4444]";
}

function getGlowColor(score: number): string {
  if (score >= 80) return "#10B981";
  if (score >= 50) return "#F59E0B";
  return "#EF4444";
}

function getBarColor(score: number): string {
  if (score >= 80) return "bg-[#10B981]";
  if (score >= 50) return "bg-[#F59E0B]";
  return "bg-[#EF4444]";
}

// ─── Metric Card ─────────────────────────────────────────────────────────────

function MetricCard({
  title,
  metrics,
}: {
  title: string;
  metrics: MetricGroup;
}) {
  const [expanded, setExpanded] = useState(false);
  const details = metrics.details ?? [];

  const avgScore = Math.round(metrics.score ?? 0);
  const allSuggestions = details.flatMap((m) => m.suggestions ?? []);

  return (
    <div className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl backdrop-blur-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-[#F1F5F9]">
          {title}
        </h3>
        <span className="text-lg font-bold text-[#F8FAFC]">
          {avgScore}/100
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-[#0F172A]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getBarColor(avgScore)}`}
          style={{ width: `${avgScore}%` }}
        />
      </div>

      {/* Detail items */}
      <div className="space-y-2">
        {details.map((metric, i) => (
          <div
            key={i}
            className="flex items-center justify-between text-sm"
          >
            <span className="text-[#94A3B8]">
              {metric.name}
            </span>
            <span className="font-medium text-[#F8FAFC]">
              {metric.score}/{metric.max_score}
            </span>
          </div>
        ))}
      </div>

      {/* Suggestions toggle */}
      {allSuggestions.length > 0 && (
        <div className="mt-4 border-t border-[#334155] pt-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs font-medium text-[#6366F1] transition-all duration-200 hover:text-[#818CF8]"
          >
            {expanded ? "Ocultar" : "Ver"} sugerencias ({allSuggestions.length})
            <span
              className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            >
              ▾
            </span>
          </button>
          {expanded && (
            <ul className="mt-2 space-y-1">
              {allSuggestions.map((s, i) => (
                <li
                  key={i}
                  className="text-xs text-[#94A3B8]"
                >
                  • {s}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
