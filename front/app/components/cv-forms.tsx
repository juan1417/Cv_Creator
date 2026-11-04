"use client";

import { useEffect, useRef, useState } from "react";

import {
  addAchievement,
  addEducation,
  addExperience,
  addLanguage,
  addProgram,
  addSkill,
  apiErrorMessage,
  deleteAchievement,
  deleteEducation,
  deleteExperience,
  deleteLanguage,
  deleteProgram,
  deleteSkill,
  isNotFoundError,
  searchSkillCatalog,
  updateExperience,
  type SkillCatalogItem,
} from "@/app/lib/api";
import { LANGUAGE_LEVELS, SKILL_LEVELS } from "@/app/lib/cv-constants";
import {
  hasErrors,
  toDateInput,
  validateAchievement,
  validateEducation,
  validateExperience,
  validateLanguage,
  validateSkillName,
  type AchievementData,
  type EducationData,
  type ExperienceData,
  type FieldErrors,
  type LanguageData,
} from "@/app/lib/cv-validation";
import {
  ChipList,
  DateField,
  FormError,
  ItemCard,
  SaveState,
  SelectField,
  TextAreaField,
  TextField,
} from "@/app/components/cv-form-ui";
import type { FullCV } from "@/app/lib/types";

/**
 * Formularios por entidad compartidos por el editor (`/cv/edit`) y el
 * asistente (`/cv/create`): una sola implementación de alta, edición, baja y
 * validación, para que los dos caminos no se comporten distinto.
 *
 * Guardan contra la API existente y avisan con `onChanged` (refresco
 * silencioso) y, si algo falla, con `onError`.
 */

interface ManagerProps {
  cv: FullCV;
  userId: string;
  onChanged: () => void;
  onError?: (message: string) => void;
  /** Si el padre ya pone el título, el encabezado interno se omite. */
  title?: string;
  subtitle?: string;
  /** El asistente ya tiene el marco: el componente no agrega borde ni fondo. */
  plain?: boolean;
}

type SaveStatus = "idle" | "saving" | "error";

const ADD_BUTTON =
  "rounded-lg bg-[#6366F1] px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50";

const CANCEL_BUTTON =
  "rounded-lg border border-[#334155] bg-[#0F172A] px-4 py-2 text-sm font-medium text-[#F1F5F9] transition-colors hover:bg-[#1E293B]";

const SAVE_BUTTON =
  "rounded-lg bg-[#6366F1] px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50";

const FORM_PANEL = "rounded-xl border border-[#6366F1]/30 bg-[#0F172A] p-4";

function Card({
  title,
  subtitle,
  plain,
  children,
}: {
  title?: string;
  subtitle?: string;
  plain?: boolean;
  children: React.ReactNode;
}) {
  if (plain) {
    return (
      <div>
        {subtitle && (
          <p className="mb-3 text-xs text-[#64748B]">{subtitle}</p>
        )}
        {children}
      </div>
    );
  }
  return (
    <section className="rounded-2xl border border-[#334155] bg-[#1E293B] p-6 shadow-xl backdrop-blur-sm">
      {title && (
        <div className="mb-1">
          <h2 className="text-lg font-semibold text-[#F1F5F9]">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-[#64748B]">{subtitle}</p>}
        </div>
      )}
      {children}
    </section>
  );
}

function AddRow({ hint, onAdd }: { hint: string; onAdd: () => void }) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <span className="text-sm text-[#94A3B8]">{hint}</span>
      <button type="button" onClick={onAdd} className={ADD_BUTTON}>
        + Agregar
      </button>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-dashed border-[#334155] px-4 py-8 text-center text-sm text-[#64748B]">
      {message}
    </p>
  );
}

function FormFooter({
  status,
  onCancel,
  onSave,
  saveLabel,
}: {
  status: SaveStatus;
  onCancel: () => void;
  onSave: () => void;
  saveLabel: string;
}) {
  return (
    <div className="mt-4 flex items-center justify-between gap-3">
      <SaveState status={status} />
      <div className="flex gap-2">
        <button type="button" onClick={onCancel} className={CANCEL_BUTTON}>
          Cancelar
        </button>
        <button
          type="button"
          onClick={onSave}
          disabled={status === "saving"}
          className={SAVE_BUTTON}
        >
          {status === "saving" ? "Guardando…" : saveLabel}
        </button>
      </div>
    </div>
  );
}

// ─── Datos personales ────────────────────────────────────────────────────────

