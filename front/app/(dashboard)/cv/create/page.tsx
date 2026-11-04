"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/app/lib/auth";
import { getFullCV } from "@/app/lib/api";
import type { FullCV } from "@/app/lib/types";
import { cvCompleteness, sectionProgress } from "@/app/lib/cv-validation";
import { PersonalStep } from "./steps/personal";
import { ExperienceStep } from "./steps/experience";
import { EducationStep } from "./steps/education";
import { SkillsStep } from "./steps/skills";
import { ExtrasStep } from "./steps/extras";
import { ReviewStep } from "./steps/review";

/**
 * Asistente para crear el CV: un paso por pantalla, barra de progreso y
 * guardado real en el backend al avanzar. Cada paso maneja sus propios
 * formularios y le avisa al shell con `onChanged` (refresco silencioso, sin
 * spinner) o con `onAdvance` (paso siguiente).
 *
 * El editor `/cv/edit` queda para retocar; este flujo es para armar el CV
 * desde cero sin enfrentarse a la página completa.
 */

interface StepDefinition {
  key: string;
  label: string;
  /** Si el paso ya tiene datos, se muestra como completado. */
  isFilled: (cv: FullCV) => boolean;
}

const STEPS: StepDefinition[] = [
  {
    key: "personal",
    label: "Datos personales",
    isFilled: (cv) => !!(cv.cv.name && cv.cv.email),
  },
  {
    key: "experience",
    label: "Experiencia",
    isFilled: (cv) => cv.experiences.length > 0,
  },
  {
    key: "education",
    label: "Formación",
    isFilled: (cv) => cv.education.length > 0,
  },
  {
    key: "skills",
    label: "Habilidades",
    isFilled: (cv) => cv.skills.length > 0 || cv.programs.length > 0,
  },
  {
    key: "extras",
    label: "Logros e idiomas",
    isFilled: (cv) => cv.achievements.length > 0 || cv.languages.length > 0,
  },
  {
    key: "review",
    label: "Revisar",
    isFilled: (cv) => !!(cv.cv.name && cv.cv.email),
  },
];

const stepStorageKey = (userId: string) => `cv_wizard_step:${userId}`;

