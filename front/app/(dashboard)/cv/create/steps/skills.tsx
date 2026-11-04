"use client";

import { ProgramPicker, SkillPicker } from "@/app/components/cv-forms";
import { StepActions, type StepProps } from "@/app/components/cv-form-ui";

/**
 * Paso 4: habilidades. Los tres bloques (técnicas, blandas y programas) son
 * los mismos componentes que usa el editor.
 */
export function SkillsStep({ cv, userId, onChanged, onAdvance }: StepProps) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-[#94A3B8]">
        Las habilidades técnicas son las que un filtro ATS más busca. Si todavía
        no tenés ninguna, podés avanzar.
      </p>

      <SkillPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        type="tech"
        subtitle="Lenguajes, frameworks, bases de datos y herramientas"
        plain
      />
      <SkillPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        type="soft"
        subtitle="Cómo trabajás: comunicación, liderazgo, organización"
        plain
      />
      <ProgramPicker
        cv={cv}
        userId={userId}
        onChanged={onChanged}
        subtitle="Herramientas, cursos y certificaciones (sección TECNOLOGÍAS)"
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
