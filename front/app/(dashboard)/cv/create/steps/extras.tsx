"use client";

import { AchievementManager, LanguagePicker } from "@/app/components/cv-forms";
import { StepActions, type StepProps } from "@/app/components/cv-form-ui";

/**
 * Paso 5: logros e idiomas, ambos opcionales. Los formularios son los mismos
 * que usa el editor.
 */
export function ExtrasStep({ cv, userId, onChanged, onLocal, onAdvance }: StepProps) {
  return (
    <div className="space-y-6">
      <p className="text-sm text-[#94A3B8]">
        Lo que hace memorable a un perfil. Si no tenés nada por agregar acá,
        seguí directo.
      </p>

      <AchievementManager
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        onLocal={onLocal}
        subtitle="Premios, publicaciones y proyectos propios"
        plain
      />
      <LanguagePicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        onLocal={onLocal}
        subtitle="Nivel con estándar europeo si lo tenés (C1, B1, A2)"
        plain
      />

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Nada por agregar acá"
      />
    </div>
  );
}
