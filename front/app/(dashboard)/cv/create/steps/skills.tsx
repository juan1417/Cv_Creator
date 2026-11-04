"use client";

import { useEffect, useRef, useState } from "react";

import {
  addProgram,
  addSkill,
  apiErrorMessage,
  deleteProgram,
  deleteSkill,
  isNotFoundError,
  searchSkillCatalog,
  type SkillCatalogItem,
} from "@/app/lib/api";
import { SKILL_LEVELS } from "@/app/lib/cv-constants";
import { validateSkillName } from "@/app/lib/cv-validation";
import {
  ChipList,
  SelectField,
  StepActions,
  TextField,
  type StepProps,
} from "../components/form-ui";

/**
 * Paso 4: habilidades. Tres bloques —técnicas, blandas y programas— porque
 * alimentan tres secciones distintas del CV final (HABILIDADES y TECNOLOGÍAS).
 * Las técnicas y las blandas autocompletan con el catálogo existente.
 */

function SkillBlock({
  userId,
  type,
  title,
  subtitle,
  placeholder,
  skills,
  onChanged,
}: {
  userId: string;
  type: "tech" | "soft";
  title: string;
  subtitle: string;
  placeholder: string;
  skills: { id: string; name: string; level: string; type?: string }[];
  onChanged: () => void;
}) {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState(SKILL_LEVELS[1]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState<SkillCatalogItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const deletingRef = useRef(false);

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
    setError(null);
    try {
      await addSkill({ user_id: userId, name: candidate, level, type });
      await onChanged();
      setQuery("");
      setShowSuggestions(false);
    } catch (e) {
      setError(apiErrorMessage(e, "No se pudo agregar la habilidad"));
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
        setError(apiErrorMessage(e, "No se pudo eliminar la habilidad"));
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
      <h3 className="font-medium text-[#F8FAFC]">{title}</h3>
      <p className="mt-0.5 text-xs text-[#64748B]">{subtitle}</p>

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="relative flex-1">
          <TextField
            label="Habilidad"
            value={query}
            onChange={(value) => {
              setQuery(value);
              if (error) setError(null);
            }}
            placeholder={placeholder}
            error={error ?? undefined}
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

        <div className="flex items-end gap-2 sm:pb-0.5">
          <button
            type="button"
            onClick={() => handleAdd()}
            disabled={saving || !query.trim()}
            className="h-[42px] rounded-lg bg-[#6366F1] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
          >
            {saving ? "…" : "Agregar"}
          </button>
        </div>
      </div>

      <div className="mt-3">
        <ChipList
          items={skills.map((skill) => ({
            id: skill.id,
            label: skill.name,
            meta: skill.level,
          }))}
          onDelete={handleDelete}
          deleteLabel={(label) => `Quitar ${label}`}
        />
      </div>
    </div>
  );
}

function ProgramBlock({
  userId,
  programs,
  onChanged,
}: {
  userId: string;
  programs: { id: string; name: string }[];
  onChanged: () => void;
}) {
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const deletingRef = useRef(false);

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
    setError(null);
    try {
      await addProgram({ user_id: userId, name: candidate });
      await onChanged();
      setQuery("");
    } catch (e) {
      setError(apiErrorMessage(e, "No se pudo agregar el programa"));
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
        setError(apiErrorMessage(e, "No se pudo eliminar el programa"));
      }
    } finally {
      deletingRef.current = false;
      await onChanged();
    }
  };

  return (
    <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
      <h3 className="font-medium text-[#F8FAFC]">Tecnologías y programas</h3>
      <p className="mt-0.5 text-xs text-[#64748B]">
        Herramientas, cursos y certificaciones que aparecen en la sección TECNOLOGÍAS.
      </p>

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="flex-1">
          <TextField
            label="Programa"
            value={query}
            onChange={(value) => {
              setQuery(value);
              if (error) setError(null);
            }}
            placeholder="Docker, Kubernetes, Scrum…"
            error={error ?? undefined}
          />
        </div>
        <div className="flex items-end gap-2 sm:pb-0.5">
          <button
            type="button"
            onClick={handleAdd}
            disabled={saving || !query.trim()}
            className="h-[42px] rounded-lg bg-[#6366F1] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
          >
            {saving ? "…" : "Agregar"}
          </button>
        </div>
      </div>

      <div className="mt-3">
        <ChipList
          items={programs.map((program) => ({ id: program.id, label: program.name }))}
          onDelete={handleDelete}
          deleteLabel={(label) => `Quitar ${label}`}
        />
      </div>
    </div>
  );
}

export function SkillsStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const techSkills = cv.skills.filter((skill) => (skill.type || "tech") === "tech");
  const softSkills = cv.skills.filter((skill) => skill.type === "soft");

  return (
    <div className="space-y-4">
      <p className="text-sm text-[#94A3B8]">
        Las habilidades técnicas son las que un filtro ATS más busca. Si todavía
        no tenés ninguna, podés avanzar.
      </p>

      <SkillBlock
        userId={userId}
        type="tech"
        title="Habilidades técnicas"
        subtitle="Lenguajes, frameworks, bases de datos y herramientas"
        placeholder="Python, React, SQL…"
        skills={techSkills}
        onChanged={onChanged}
      />

      <SkillBlock
        userId={userId}
        type="soft"
        title="Habilidades blandas"
        subtitle="Cómo trabajás: comunicación, liderazgo, organización"
        placeholder="Comunicación, liderazgo…"
        skills={softSkills}
        onChanged={onChanged}
      />

      <ProgramBlock userId={userId} programs={cv.programs} onChanged={onChanged} />

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Todavía no tengo habilidades que agregar"
      />
    </div>
  );
}
