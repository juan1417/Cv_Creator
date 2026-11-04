"use client";

import { useState } from "react";

import { updateCV } from "@/app/lib/api";
import {
  hasErrors,
  validatePersonal,
  type FieldErrors,
  type PersonalData,
} from "@/app/lib/cv-validation";
import {
  SaveState,
  StepActions,
  StepError,
  TextAreaField,
  TextField,
  type StepProps,
} from "../components/form-ui";

const EMAIL_HINT = "Lo usan los reclutadores para contactarte";

/**
 * Paso 1: los datos que un ATS y un reclutador necesitan para identificarte
 * y contactarte. Único paso con validación bloqueante (S4).
 */
export function PersonalStep({ userId, cv, onChanged, onAdvance }: StepProps) {
  const [form, setForm] = useState<PersonalData>({
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

  const setField =
    (key: keyof PersonalData) =>
    (value: string) => {
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

  const aboutLength = form.about.trim().length;

  return (
    <div className="space-y-5">
      <p className="text-sm text-[#94A3B8]">
        Empezá por lo indispensable. El resto podés completarlo en los pasos
        siguientes o después desde el editor.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextField
          label="Nombre y apellido"
          value={form.name}
          onChange={setField("name")}
          error={errors.name}
          placeholder="Ana Pérez"
          required
          autoFocus
        />
        <TextField
          label="Email"
          value={form.email}
          onChange={setField("email")}
          type="email"
          error={errors.email}
          hint={EMAIL_HINT}
          placeholder="ana@ejemplo.com"
          required
        />
        <TextField
          label="Teléfono"
          value={form.phone}
          onChange={setField("phone")}
          type="tel"
          placeholder="+54 11 5555-1234"
          hint="Opcional, pero acelera el contacto"
        />
        <TextField
          label="Dirección"
          value={form.address}
          onChange={setField("address")}
          placeholder="Ciudad, país"
        />
        <TextField
          label="LinkedIn"
          value={form.linkedin}
          onChange={setField("linkedin")}
          type="url"
          placeholder="https://linkedin.com/in/tu-perfil"
        />
        <TextField
          label="Portafolio"
          value={form.porfolio}
          onChange={setField("porfolio")}
          type="url"
          placeholder="https://github.com/tu-usuario"
        />
      </div>

      <TextAreaField
        label="Sobre mí"
        value={form.about}
        onChange={setField("about")}
        rows={4}
        hint={`${aboutLength}/300 caracteres recomendados`}
        placeholder="Dos o tres frases: quién sos, qué hacés y hacia dónde apuntás."
      />

      <StepError message={general} />

      <div className="flex items-center justify-end">
        <SaveState status={status} />
      </div>

      <StepActions onNext={handleNext} nextBusy={status === "saving"} />
    </div>
  );
}
