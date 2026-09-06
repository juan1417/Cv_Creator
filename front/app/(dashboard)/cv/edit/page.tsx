"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/app/lib/auth";
import {
  getFullCV,
  updateCV,
  addExperience,
  updateExperience,
  deleteExperience,
  addSkill,
  deleteSkill,
  addEducation,
  deleteEducation,
} from "@/app/lib/api";
import type {
  FullCV,
  ExperienceResponse,
  SkillResponse,
  EducationResponse,
} from "@/app/lib/types";

// ─── Loading Spinner ─────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
    </div>
  );
}

// ─── CV Editor Page ──────────────────────────────────────────────────────────

export default function CVEditPage() {
  const { user } = useAuth();
  const [cv, setCv] = useState<FullCV | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Personal info form
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [about, setAbout] = useState("");
  const [porfolio, setPorfolio] = useState("");
  const [linkedin, setLinkedin] = useState("");

  const fetchCV = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getFullCV(user.id);
      setCv(data);
      setName(data.cv.name);
      setEmail(data.cv.email);
      setPhone(data.cv.phone);
      setAddress(data.cv.address);
      setAbout(data.cv.about);
      setPorfolio(data.cv.porfolio);
      setLinkedin(data.cv.linkedin ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar el CV");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchCV();
  }, [fetchCV]);

  const handleSavePersonal = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const updated = await updateCV(user.id, {
        name,
        email,
        phone,
        address,
        about,
        porfolio,
        linkedin,
      });
      setCv((prev) => (prev ? { ...prev, cv: updated } : prev));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Spinner />;

  if (error && !cv) {
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
          Editar CV
        </h1>
        <a
          href="/cv/preview"
          target="_blank"
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          Vista Previa
        </a>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 font-medium underline"
          >
            Cerrar
          </button>
        </div>
      )}

      {/* ── Personal Info ─────────────────────────────────────────────── */}
      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
          Información Personal
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Nombre" value={name} onChange={setName} />
          <Field label="Email" value={email} onChange={setEmail} type="email" />
          <Field label="Teléfono" value={phone} onChange={setPhone} />
          <Field label="Dirección" value={address} onChange={setAddress} />
          <Field
            label="Portfolio"
            value={porfolio}
            onChange={setPorfolio}
            placeholder="https://..."
          />
          <Field
            label="LinkedIn"
            value={linkedin}
            onChange={setLinkedin}
            placeholder="https://linkedin.com/in/..."
          />
        </div>
        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Sobre mí
          </label>
          <textarea
            value={about}
            onChange={(e) => setAbout(e.target.value)}
            rows={4}
            className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div className="mt-4 flex justify-end">
          <button
            onClick={handleSavePersonal}
            disabled={saving}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      </section>

      {/* ── Experiences ───────────────────────────────────────────────── */}
      <ExperiencesSection
        experiences={cv?.experiences ?? []}
        userId={user!.id}
        onChanged={fetchCV}
      />

      {/* ── Skills ────────────────────────────────────────────────────── */}
      <SkillsSection
        skills={cv?.skills ?? []}
        userId={user!.id}
        onChanged={fetchCV}
      />

      {/* ── Education ─────────────────────────────────────────────────── */}
      <EducationSection
        education={cv?.education ?? []}
        userId={user!.id}
        onChanged={fetchCV}
      />
    </div>
  );
}

// ─── Reusable Field ──────────────────────────────────────────────────────────

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
      />
    </div>
  );
}

// ─── Experiences Section ─────────────────────────────────────────────────────

