"use client";

import { useState } from "react";

import { PersonalFields, type PersonalValues } from "@/app/components/cv-forms";
import {
  FormError,
  SaveState,
  StepActions,
  type StepProps,
} from "@/app/components/cv-form-ui";
import { updateCV } from "@/app/lib/api";
import {
  hasErrors,
  validatePersonal,
  type FieldErrors,
} from "@/app/lib/cv-validation";

/**
 * Paso 1: los datos que un ATS y un reclutador necesitan para identificarte y
 * contactarte. Único paso con validación bloqueante (S4).
 */
export function PersonalStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const [form, setForm] = useState<PersonalValues>({
    name: cv.cv.name,
    email: cv.cv.email,
    phone: cv.cv.phone,
    address: cv.cv.address,
    about: cv.cv.about,
    porfolio: cv.cv.porfolio,
    linkedin: cv.cv.linkedin ?? "",
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [general, setGeneral] = useState<string | undefined>();

  const handleChange = (key: keyof PersonalValues, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const handleNext = async () => {
    const found = validatePersonal(form);
    setErrors(found);
    if (hasErrors(found)) return;

    setStatus("saving");
    setGeneral(undefined);
    try {
      await updateCV(userId, form);
      await onChanged();
      setStatus("saved");
      window.setTimeout(onAdvance, 350);
    } catch (e) {
      setStatus("error");
      setGeneral(
        e instanceof Error ? e.message : "No se pudieron guardar tus datos",
      );
    }
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        Empezá por lo indispensable. El resto podés completarlo en los pasos
        siguientes o después desde el editor.
      </p>

      <PersonalFields
        value={form}
        onChange={handleChange}
        errors={errors}
        disabled={status === "saving"}
      />

      <FormError message={general} />

      <div className="flex items-center justify-end">
        <SaveState status={status} />
      </div>

      <StepActions onNext={handleNext} nextBusy={status === "saving"} />
    </div>
  );
}