export default function CreateCVWizardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [cv, setCv] = useState<FullCV | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stepIdx, setStepIdx] = useState(0);
  const [maxVisited, setMaxVisited] = useState(0);

  const refreshCV = useCallback(async () => {
    if (!user) return;
    try {
      const data = await getFullCV(user.id);
      setCv(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo actualizar el CV");
    }
  }, [user]);

  // Carga inicial + retomada del paso en el que quedó.
  useEffect(() => {
    if (!user) return;
    let cancelled = false;

    const load = async () => {
      try {
        const data = await getFullCV(user.id);
        if (cancelled) return;
        setCv(data);

        const stored = Number.parseInt(
          window.localStorage.getItem(stepStorageKey(user.id)) ?? "0",
          10,
        );
        const resume = Number.isFinite(stored)
          ? Math.min(Math.max(stored, 0), STEPS.length - 1)
          : 0;
        setStepIdx(resume);
        setMaxVisited(resume);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "No se pudo cargar el CV");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [user]);

  const goTo = useCallback(
    (next: number) => {
      const target = Math.min(Math.max(next, 0), STEPS.length - 1);
      setStepIdx(target);
      setMaxVisited((current) => Math.max(current, target));
      if (user) {
        window.localStorage.setItem(stepStorageKey(user.id), String(target));
      }
      // El formulario del paso recién abierto arranca arriba.
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [user],
  );

  const handleFinish = useCallback(() => {
    if (user) {
      window.localStorage.removeItem(stepStorageKey(user.id));
    }
    router.push("/dashboard");
  }, [router, user]);

  const progress = useMemo(
    () => (cv ? sectionProgress(cv) : null),
    [cv],
  );

  if (!user) return null;

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#6366F1] border-t-transparent" />
      </div>
    );
  }

  if (!cv) {
    return (
      <div className="flex flex-col items-center gap-4 py-20">
        <p className="text-[#EF4444]">
          {error ?? "No se pudo cargar tu CV"}
        </p>
        <Link
          href="/dashboard"
          className="rounded-lg bg-[#6366F1] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#6366F1]/90"
        >
          Volver al dashboard
        </Link>
      </div>
    );
  }

  const activeStep = STEPS[stepIdx];
  const isLastStep = stepIdx === STEPS.length - 1;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* ── Header + progreso ─────────────────────────────────────────── */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold text-[#F8FAFC]">
            Crear mi CV
          </h1>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Un paso por vez: cargás, guardás y seguís. Nada se pierde si cerrás
            la pestaña.
          </p>
        </div>
        <Link
          href="/cv/edit"
          className="rounded-lg border border-[#334155] bg-[#1E293B] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-colors hover:border-[#6366F1]/30 hover:bg-[#0F172A]"
        >
          Ir al editor completo
        </Link>
      </div>

      <nav aria-label="Progreso del asistente">
        <ol className="flex flex-wrap gap-2">
          {STEPS.map((step, index) => {
            const isCurrent = index === stepIdx;
            const canJump = index <= maxVisited;
            const filled = step.isFilled(cv);
            return (
              <li key={step.key}>
                <button
                  type="button"
                  onClick={() => canJump && goTo(index)}
                  disabled={!canJump}
                  aria-current={isCurrent ? "step" : undefined}
                  className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                    isCurrent
                      ? "border-[#6366F1] bg-[#6366F1]/15 text-[#818CF8]"
                      : canJump
                        ? "border-[#334155] bg-[#1E293B] text-[#CBD5E1] hover:border-[#6366F1]/40"
                        : "border-[#1E293B] bg-[#0F172A] text-[#64748B]"
                  }`}
                >
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] font-bold ${
                      filled && !isCurrent
                        ? "bg-[#10B981]/20 text-[#10B981]"
                        : isCurrent
                          ? "bg-[#6366F1] text-white"
                          : "bg-[#334155] text-[#94A3B8]"
                    }`}
                  >
                    {filled && !isCurrent ? "✓" : index + 1}
                  </span>
                  {step.label}
                </button>
              </li>
            );
          })}
        </ol>
        {progress && (
          <p className="mt-2 text-xs text-[#64748B]">
            {progress.filled}/{progress.total} secciones del CV completadas ·{" "}
            {cvCompleteness(cv)}% de completitud
          </p>
        )}
      </nav>

      {error && (
        <div className="rounded-lg border border-[#EF4444]/20 bg-[#EF4444]/10 px-4 py-2.5 text-sm text-[#EF4444]">
          {error}
        </div>
      )}

      {/* ── Paso activo ───────────────────────────────────────────────── */}
      <section className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl">
        <div className="mb-5 flex items-baseline justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-[#6366F1]">
              Paso {stepIdx + 1} de {STEPS.length}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-[#F1F5F9]">
              {activeStep.label}
            </h2>
          </div>
          {!isLastStep && (
            <button
              type="button"
              onClick={() => goTo(stepIdx + 1)}
              className="text-xs text-[#94A3B8] underline-offset-2 transition-colors hover:text-[#CBD5E1] hover:underline"
            >
              Ir al paso {stepIdx + 2}
            </button>
          )}
        </div>

        {stepIdx === 0 && (
          <PersonalStep userId={user.id} cv={cv} onChanged={refreshCV} onAdvance={() => goTo(1)} />
        )}
        {stepIdx === 1 && (
          <ExperienceStep userId={user.id} cv={cv} onChanged={refreshCV} onAdvance={() => goTo(2)} />
        )}
        {stepIdx === 2 && (
          <EducationStep userId={user.id} cv={cv} onChanged={refreshCV} onAdvance={() => goTo(3)} />
        )}
        {stepIdx === 3 && (
          <SkillsStep userId={user.id} cv={cv} onChanged={refreshCV} onAdvance={() => goTo(4)} />
        )}
        {stepIdx === 4 && (
          <ExtrasStep userId={user.id} cv={cv} onChanged={refreshCV} onAdvance={() => goTo(5)} />
        )}
        {stepIdx === 5 && (
          <ReviewStep
            userId={user.id}
            cv={cv}
            onChanged={refreshCV}
            onAdvance={() => goTo(5)}
            onFinish={handleFinish}
          />
        )}
      </section>

      {/* ── Volver al paso anterior ─────────────────────────────────────── */}
      {stepIdx > 0 && (
        <div className="flex justify-start">
          <button
            type="button"
            onClick={() => goTo(stepIdx - 1)}
            className="text-sm text-[#94A3B8] underline-offset-2 transition-colors hover:text-[#F1F5F9] hover:underline"
          >
            ← Paso anterior
          </button>
        </div>
      )}
    </div>
  );
}