export interface PersonalValues {
  name: string;
  email: string;
  phone: string;
  address: string;
  about: string;
  porfolio: string;
  linkedin: string;
}

/**
 * Campos de datos personales, compartidos por el editor (autoguardado) y el
 * asistente (guardado al continuar): mismos campos, mismos placeholders.
 */
export function PersonalFields({
  value,
  onChange,
  errors,
  disabled,
}: {
  value: PersonalValues;
  onChange: (key: keyof PersonalValues, value: string) => void;
  errors?: FieldErrors;
  disabled?: boolean;
}) {
  return (
    <>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextField
          label="Nombre"
          value={value.name}
          onChange={(v) => onChange("name", v)}
          placeholder="Ana Pérez"
          required
          disabled={disabled}
          error={errors?.name}
        />
        <TextField
          label="Email"
          value={value.email}
          onChange={(v) => onChange("email", v)}
          type="email"
          placeholder="ana@ejemplo.com"
          required
          disabled={disabled}
          error={errors?.email}
        />
        <TextField
          label="Teléfono"
          value={value.phone}
          onChange={(v) => onChange("phone", v)}
          type="tel"
          placeholder="+54 11 5555-1234"
          disabled={disabled}
          error={errors?.phone}
        />
        <TextField
          label="Dirección"
          value={value.address}
          onChange={(v) => onChange("address", v)}
          placeholder="Ciudad, país"
          disabled={disabled}
          error={errors?.address}
        />
        <TextField
          label="Portfolio"
          value={value.porfolio}
          onChange={(v) => onChange("porfolio", v)}
          placeholder="https://..."
          disabled={disabled}
          error={errors?.porfolio}
        />
        <TextField
          label="LinkedIn"
          value={value.linkedin}
          onChange={(v) => onChange("linkedin", v)}
          placeholder="https://linkedin.com/in/..."
          disabled={disabled}
          error={errors?.linkedin}
        />
      </div>
      <div className="mt-4">
        <TextAreaField
          label="Sobre mí"
          value={value.about}
          onChange={(v) => onChange("about", v)}
          rows={4}
          hint={`${value.about.trim().length}/300 caracteres recomendados`}
          placeholder="Dos o tres frases: quién sos, qué hacés y hacia dónde apuntás."
          disabled={disabled}
          error={errors?.about}
        />
      </div>
    </>
  );
}

// ─── Experiencia ─────────────────────────────────────────────────────────────

const EMPTY_EXPERIENCE: ExperienceData = {
  title: "",
  company: "",
  start_date: "",
  end_date: "",
  description: "",
};

