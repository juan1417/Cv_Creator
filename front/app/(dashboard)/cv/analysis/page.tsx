"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/app/lib/auth";
import { analyzeCV } from "@/app/lib/api";
import type { CVAnalysis, MetricDetail } from "@/app/lib/types";
import Link from "next/link";

// ─── Analysis Page ───────────────────────────────────────────────────────────

export default function CVAnalysisPage() {
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState<CVAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeCV(user.id);
      setAnalysis(data);
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
      <div className="flex flex-col items-center justify-center py-20">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">
          Analizando tu CV...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchAnalysis}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
        Análisis del CV
      </h1>

      {/* ── Overall Score ──────────────────────────────────────────────── */}
      <section className="rounded-xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex flex-col items-center">
          <ScoreGauge score={analysis.overall_score} />
          <p className="mt-4 max-w-lg text-center text-sm text-zinc-600 dark:text-zinc-400">
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
        <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
            Mejoras recomendadas
          </h2>
          <ol className="space-y-2">
            {analysis.top_improvements.map((imp, i) => (
              <li
                key={i}
                className="flex gap-3 text-sm text-zinc-700 dark:text-zinc-300"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
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
          className="rounded-lg bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-white dark:hover:bg-zinc-600"
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
          stroke="currentColor"
          strokeWidth="10"
          className="text-zinc-100 dark:text-zinc-800"
        />
        <circle
          cx="70"
          cy="70"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`transition-all duration-1000 ${color}`}
        />
      </svg>
      <span className="absolute text-3xl font-bold text-zinc-900 dark:text-white">
        {score}
      </span>
    </div>
  );
}

function getScoreColor(score: number): string {
  if (score < 40) return "text-red-500";
  if (score < 60) return "text-yellow-500";
  if (score < 80) return "text-orange-500";
  return "text-green-500";
}

function getBarColor(score: number): string {
  if (score < 40) return "bg-red-500";
  if (score < 60) return "bg-yellow-500";
  if (score < 80) return "bg-orange-500";
  return "bg-green-500";
}

// ─── Metric Card ─────────────────────────────────────────────────────────────

function MetricCard({
  title,
  metrics,
}: {
  title: string;
  metrics: Record<string, MetricDetail>;
}) {
  const [expanded, setExpanded] = useState(false);
  const entries = Object.values(metrics);

  // Calculate average score
  const totalScore = entries.reduce((sum, m) => sum + m.score, 0);
  const totalMax = entries.reduce((sum, m) => sum + m.max_score, 0);
  const avgScore = totalMax > 0 ? Math.round((totalScore / totalMax) * 100) : 0;

  // Collect all suggestions
  const allSuggestions = entries.flatMap((m) => m.suggestions);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-zinc-900 dark:text-white">
          {title}
        </h3>
        <span className="text-lg font-bold text-zinc-900 dark:text-white">
          {avgScore}/100
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-zinc-100 dark:bg-zinc-800">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getBarColor(avgScore)}`}
          style={{ width: `${avgScore}%` }}
        />
      </div>

      {/* Detail items */}
      <div className="space-y-2">
        {entries.map((metric, i) => (
          <div
            key={i}
            className="flex items-center justify-between text-sm"
          >
            <span className="text-zinc-600 dark:text-zinc-400">
              {metric.name}
            </span>
            <span className="font-medium text-zinc-900 dark:text-white">
              {metric.score}/{metric.max_score}
            </span>
          </div>
        ))}
      </div>

      {/* Suggestions toggle */}
      {allSuggestions.length > 0 && (
        <div className="mt-4 border-t border-zinc-100 pt-3 dark:border-zinc-800">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            {expanded ? "Ocultar" : "Ver"} sugerencias ({allSuggestions.length})
            <span
              className={`transition-transform ${expanded ? "rotate-180" : ""}`}
            >
              ▾
            </span>
          </button>
          {expanded && (
            <ul className="mt-2 space-y-1">
              {allSuggestions.map((s, i) => (
                <li
                  key={i}
                  className="text-xs text-zinc-600 dark:text-zinc-400"
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
