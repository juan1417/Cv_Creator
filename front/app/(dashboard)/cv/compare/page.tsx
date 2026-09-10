"use client";

import { useState } from "react";
import { useAuth } from "@/app/lib/auth";
import { compareCVJob, adaptCVForJob } from "@/app/lib/api";
import type { JobMatchResult, CVAdaptationResult } from "@/app/lib/types";

type Step = "input" | "results" | "adapted";

export default function ComparePage() {
  const { user } = useAuth();
  const [jobDescription, setJobDescription] = useState("");
  const [step, setStep] = useState<Step>("input");
  const [matchResult, setMatchResult] = useState<JobMatchResult | null>(null);
  const [adaptResult, setAdaptResult] = useState<CVAdaptationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ── Compare ────────────────────────────────────────────────────────────

  const handleCompare = async () => {
    if (!user || !jobDescription.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await compareCVJob(user.id, jobDescription);
      setMatchResult(result);
      setStep("results");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  // ── Adapt ──────────────────────────────────────────────────────────────

  const handleAdapt = async () => {
    if (!user || !matchResult) return;
    setLoading(true);
    setError("");
    try {
      const result = await adaptCVForJob(
        user.id,
        jobDescription,
        matchResult.missing_skills.map((s) => ({
          name: s.name,
          importance: s.importance,
        })),
      );
      setAdaptResult(result);
      setStep("adapted");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  // ── Score helpers ──────────────────────────────────────────────────────

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-[#10B981]";
    if (score >= 50) return "text-[#F59E0B]";
    return "text-[#EF4444]";
  };

  const scoreRing = (score: number) => {
    if (score >= 80) return "#10B981";
    if (score >= 50) return "#F59E0B";
    return "#EF4444";
  };

  const importanceColor = (imp: string) => {
    if (imp === "Alta") return "bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20";
    if (imp === "Media") return "bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20";
    return "bg-slate-700/50 text-slate-400 border border-slate-600/30";
  };

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-white">
          Comparar CV con Puesto
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Pegá la descripción del puesto y descubrí qué tan bien encaja tu CV
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm">
        {(["input", "results", "adapted"] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            {i > 0 && <span className="text-slate-600">→</span>}
            <span
              className={`rounded-full px-3 py-1 font-medium transition-all duration-200 ${
                step === s
                  ? "bg-[#6366F1] text-white shadow-lg shadow-indigo-500/25"
                  : "bg-slate-800 text-slate-500 border border-slate-700"
              }`}
            >
              {s === "input" ? "1. Descripcion" : s === "results" ? "2. Analisis" : "3. Adaptado"}
            </span>
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-[#EF4444]/20 bg-[#EF4444]/10 px-4 py-3 text-sm text-[#EF4444] backdrop-blur-sm">
          {error}
        </div>
      )}

      {/* Step 1: Input */}
      {step === "input" && (
        <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-6 shadow-xl backdrop-blur-sm">
          <label className="block text-sm font-medium text-slate-300">
            Descripcion del puesto
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={12}
            placeholder="Pegá aquí la descripción completa del puesto al que te querés postular. Incluí requisitos, responsabilidades, tecnologías, etc."
            className="mt-2 w-full resize-none rounded-xl border border-[#1E293B] bg-[#090D16] px-4 py-3 text-sm text-white placeholder-slate-500 transition-all duration-200 focus:border-[#6366F1] focus:outline-none focus:ring-1 focus:ring-[#6366F1]/50"
          />
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleCompare}
              disabled={loading || !jobDescription.trim()}
              className="rounded-xl bg-[#6366F1] px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-[#6366F1]/90 hover:shadow-indigo-500/40 disabled:opacity-50 disabled:shadow-none"
            >
              {loading ? "Analizando..." : "Comparar con mi CV"}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Results */}
      {step === "results" && matchResult && (
        <div className="space-y-6">
          {/* Score */}
          <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-6 shadow-xl backdrop-blur-sm">
            <div className="flex items-center gap-6">
              <div className="relative h-32 w-32">
                <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
                  <circle
                    cx="60" cy="60" r="50"
                    fill="none"
                    stroke="#1E293B"
                    strokeWidth="10"
                  />
                  <circle
                    cx="60" cy="60" r="50"
                    fill="none"
                    stroke={scoreRing(matchResult.match_score)}
                    strokeWidth="10"
                    strokeDasharray={`${(matchResult.match_score / 100) * 314} 314`}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                    style={{ filter: `drop-shadow(0 0 6px ${scoreRing(matchResult.match_score)}40)` }}
                  />
                </svg>
                <span className={`absolute inset-0 flex items-center justify-center text-3xl font-bold ${scoreColor(matchResult.match_score)}`}>
                  {matchResult.match_score}%
                </span>
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-white">
                  Compatibilidad con el puesto
                </h2>
                <p className="mt-1 text-sm leading-relaxed text-slate-400">
                  {matchResult.summary}
                </p>
              </div>
            </div>
          </div>

          {/* Skills */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Matching skills */}
            <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-[#10B981]">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#10B981]/10 text-xs">✓</span>
                Skills que tenés ({matchResult.matching_skills.length})
              </h3>
              <div className="space-y-2">
                {matchResult.matching_skills.map((skill, i) => (
                  <div key={i} className="rounded-xl border border-[#10B981]/10 bg-[#10B981]/5 px-3 py-2.5 transition-all duration-200 hover:border-[#10B981]/20">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{skill.name}</span>
                      <span className="text-xs font-medium text-[#10B981]">{skill.level}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">{skill.relevance}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Missing skills */}
            <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-[#EF4444]">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#EF4444]/10 text-xs">✗</span>
                Skills que faltan ({matchResult.missing_skills.length})
              </h3>
              <div className="space-y-2">
                {matchResult.missing_skills.map((skill, i) => (
                  <div key={i} className="rounded-xl border border-[#EF4444]/10 bg-[#EF4444]/5 px-3 py-2.5 transition-all duration-200 hover:border-[#EF4444]/20">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{skill.name}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${importanceColor(skill.importance)}`}>
                        {skill.importance}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">{skill.suggestion}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Strengths & Weaknesses */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
              <h3 className="mb-3 text-sm font-semibold text-[#10B981]">Fortalezas</h3>
              <ul className="space-y-2.5">
                {matchResult.strengths.map((s, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#10B981]" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
              <h3 className="mb-3 text-sm font-semibold text-[#F59E0B]">Debilidades</h3>
              <ul className="space-y-2.5">
                {matchResult.weaknesses.map((w, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[#F59E0B]" />
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-between">
            <button
              onClick={() => { setStep("input"); setMatchResult(null); }}
              className="rounded-xl border border-[#1E293B] bg-slate-800/50 px-4 py-2.5 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-[#6366F1]/30 hover:bg-slate-800"
            >
              Volver
            </button>
            <button
              onClick={handleAdapt}
              disabled={loading}
              className="rounded-xl bg-[#6366F1] px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-[#6366F1]/90 hover:shadow-indigo-500/40 disabled:opacity-50 disabled:shadow-none"
            >
              {loading ? "Adaptando..." : "Adaptar mi CV para este puesto"}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Adapted */}
      {step === "adapted" && adaptResult && (
        <div className="space-y-6">
          {/* Key changes */}
          <div className="rounded-2xl border border-[#8B5CF6]/20 bg-[#8B5CF6]/5 p-5 shadow-xl backdrop-blur-sm">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#8B5CF6]">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-[#8B5CF6]/20 text-[10px]">✦</span>
              Cambios principales
            </h3>
            <ul className="space-y-1.5">
              {adaptResult.key_changes.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-0.5 text-[#8B5CF6]">→</span>
                  {c}
                </li>
              ))}
            </ul>
          </div>

          {/* Adapted About */}
          <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
            <h3 className="mb-2 text-sm font-semibold text-slate-300">Sobre mí (adaptado)</h3>
            <div className="rounded-xl border border-[#1E293B] bg-[#090D16] p-4 text-sm leading-relaxed text-slate-300">
              {adaptResult.adapted_about}
            </div>
          </div>

          {/* Adapted Experiences */}
          <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Experiencia (adaptada)</h3>
            <div className="space-y-4">
              {adaptResult.adapted_experiences.map((exp, i) => (
                <div key={i} className="rounded-xl border border-[#1E293B] bg-[#090D16] p-4 transition-all duration-200 hover:border-[#6366F1]/20">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{exp.title}</span>
                    <span className="text-xs text-slate-500">{exp.company}</span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-400">{exp.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Adapted Skills */}
          <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Habilidades (reordenadas)</h3>
            <div className="flex flex-wrap gap-2">
              {adaptResult.adapted_skills.map((skill, i) => (
                <span
                  key={i}
                  className="rounded-full border border-[#6366F1]/20 bg-[#6366F1]/10 px-3 py-1 text-xs font-medium text-[#6366F1] transition-all duration-200 hover:bg-[#6366F1]/20"
                >
                  {skill.name} · {skill.level}
                </span>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 shadow-xl backdrop-blur-sm">
            <h3 className="mb-3 text-sm font-semibold text-slate-300">Consejos adicionales</h3>
            <ul className="space-y-2">
              {adaptResult.tips.map((t, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                  <span className="mt-1 h-1 w-1 flex-shrink-0 rounded-full bg-slate-600" />
                  {t}
                </li>
              ))}
            </ul>
          </div>

          {/* Actions */}
          <div className="flex justify-between">
            <button
              onClick={() => setStep("results")}
              className="rounded-xl border border-[#1E293B] bg-slate-800/50 px-4 py-2.5 text-sm font-medium text-slate-300 transition-all duration-200 hover:border-[#6366F1]/30 hover:bg-slate-800"
            >
              ← Volver al análisis
            </button>
            <button
              onClick={() => { setStep("input"); setMatchResult(null); setAdaptResult(null); setJobDescription(""); }}
              className="rounded-xl bg-[#6366F1] px-6 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/25 transition-all duration-200 hover:bg-[#6366F1]/90 hover:shadow-indigo-500/40"
            >
              Nuevo puesto
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