export function ExperienceManager({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
}: ManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<ExperienceData>(EMPTY_EXPERIENCE);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [general, setGeneral] = useState<string | undefined>();
  const deletingRef = useRef(false);

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

  const openCreate = () => {
    setForm(EMPTY_EXPERIENCE);
    setErrors({});
    setEditId(null);
    setGeneral(undefined);
    setStatus("idle");
    setShowForm(true);
  };

  const openEdit = (id: string) => {
    const item = cv.experiences.find((entry) => entry.id === id);
    if (!item) return;
    setForm({
      title: item.title,
      company: item.company,
      start_date: toDateInput(item.start_date),
      end_date: toDateInput(item.end_date),
      description: item.description,
    });
    setErrors({});
    setEditId(item.id);
    setGeneral(undefined);
    setStatus("idle");
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
      setShowForm(false);
      setStatus("idle");
    } catch (e) {
      setStatus("error");
      const message = apiErrorMessage(e, "No se pudo guardar la experiencia");
      setGeneral(message);
      onError?.(message);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteExperience(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar la experiencia");
        setGeneral(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  const experiences = cv.experiences;

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      {showForm ? (
        <div className={FORM_PANEL}>
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
              hint="Verbos de acción y métricas"
              placeholder="Desarrollé APIs en Python con FastAPI; reduje la latencia un 30%."
            />
          </div>
          <FormError message={general} />
          <FormFooter
            status={status}
            onCancel={() => setShowForm(false)}
            onSave={handleSave}
            saveLabel={editId ? "Actualizar" : "Agregar"}
          />
        </div>
      ) : (
        <AddRow
          hint="Puestos, proyectos o freelance: una acción y un resultado concreto"
          onAdd={openCreate}
        />
      )}

      <FormError message={showForm ? undefined : general} />

      {experiences.length === 0 && !showForm ? (
        <EmptyState message="Todavía no tenés experiencia cargada. También podés agregar proyectos personales o freelance." />
      ) : (
        <div className="space-y-3">
          {experiences.map((item) => (
            <ItemCard
              key={item.id}
              title={item.title}
              subtitle={item.company}
              meta={[
                toDateInput(item.start_date),
                toDateInput(item.end_date) || "Actualidad",
              ]
                .filter(Boolean)
                .join(" — ")}
              description={item.description}
              onEdit={() => openEdit(item.id)}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

// ─── Formación ───────────────────────────────────────────────────────────────

const EMPTY_EDUCATION: EducationData = {
  degree: "",
  institution: "",
  start_date: "",
  end_date: "",
};

/**
 * La API no tiene `update` para educación: editar es alta nueva y después
 * baja de la anterior, con el alta primero para que un fallo nunca pierda la
 * entrada original (queda un duplicado visible, que se borra).
 */
export function EducationManager({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
}: ManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<EducationData>(EMPTY_EDUCATION);
  const [originalDescription, setOriginalDescription] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [general, setGeneral] = useState<string | undefined>();
  const deletingRef = useRef(false);

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

  const openCreate = () => {
    setForm(EMPTY_EDUCATION);
    setOriginalDescription("");
    setErrors({});
    setEditId(null);
    setGeneral(undefined);
    setStatus("idle");
    setShowForm(true);
  };

  const openEdit = (id: string) => {
    const item = cv.education.find((entry) => entry.id === id);
    if (!item) return;
    setForm({
      degree: item.degree,
      institution: item.institution,
      start_date: toDateInput(item.start_date),
      end_date: toDateInput(item.end_date),
    });
    setOriginalDescription(item.description);
    setErrors({});
    setEditId(item.id);
    setGeneral(undefined);
    setStatus("idle");
    setShowForm(true);
  };

  const handleSave = async () => {
    const found = validateEducation(form);
    setErrors(found);
    if (hasErrors(found)) return;

    setStatus("saving");
    setGeneral(undefined);
    try {
      // Alta primero, baja después (ver nota arriba).
      await addEducation({
        user_id: userId,
        degree: form.degree.trim(),
        institution: form.institution.trim(),
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
        description: originalDescription || undefined,
      });
      if (editId) {
        try {
          await deleteEducation(editId, userId);
        } catch {
          // Duplicado visible en vez de dato perdido.
        }
      }
      await onChanged();
      setShowForm(false);
      setStatus("idle");
    } catch (e) {
      setStatus("error");
      const message = apiErrorMessage(e, "No se pudo guardar la formación");
      setGeneral(message);
      onError?.(message);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteEducation(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar la formación");
        setGeneral(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  const education = cv.education;

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      {showForm ? (
        <div className={FORM_PANEL}>
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
          <FormError message={general} />
          <FormFooter
            status={status}
            onCancel={() => setShowForm(false)}
            onSave={handleSave}
            saveLabel={editId ? "Actualizar" : "Agregar"}
          />
        </div>
      ) : (
        <AddRow hint="Carreras, tecnicaturas, cursos largos y certificaciones" onAdd={openCreate} />
      )}

      <FormError message={showForm ? undefined : general} />

      {education.length === 0 && !showForm ? (
        <EmptyState message="Todavía no tenés formación cargada. Si estás cursando, dejá la fecha de fin vacía." />
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
              onEdit={() => openEdit(item.id)}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

// ─── Logros ──────────────────────────────────────────────────────────────────

const EMPTY_ACHIEVEMENT: AchievementData = { title: "", description: "" };

export function AchievementManager({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
}: ManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AchievementData>(EMPTY_ACHIEVEMENT);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [general, setGeneral] = useState<string | undefined>();
  const deletingRef = useRef(false);

  const openCreate = () => {
    setForm(EMPTY_ACHIEVEMENT);
    setErrors({});
    setGeneral(undefined);
    setStatus("idle");
    setShowForm(true);
  };

  const handleSave = async () => {
    const found = validateAchievement(form);
    setErrors(found);
    if (hasErrors(found)) return;

    setStatus("saving");
    setGeneral(undefined);
    try {
      await addAchievement({
        user_id: userId,
        title: form.title.trim(),
        description: form.description.trim() || undefined,
      });
      await onChanged();
      setShowForm(false);
      setStatus("idle");
    } catch (e) {
      setStatus("error");
      const message = apiErrorMessage(e, "No se pudo guardar el logro");
      setGeneral(message);
      onError?.(message);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteAchievement(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar el logro");
        setGeneral(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  const achievements = cv.achievements;

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      {showForm ? (
        <div className={FORM_PANEL}>
          <TextField
            label="Logro"
            value={form.title}
            onChange={(value) => {
              setForm((current) => ({ ...current, title: value }));
              setErrors({});
            }}
            error={errors.title}
            placeholder="Primer puesto en el hackathon nacional"
            required
            autoFocus
          />
          <div className="mt-4">
            <TextAreaField
              label="Detalle"
              value={form.description}
              onChange={(value) =>
                setForm((current) => ({ ...current, description: value }))
              }
              rows={2}
              placeholder="40 equipos; proyecto con React y FastAPI."
            />
          </div>
          <FormError message={general} />
          <FormFooter
            status={status}
            onCancel={() => setShowForm(false)}
            onSave={handleSave}
            saveLabel="Agregar logro"
          />
        </div>
      ) : (
        <AddRow hint="Premios, publicaciones, proyectos propios: lo que te distingue" onAdd={openCreate} />
      )}

      <FormError message={showForm ? undefined : general} />

      {achievements.length === 0 && !showForm ? (
        <EmptyState message="Sin logros todavía. ¿Ganaste algo, publicaste algo, construiste algo propio? Eso va acá." />
      ) : (
        <div className="space-y-3">
          {achievements.map((item) => (
            <ItemCard
              key={item.id}
              title={item.title}
              description={item.description}
              onEdit={() => {
                setForm({ title: item.title, description: item.description });
                setErrors({});
                setGeneral(undefined);
                setShowForm(true);
              }}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

// ─── Habilidades (técnicas y blandas) ────────────────────────────────────────

interface SkillPickerProps extends ManagerProps {
  type: "tech" | "soft";
}

export function SkillPicker({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
  type,
}: SkillPickerProps) {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState(SKILL_LEVELS[1]);
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState<SkillCatalogItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const deletingRef = useRef(false);

  const skills = cv.skills.filter((skill) => (skill.type || "tech") === type);

  useEffect(() => {
    if (query.trim().length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        const data = await searchSkillCatalog(query);
        setSuggestions(data.results);
        setShowSuggestions(data.results.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 200);
    return () => window.clearTimeout(timer);
  }, [query]);

  const handleAdd = async (name?: string) => {
    const candidate = (name ?? query).trim();
    const problem = validateSkillName(candidate, type, skills);
    if (problem) {
      setError(problem);
      return;
    }
    setSaving(true);
    setError(undefined);
    try {
      await addSkill({ user_id: userId, name: candidate, level, type });
      await onChanged();
      setQuery("");
      setShowSuggestions(false);
    } catch (e) {
      const message = apiErrorMessage(e, "No se pudo agregar la habilidad");
      setError(message);
      onError?.(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteSkill(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar la habilidad");
        setError(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="relative flex-1">
          <TextField
            label="Habilidad"
            value={query}
            onChange={(value) => {
              setQuery(value);
              if (error) setError(undefined);
            }}
            placeholder={type === "tech" ? "Python, React, SQL…" : "Comunicación, liderazgo…"}
            error={error}
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-[#334155] bg-[#1E293B] shadow-xl">
              {suggestions.slice(0, 6).map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => handleAdd(item.name)}
                    className="block w-full px-3 py-2 text-left text-sm text-[#CBD5E1] transition-colors hover:bg-[#6366F1]/15"
                  >
                    {item.name}
                    <span className="ml-2 text-xs text-[#64748B]">{item.category}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="sm:w-44">
          <SelectField
            label="Nivel"
            value={level}
            onChange={setLevel}
            options={SKILL_LEVELS}
          />
        </div>
        <div className="flex items-end sm:pb-0.5">
          <button
            type="button"
            onClick={() => handleAdd()}
            disabled={saving || !query.trim()}
            className={`${ADD_BUTTON} h-[42px]`}
          >
            {saving ? "…" : "Agregar"}
          </button>
        </div>
      </div>

      <div className="mt-4">
        {skills.length === 0 ? (
          <EmptyState
            message={
              type === "tech"
                ? "Sin habilidades técnicas todavía: empezá por el lenguaje que más usás."
                : "Sin habilidades blandas todavía: cómo trabajás también se valora."
            }
          />
        ) : (
          <ChipList
            items={skills.map((skill) => ({
              id: skill.id,
              label: skill.name,
              meta: skill.level,
            }))}
            onDelete={handleDelete}
            deleteLabel={(label) => `Quitar ${label}`}
          />
        )}
      </div>
    </Card>
  );
}

// ─── Programas ───────────────────────────────────────────────────────────────

export function ProgramPicker({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
}: ManagerProps) {
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);
  const deletingRef = useRef(false);

  const programs = cv.programs;

  const handleAdd = async () => {
    const candidate = query.trim();
    if (!candidate) {
      setError("Ingresá el nombre del programa");
      return;
    }
    if (programs.some((program) => program.name.toLowerCase() === candidate.toLowerCase())) {
      setError("Ya está en tu lista");
      return;
    }
    setSaving(true);
    setError(undefined);
    try {
      await addProgram({ user_id: userId, name: candidate });
      await onChanged();
      setQuery("");
    } catch (e) {
      const message = apiErrorMessage(e, "No se pudo agregar el programa");
      setError(message);
      onError?.(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteProgram(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar el programa");
        setError(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="flex-1">
          <TextField
            label="Tecnología o programa"
            value={query}
            onChange={(value) => {
              setQuery(value);
              if (error) setError(undefined);
            }}
            placeholder="Docker, Kubernetes, Scrum…"
            error={error}
          />
        </div>
        <div className="flex items-end sm:pb-0.5">
          <button
            type="button"
            onClick={handleAdd}
            disabled={saving || !query.trim()}
            className={`${ADD_BUTTON} h-[42px]`}
          >
            {saving ? "…" : "Agregar"}
          </button>
        </div>
      </div>

      <div className="mt-4">
        {programs.length === 0 ? (
          <EmptyState message="Sin programas cargados: herramientas, cursos y certificaciones van acá." />
        ) : (
          <ChipList
            items={programs.map((program) => ({
              id: program.id,
              label: program.name,
            }))}
            onDelete={handleDelete}
            deleteLabel={(label) => `Quitar ${label}`}
          />
        )}
      </div>
    </Card>
  );
}

// ─── Idiomas ─────────────────────────────────────────────────────────────────

const EMPTY_LANGUAGE: LanguageData = { name: "", level: LANGUAGE_LEVELS[1] };

export function LanguagePicker({
  cv,
  userId,
  onChanged,
  onError,
  title,
  subtitle,
  plain,
}: ManagerProps) {
  const [form, setForm] = useState<LanguageData>(EMPTY_LANGUAGE);
  const [error, setError] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);
  const deletingRef = useRef(false);

  const languages = cv.languages;

  const handleAdd = async () => {
    const found = validateLanguage(form);
    const first = Object.values(found)[0];
    if (first) {
      setError(first);
      return;
    }
    if (
      languages.some(
        (language) => language.name.trim().toLowerCase() === form.name.trim().toLowerCase(),
      )
    ) {
      setError("Ya está en tu lista");
      return;
    }
    setSaving(true);
    setError(undefined);
    try {
      await addLanguage({
        user_id: userId,
        name: form.name.trim(),
        level: form.level,
      });
      await onChanged();
      setForm(EMPTY_LANGUAGE);
    } catch (e) {
      const message = apiErrorMessage(e, "No se pudo guardar el idioma");
      setError(message);
      onError?.(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (deletingRef.current) return;
    deletingRef.current = true;
    try {
      await deleteLanguage(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        const message = apiErrorMessage(e, "No se pudo eliminar el idioma");
        setError(message);
        onError?.(message);
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <Card title={title} subtitle={subtitle} plain={plain}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="flex-1">
          <TextField
            label="Idioma"
            value={form.name}
            onChange={(value) => {
              setForm((current) => ({ ...current, name: value }));
              if (error) setError(undefined);
            }}
            placeholder="Inglés"
            error={error}
          />
        </div>
        <div className="sm:w-52">
          <SelectField
            label="Nivel"
            value={form.level}
            onChange={(value) => setForm((current) => ({ ...current, level: value }))}
            options={LANGUAGE_LEVELS}
          />
        </div>
        <div className="flex items-end sm:pb-0.5">
          <button
            type="button"
            onClick={handleAdd}
            disabled={saving || !form.name.trim()}
            className={`${ADD_BUTTON} h-[42px]`}
          >
            {saving ? "…" : "Agregar"}
          </button>
        </div>
      </div>

      <div className="mt-4">
        {languages.length === 0 ? (
          <EmptyState message="Sin idiomas cargados. Si tenés certificación (C1, B1), sumala." />
        ) : (
          <ChipList
            items={languages.map((language) => ({
              id: language.id,
              label: language.name,
              meta: language.level,
            }))}
            onDelete={handleDelete}
            deleteLabel={(label) => `Quitar ${label}`}
          />
        )}
      </div>
    </Card>
  );
}
