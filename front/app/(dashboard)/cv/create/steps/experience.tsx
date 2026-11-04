"use client";

import { useRef, useState } from "react";

import {
  addExperience,
  apiErrorMessage,
  deleteExperience,
  isNotFoundError,
  updateExperience,
} from "@/app/lib/api";
import type { ExperienceResponse } from "@/app/lib/types";
import {
  hasErrors,
  toDateInput,
  validateExperience,
  type ExperienceData,
  type FieldErrors,
} from "@/app/lib/cv-validation";
import {
  DateField,
  ItemCard,
  SaveState,
  StepActions,
  StepError,
  TextAreaField,
  TextField,
  type StepProps,
} from "../components/form-ui";

const EMPTY: ExperienceData = {
  title: "",
  company: "",
  start_date: "",
  end_date: "",
  description: "",
};

const DESCRIPTION_HINT = "Verbos de acción y métricas: “optimicé”, “30% menos tiempo”";

/**
 * Paso 2: experiencia laboral. Cada alta y edición se guarda en el backend
 * en el momento, así que "Continuar" no tiene nada que validar.
 */
export function ExperienceStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<ExperienceData>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [general, setGeneral] = useState<string | undefined>();
  const deletingRef = useRef(false);

  const experiences = cv.experiences;

  const setField =
    (key: keyof ExperienceData) =>
    (value: string) => {
      setForm((current) => ({ ...current, [key]: value }));
      setErrors((current) => {
        if (!current[key]) return current;
        const next = { ...current };
        delete next[key];
        return next;
      });
    };

  const resetForm = () => {
    setForm(EMPTY);
    setErrors({});
    setEditId(null);
    setShowForm(false);
    setGeneral(undefined);
  };

  const openEdit = (experience: ExperienceResponse) => {
    setForm({
      title: experience.title,
      company: experience.company,
      start_date: toDateInput(experience.start_date),
      end_date: toDateInput(experience.end_date),
      description: experience.description,
    });
    setErrors({});
    setEditId(experience.id);
    setGeneral(undefined);
    setShowForm(true);
  };

  const handleSave = async () => {
    const found = validateExperience(form);
    setErrors(found);
    if (hasErrors(found)) return;

    setStatus("saving");
    setGeneral(undefined);
    try {
      const payload = {
        user_id: userId,
        title: form.title.trim(),
        company: form.company.trim(),
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
        description: form.description.trim(),
      };
      if (editId) {
        await updateExperience(editId, payload);
      } else {
        await addExperience(payload);
      }
      await onChanged();
      setStatus("saved");
      resetForm();
    } catch (e) {
      setStatus("error");
      setGeneral(apiErrorMessage(e, "No se pudo guardar la experiencia"));
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteExperience(id, userId);
    } catch (e) {
      // Que ya no exista es el resultado deseado, no un fallo.
      if (!isNotFoundError(e)) {
        setGeneral(apiErrorMessage(e, "No se pudo eliminar la experiencia"));
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        La experiencia es lo que más pesa en un CV. Si todavía no tenés, podés
        avanzar: después la cargás cuando la tengas.
      </p>

      {showForm ? (
        <div className="rounded-xl border border-[#6366F1]/30 bg-[#0F172A] p-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <TextField
              label="Puesto o proyecto"
              value={form.title}
              onChange={setField("title")}
              error={errors.title}
              placeholder="Backend Developer"
              required
              autoFocus
            />
            <TextField
              label="Empresa u organización"
              value={form.company}
              onChange={setField("company")}
              error={errors.company}
              placeholder="Acme S.A. · Freelance · Proyecto personal"
              required
            />
            <DateField
              label="Fecha de inicio"
              value={form.start_date}
              onChange={setField("start_date")}
              error={errors.start_date}
            />
            <DateField
              label="Fecha de fin"
              value={form.end_date}
              onChange={setField("end_date")}
              error={errors.end_date}
              hint="Vacío = actualidad"
            />
          </div>

          <div className="mt-4">
            <TextAreaField
              label="Qué hiciste"
              value={form.description}
              onChange={setField("description")}
              rows={4}
              hint={DESCRIPTION_HINT}
              placeholder="Desarrollé APIs en Python con FastAPI; reduje la latencia un 30%."
            />
          </div>

          <StepError message={general} />

          <div className="mt-4 flex items-center justify-between gap-3">
            <SaveState status={status} />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={resetForm}
                className="rounded-lg border border-[#334155] bg-[#0F172A] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-colors hover:bg-[#1E293B]"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={status === "saving"}
                className="rounded-lg bg-[#6366F1] px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
              >
                {status === "saving" ? "Guardando…" : editId ? "Actualizar" : "Agregar"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="rounded-lg bg-[#6366F1] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-colors hover:bg-[#6366F1]/90"
        >
          + Agregar experiencia
        </button>
      )}

      {experiences.length === 0 && !showForm ? (
        <p className="rounded-xl border border-dashed border-[#334155] px-4 py-8 text-center text-sm text-[#64748B]">
          Todavía no agregaste experiencia. Está bien: podés seguir y agregarla
          más adelante.
        </p>
      ) : (
        <div className="space-y-3">
          {experiences.map((experience) => (
            <ItemCard
              key={experience.id}
              title={experience.title}
              subtitle={experience.company}
              meta={[
                toDateInput(experience.start_date),
                toDateInput(experience.end_date) || "Actualidad",
              ]
                .filter(Boolean)
                .join(" — ")}
              description={experience.description}
              onEdit={() => openEdit(experience)}
              onDelete={() => handleDelete(experience.id)}
            />
          ))}
        </div>
      )}

      <StepActions onNext={onAdvance} onSkip={onAdvance} skipLabel="Todavía no tengo experiencia" />
    </div>
  );
}
