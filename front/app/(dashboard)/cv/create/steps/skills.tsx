"use client";

import { ProgramPicker, SkillPicker } from "@/app/components/cv-forms";
import { StepActions, type StepProps } from "@/app/components/cv-form-ui";

/**
 * Paso 4: habilidades. Los tres bloques (técnicas, blandas y programas) son
 * los mismos componentes que usa el editor.
 */
export function SkillsStep({ cv, userId, onChanged, onLocal, onAdvance }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-[#94A3B8]">
        Todo esto va a una sola sección del CV, HABILIDADES, con una línea por
        categoría. Las técnicas son las que más pesan en un filtro ATS.
      </p>

      <SkillPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        onLocal={onLocal}
        type="tech"
        subtitle="Habilidades técnicas: cada una cae en su categoría dentro de HABILIDADES"
        plain
      />
      <SkillPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        onLocal={onLocal}
        type="soft"
        subtitle="Habilidades blandas: aparecen en su propia línea de HABILIDADES"
        plain
      />
      <ProgramPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        onLocal={onLocal}
        subtitle="Cursos, certificaciones y metodologías: entran en «Otros conocimientos»"
        plain
      />

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Todavía no tengo habilidades que agregar"
      />
    </div>
  );
}
