"use client";

import { useRef, useState } from "react";

import {
  addEducation,
  apiErrorMessage,
  deleteEducation,
  isNotFoundError,
} from "@/app/lib/api";
import type { EducationResponse } from "@/app/lib/types";
import {
  hasErrors,
  toDateInput,
  validateEducation,
  type EducationData,
  type FieldErrors,
} from "@/app/lib/cv-validation";
import {
  DateField,
  ItemCard,
  SaveState,
  StepActions,
  StepError,
  TextField,
  type StepProps,
} from "../components/form-ui";

const EMPTY: EducationData = {
  degree: "",
  institution: "",
  start_date: "",
  end_date: "",
};

/**
 * Paso 3: formación académica.
 *
 * La API no tiene endpoint de actualización para educación (sí alta y baja),
 * así que "editar" se hace alta nueva y recién después baja de la anterior:
 * si algo falla en el medio queda un duplicado visible, nunca un dato perdido.
 */
export function EducationStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<EducationData>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [general, setGeneral] = useState<string | undefined>();
  const deletingRef = useRef(false);

  const education = cv.education;

  const setField =
    (key: keyof EducationData) =>
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

  const openEdit = (item: EducationResponse) => {
    setForm({
      degree: item.degree,
      institution: item.institution,
      start_date: toDateInput(item.start_date),
      end_date: toDateInput(item.end_date),
    });
    setErrors({});
    setEditId(item.id);
    setGeneral(undefined);
    setShowForm(true);
  };

  const handleSave = async () => {
    const found = validateEducation(form);
    setErrors(found);
    if (hasErrors(found)) return;

    setStatus("saving");
    setGeneral(undefined);
    try {
      const payload = {
        user_id: userId,
        degree: form.degree.trim(),
        institution: form.institution.trim(),
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
      };
      // Alta primero, baja después (ver nota en la doc del componente).
      await addEducation(payload);
      if (editId) {
        try {
          await deleteEducation(editId, userId);
        } catch {
          // Si la baja falla queda un duplicado visible, no un dato perdido.
        }
      }
      await onChanged();
      setStatus("saved");
      resetForm();
    } catch (e) {
      setStatus("error");
      setGeneral(apiErrorMessage(e, "No se pudo guardar la formación"));
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteEducation(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        setGeneral(apiErrorMessage(e, "No se pudo eliminar la formación"));
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        Carreras, tecnicaturas, cursos largos y certificaciones importantes.
      </p>

      {showForm ? (
        <div className="rounded-xl border border-[#6366F1]/30 bg-[#0F172A] p-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <TextField
              label="Carrera o título"
              value={form.degree}
              onChange={setField("degree")}
              error={errors.degree}
              placeholder="Ingeniería en Sistemas"
              required
              autoFocus
            />
            <TextField
              label="Institución"
              value={form.institution}
              onChange={setField("institution")}
              error={errors.institution}
              placeholder="Universidad Nacional"
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
              hint="Vacío = en curso"
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
          + Agregar formación
        </button>
      )}

      {education.length === 0 && !showForm ? (
        <p className="rounded-xl border border-dashed border-[#334155] px-4 py-8 text-center text-sm text-[#64748B]">
          Todavía no agregaste formación. Podés avanzar y hacerlo más adelante.
        </p>
      ) : (
        <div className="space-y-3">
          {education.map((item) => (
            <ItemCard
              key={item.id}
              title={item.degree}
              subtitle={item.institution}
              meta={[
                toDateInput(item.start_date),
                toDateInput(item.end_date) || "En curso",
              ]
                .filter(Boolean)
                .join(" — ")}
              description={item.description}
              onEdit={() => openEdit(item)}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
        </div>
      )}

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Todavía no tengo formación que agregar"
      />
    </div>
  );
}
