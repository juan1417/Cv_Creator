"use client";

import { ExperienceManager } from "@/app/components/cv-forms";
import { StepActions, type StepProps } from "@/app/components/cv-form-ui";

/**
 * Paso 2: experiencia. El formulario vive en `ExperienceManager`, compartido
 * con el editor, así que alta, edición y baja se comportan igual en los dos
 * caminos.
 */
export function ExperienceStep({ cv, userId, onChanged, onAdvance }: StepProps) {
  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        La experiencia es lo que más pesa en un CV. Si todavía no tenés, podés
        avanzar: después la cargás cuando la tengas.
      </p>

      <ExperienceManager cv={cv} userId={userId} onChanged={onChanged} plain />

      <StepActions
        onNext={onAdvance}
        onSkip={onAdvance}
        skipLabel="Todavía no tengo experiencia"
      />
    </div>
  );
}
