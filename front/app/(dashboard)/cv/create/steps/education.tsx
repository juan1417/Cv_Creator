"use client";

import { EducationManager } from "@/app/components/cv-forms";
import { StepActions, type StepProps } from "@/app/components/cv-form-ui";

/**
 * Paso 3: formación. El formulario vive en `EducationManager`, compartido con
 * el editor.
 */
export function EducationStep({ cv, userId, onChanged, onAdvance }: StepProps) {
  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        Carreras, tecnicaturas, cursos largos y certificaciones importantes.
      </p>

      <EducationManager cv={cv} userId={userId} onChanged={onChanged} plain />

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Todavía no tengo formación que agregar"
      />
    </div>
  );
}
