"use client";

import { useRef, useState } from "react";

import {
  addAchievement,
  addLanguage,
  apiErrorMessage,
  deleteAchievement,
  deleteLanguage,
  isNotFoundError,
} from "@/app/lib/api";
import { LANGUAGE_LEVELS } from "@/app/lib/cv-constants";
import {
  hasErrors,
  validateAchievement,
  validateLanguage,
  type AchievementData,
  type FieldErrors,
  type LanguageData,
} from "@/app/lib/cv-validation";
import {
  ChipList,
  ItemCard,
  SaveState,
  SelectField,
  StepActions,
  StepError,
  TextAreaField,
  TextField,
  type StepProps,
} from "../components/form-ui";

const EMPTY_ACHIEVEMENT: AchievementData = { title: "", description: "" };
const EMPTY_LANGUAGE: LanguageData = { name: "", level: LANGUAGE_LEVELS[1] };

/**
 * Paso 5: lo que hace memorable al CV. Ambos bloques son opcionales: el
 * usuario puede avanzar sin agregar nada.
 */
export function ExtrasStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const [achievement, setAchievement] = useState<AchievementData>(EMPTY_ACHIEVEMENT);
  const [achievementErrors, setAchievementErrors] = useState<FieldErrors>({});
  const [achievementGeneral, setAchievementGeneral] = useState<string | undefined>();
  const [achievementSaving, setAchievementSaving] = useState(false);
  const achievementDeleting = useRef(false);

  const [language, setLanguage] = useState<LanguageData>(EMPTY_LANGUAGE);
  const [languageErrors, setLanguageErrors] = useState<FieldErrors>({});
  const [languageGeneral, setLanguageGeneral] = useState<string | undefined>();
  const [languageSaving, setLanguageSaving] = useState(false);
  const languageDeleting = useRef(false);

  const handleAchievementSave = async () => {
    const found = validateAchievement(achievement);
    setAchievementErrors(found);
    if (hasErrors(found)) return;

    setAchievementSaving(true);
    setAchievementGeneral(undefined);
    try {
      await addAchievement({
        user_id: userId,
        title: achievement.title.trim(),
        description: achievement.description.trim() || undefined,
      });
      await onChanged();
      setAchievement(EMPTY_ACHIEVEMENT);
    } catch (e) {
      setAchievementGeneral(
        apiErrorMessage(e, "No se pudo guardar el logro"),
      );
    } finally {
      setAchievementSaving(false);
    }
  };

  const handleAchievementDelete = async (id: string) => {
    if (achievementDeleting.current) return;
    achievementDeleting.current = true;
    try {
      await deleteAchievement(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        setAchievementGeneral(
          apiErrorMessage(e, "No se pudo eliminar el logro"),
        );
      }
    } finally {
      achievementDeleting.current = false;
      await onChanged();
    }
  };

  const handleLanguageSave = async () => {
    const found = validateLanguage(language);
    setLanguageErrors(found);
    if (hasErrors(found)) return;

    setLanguageSaving(true);
    setLanguageGeneral(undefined);
    try {
      await addLanguage({
        user_id: userId,
        name: language.name.trim(),
        level: language.level,
      });
      await onChanged();
      setLanguage(EMPTY_LANGUAGE);
    } catch (e) {
      setLanguageGeneral(
        apiErrorMessage(e, "No se pudo guardar el idioma"),
      );
    } finally {
      setLanguageSaving(false);
    }
  };

  const handleLanguageDelete = async (id: string) => {
    if (languageDeleting.current) return;
    languageDeleting.current = true;
    try {
      await deleteLanguage(id, userId);
    } catch (e) {
      if (!isNotFoundError(e)) {
        setLanguageGeneral(
          apiErrorMessage(e, "No se pudo eliminar el idioma"),
        );
      }
    } finally {
      languageDeleting.current = false;
      await onChanged();
    }
  };

  return (
    <div className="space-y-6">
      {/* ── Logros ─────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
        <h3 className="font-medium text-[#F8FAFC]">Logros destacados</h3>
        <p className="mt-0.5 text-xs text-[#64748B]">
          Premios, publicaciones, proyectos propios: lo que te distingue.
        </p>

        <div className="mt-3 space-y-3">
          <TextField
            label="Logro"
            value={achievement.title}
            onChange={(value) => {
              setAchievement((current) => ({ ...current, title: value }));
              setAchievementErrors({});
            }}
            error={achievementErrors.title}
            placeholder="Primer puesto en el hackathon Nacional"
          />
          <TextAreaField
            label="Detalle"
            value={achievement.description}
            onChange={(value) =>
              setAchievement((current) => ({ ...current, description: value }))
            }
            rows={2}
            placeholder="40 equipos, proyecto con React y FastAPI."
          />
          <StepError message={achievementGeneral} />
          <div className="flex items-center justify-between gap-3">
            <SaveState status={achievementSaving ? "saving" : "idle"} />
            <button
              type="button"
              onClick={handleAchievementSave}
              disabled={achievementSaving || !achievement.title.trim()}
              className="rounded-lg bg-[#6366F1] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
            >
              {achievementSaving ? "Guardando…" : "Agregar logro"}
            </button>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {cv.achievements.map((item) => (
            <ItemCard
              key={item.id}
              title={item.title}
              description={item.description}
              onDelete={() => handleAchievementDelete(item.id)}
            />
          ))}
        </div>
      </div>

      {/* ── Idiomas ────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-[#334155] bg-[#0F172A] p-4">
        <h3 className="font-medium text-[#F8FAFC]">Idiomas</h3>
        <p className="mt-0.5 text-xs text-[#64748B]">
          Nivel con estándar europeo si lo tenés (C1, B1, A2).
        </p>

        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="flex-1">
            <TextField
              label="Idioma"
              value={language.name}
              onChange={(value) => {
                setLanguage((current) => ({ ...current, name: value }));
                setLanguageErrors({});
              }}
              error={languageErrors.name}
              placeholder="Inglés"
            />
          </div>
          <div className="sm:w-52">
            <SelectField
              label="Nivel"
              value={language.level}
              onChange={(value) =>
                setLanguage((current) => ({ ...current, level: value }))
              }
              options={LANGUAGE_LEVELS}
            />
          </div>
          <div className="flex items-end gap-2 sm:pb-0.5">
            <button
              type="button"
              onClick={handleLanguageSave}
              disabled={languageSaving || !language.name.trim()}
              className="h-[42px] rounded-lg bg-[#6366F1] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#6366F1]/90 disabled:opacity-50"
            >
              {languageSaving ? "…" : "Agregar"}
            </button>
          </div>
        </div>

        <StepError message={languageGeneral} />

        <div className="mt-3">
          <ChipList
            items={cv.languages.map((item) => ({
              id: item.id,
              label: item.name,
              meta: item.level,
            }))}
            onDelete={handleLanguageDelete}
            deleteLabel={(label) => `Quitar ${label}`}
          />
        </div>
      </div>

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Nada por agregar acá"
      />
    </div>
  );
}