function ExperiencesSection({
  experiences,
  userId,
  onChanged,
}: {
  experiences: ExperienceResponse[];
  userId: string;
  onChanged: () => void;
}) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setTitle("");
    setCompany("");
    setStartDate("");
    setEndDate("");
    setDescription("");
    setEditId(null);
    setShowForm(false);
  };

  const openEdit = (exp: ExperienceResponse) => {
    setTitle(exp.title);
    setCompany(exp.company);
    setStartDate(exp.start_date ?? "");
    setEndDate(exp.end_date ?? "");
    setDescription(exp.description);
    setEditId(exp.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editId) {
        await updateExperience(editId, {
          user_id: userId,
          title,
          company,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          description,
        });
      } else {
        await addExperience({
          user_id: userId,
          title,
          company,
          start_date: startDate || undefined,
          end_date: endDate || undefined,
          description,
        });
      }
      resetForm();
      onChanged();
    } catch {
      // error handled by parent refresh
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteExperience(id, userId);
    onChanged();
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">
          Experiencia
        </h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + Agregar experiencia
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Título" value={title} onChange={setTitle} />
            <Field label="Empresa" value={company} onChange={setCompany} />
            <Field
              label="Fecha inicio"
              value={startDate}
              onChange={setStartDate}
              type="date"
            />
            <Field
              label="Fecha fin"
              value={endDate}
              onChange={setEndDate}
              type="date"
            />
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Descripción
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
          <div className="mt-4 flex gap-2 justify-end">
            <button
              onClick={resetForm}
              className="rounded-lg bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-white dark:hover:bg-zinc-600"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Guardando..." : editId ? "Actualizar" : "Agregar"}
            </button>
          </div>
        </div>
      )}

      {experiences.length === 0 && !showForm && (
        <p className="py-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
          No hay experiencias registradas.
        </p>
      )}

      <div className="space-y-3">
        {experiences.map((exp) => (
          <div
            key={exp.id}
            className="flex items-start justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800"
          >
            <div className="min-w-0 flex-1">
              <p className="font-medium text-zinc-900 dark:text-white">
                {exp.title}
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {exp.company}
              </p>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
                {exp.start_date ?? "—"} — {exp.end_date ?? "Presente"}
              </p>
              {exp.description && (
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {exp.description}
                </p>
              )}
            </div>
            <div className="ml-4 flex gap-2">
              <button
                onClick={() => openEdit(exp)}
                className="rounded px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
              >
                Editar
              </button>
              <button
                onClick={() => handleDelete(exp.id)}
                className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── Skills Section ──────────────────────────────────────────────────────────

const LEVELS = ["Básico", "Intermedio", "Avanzado", "Experto"];

function SkillsSection({
  skills,
  userId,
  onChanged,
}: {
  skills: SkillResponse[];
  userId: string;
  onChanged: () => void;
}) {
  const [name, setName] = useState("");
  const [level, setLevel] = useState("Intermedio");
  const [saving, setSaving] = useState(false);

  const handleAdd = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      await addSkill({ user_id: userId, name: name.trim(), level });
      setName("");
      setLevel("Intermedio");
      onChanged();
    } catch {
      // handled by parent
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteSkill(id, userId);
    onChanged();
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
        Habilidades
      </h2>

      <div className="mb-4 flex flex-wrap items-end gap-2">
        <div className="flex-1 min-w-[200px]">
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Nueva skill
          </label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="Ej: React, Python..."
            className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Nivel
          </label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          >
            {LEVELS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={handleAdd}
          disabled={saving || !name.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Agregando..." : "Agregar"}
        </button>
      </div>

      {skills.length === 0 ? (
        <p className="py-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
          No hay habilidades registradas.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <span
              key={skill.id}
              className="inline-flex items-center gap-2 rounded-full border border-zinc-200 bg-zinc-100 px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            >
              <span className="text-zinc-900 dark:text-white">{skill.name}</span>
              <span className="text-xs text-zinc-500 dark:text-zinc-400">
                {skill.level}
              </span>
              <button
                onClick={() => handleDelete(skill.id)}
                className="ml-1 text-zinc-400 hover:text-red-600 dark:text-zinc-500 dark:hover:text-red-400"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </section>
  );
}

// ─── Education Section ───────────────────────────────────────────────────────

function EducationSection({
  education,
  userId,
  onChanged,
}: {
  education: EducationResponse[];
  userId: string;
  onChanged: () => void;
}) {
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [degree, setDegree] = useState("");
  const [institution, setInstitution] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  const resetForm = () => {
    setDegree("");
    setInstitution("");
    setStartDate("");
    setEndDate("");
    setDescription("");
    setEditId(null);
    setShowForm(false);
  };

  const openEdit = (edu: EducationResponse) => {
    setDegree(edu.degree);
    setInstitution(edu.institution);
    setStartDate(edu.start_date ?? "");
    setEndDate(edu.end_date ?? "");
    setDescription(edu.description);
    setEditId(edu.id);
    setShowForm(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editId) {
        // There's no updateEducation in the API, we delete + re-add
        await deleteEducation(editId, userId);
      }
      await addEducation({
        user_id: userId,
        degree,
        institution,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        description,
      });
      resetForm();
      onChanged();
    } catch {
      // handled by parent
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteEducation(id, userId);
    onChanged();
  };

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">
          Formación
        </h2>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + Agregar formación
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Título" value={degree} onChange={setDegree} />
            <Field
              label="Institución"
              value={institution}
              onChange={setInstitution}
            />
            <Field
              label="Fecha inicio"
              value={startDate}
              onChange={setStartDate}
              type="date"
            />
            <Field
              label="Fecha fin"
              value={endDate}
              onChange={setEndDate}
              type="date"
            />
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-zinc-700 dark:text-zinc-300">
              Descripción
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
          <div className="mt-4 flex gap-2 justify-end">
            <button
              onClick={resetForm}
              className="rounded-lg bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-white dark:hover:bg-zinc-600"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Guardando..." : editId ? "Actualizar" : "Agregar"}
            </button>
          </div>
        </div>
      )}

      {education.length === 0 && !showForm && (
        <p className="py-8 text-center text-sm text-zinc-500 dark:text-zinc-400">
          No hay formación registrada.
        </p>
      )}

      <div className="space-y-3">
        {education.map((edu) => (
          <div
            key={edu.id}
            className="flex items-start justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800"
          >
            <div className="min-w-0 flex-1">
              <p className="font-medium text-zinc-900 dark:text-white">
                {edu.degree}
              </p>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {edu.institution}
              </p>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-500">
                {edu.start_date ?? "—"} — {edu.end_date ?? "Presente"}
              </p>
              {edu.description && (
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {edu.description}
                </p>
              )}
            </div>
            <div className="ml-4 flex gap-2">
              <button
                onClick={() => openEdit(edu)}
                className="rounded px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
              >
                Editar
              </button>
              <button
                onClick={() => handleDelete(edu.id)}
                className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
