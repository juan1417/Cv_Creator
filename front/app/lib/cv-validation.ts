import type { FullCV } from "./types";

/**
 * Reglas de validación del wizard y estado de secciones del CV.
 *
 * Una sola fuente de verdad para "¿esto está completo?" y "¿esto se puede
 * guardar?": la usa el asistente de creación y el dashboard, para que el
 * número que ve el usuario y el que bloquea el formulario nunca se contradigan.
 */

export type FieldErrors = Record<string, string>;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/;
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export interface CvSectionStatus {
  key: string;
  label: string;
  filled: boolean;
}

/** Normaliza una fecha ISO de la API (`2021-03-01T00:00:00`) para `<input type="date">`. */
export function toDateInput(iso: string | null | undefined): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

export function isEmail(value: string): boolean {
  return EMAIL_RE.test(value.trim());
}

/** Devuelve el primer mensaje de error, o `null` si no hay errores. */
export function firstError(errors: FieldErrors): string | null {
  const keys = Object.keys(errors);
  return keys.length > 0 ? (errors[keys[0]] ?? null) : null;
}

export function hasErrors(errors: FieldErrors): boolean {
  return Object.keys(errors).length > 0;
}

function checkDateRange(
  start: string,
  end: string,
  errors: FieldErrors,
): void {
  if (start && !ISO_DATE_RE.test(start)) {
    errors.start_date = "Fecha de inicio inválida";
  }
  if (end && !ISO_DATE_RE.test(end)) {
    errors.end_date = "Fecha de fin inválida";
  }
  if (
    start && end &&
    ISO_DATE_RE.test(start) && ISO_DATE_RE.test(end) &&
    end < start
  ) {
    errors.end_date = "La fecha de fin no puede ser anterior al inicio";
  }
}

export interface PersonalData {
  name: string;
  email: string;
  phone: string;
  address: string;
  about: string;
  porfolio: string;
  linkedin: string;
}

/**
 * Única validación bloqueante del wizard: sin nombre y email el CV no es
 * contactable ni pasa los filtros básicos de un ATS (S4).
 */
export function validatePersonal(data: PersonalData): FieldErrors {
  const errors: FieldErrors = {};

  if (!data.name.trim()) {
    errors.name = "Ingresá tu nombre y apellido";
  } else if (data.name.trim().length < 2) {
    errors.name = "El nombre es demasiado corto";
  }

  if (!data.email.trim()) {
    errors.email = "Ingresá tu email de contacto";
  } else if (!isEmail(data.email)) {
    errors.email = "El email no tiene un formato válido";
  }

  return errors;
}

export interface ExperienceData {
  title: string;
  company: string;
  start_date: string;
  end_date: string;
  description: string;
}

export function validateExperience(data: ExperienceData): FieldErrors {
  const errors: FieldErrors = {};

  if (!data.title.trim()) {
    errors.title = "Ingresá el título del puesto";
  }
  if (!data.company.trim()) {
    errors.company = "Ingresá la empresa o proyecto";
  }
  if (!data.start_date.trim()) {
    errors.start_date = "Ingresá la fecha de inicio";
  }
  checkDateRange(data.start_date, data.end_date, errors);

  return errors;
}

export interface EducationData {
  degree: string;
  institution: string;
  start_date: string;
  end_date: string;
}

export function validateEducation(data: EducationData): FieldErrors {
  const errors: FieldErrors = {};

  if (!data.degree.trim()) {
    errors.degree = "Ingresá la carrera o título";
  }
  if (!data.institution.trim()) {
    errors.institution = "Ingresá la institución";
  }
  if (!data.start_date.trim()) {
    errors.start_date = "Ingresá la fecha de inicio";
  }
  checkDateRange(data.start_date, data.end_date, errors);

  return errors;
}

/** No se pueden guardar skills repetidas del mismo tipo. */
export function validateSkillName(
  name: string,
  type: "tech" | "soft",
  existing: { name: string; type?: string }[],
): string | null {
  const trimmed = name.trim();
  if (!trimmed) return "Ingresá o elegí una habilidad";

  const duplicate = existing.some(
    (skill) =>
      (skill.type || "tech") === type &&
      skill.name.trim().toLowerCase() === trimmed.toLowerCase(),
  );
  if (duplicate) return "Ya está en tu lista";

  return null;
}

export interface AchievementData {
  title: string;
  description: string;
}

export function validateAchievement(data: AchievementData): FieldErrors {
  const errors: FieldErrors = {};
  if (!data.title.trim()) {
    errors.title = "Ingresá el título del logro";
  }
  return errors;
}

export interface LanguageData {
  name: string;
  level: string;
}

export function validateLanguage(data: LanguageData): FieldErrors {
  const errors: FieldErrors = {};
  if (!data.name.trim()) {
    errors.name = "Ingresá el idioma";
  }
  return errors;
}

// ─── Estado del CV (compartido con el dashboard) ─────────────────────────────

export function cvSections(cv: FullCV): CvSectionStatus[] {
  return [
    { key: "personal", label: "Datos personales", filled: !!(cv.cv.name && cv.cv.email) },
    { key: "experience", label: "Experiencia", filled: cv.experiences.length > 0 },
    { key: "tech_skills", label: "Skills técnicas", filled: cv.skills.some((s) => s.type !== "soft") },
    { key: "soft_skills", label: "Skills blandas", filled: cv.skills.some((s) => s.type === "soft") },
    { key: "education", label: "Formación", filled: cv.education.length > 0 },
    { key: "achievements", label: "Logros", filled: cv.achievements.length > 0 },
    { key: "programs", label: "Programas", filled: cv.programs.length > 0 },
    { key: "languages", label: "Idiomas", filled: cv.languages.length > 0 },
  ];
}

/** Porcentaje de completitud que muestra el dashboard (7 indicadores). */
export function cvCompleteness(cv: FullCV): number {
  return Math.round(
    ((cv.cv.name ? 1 : 0) +
      (cv.cv.email ? 1 : 0) +
      (cv.cv.phone ? 1 : 0) +
      (cv.cv.about ? 1 : 0) +
      (cv.experiences.length > 0 ? 1 : 0) +
      (cv.skills.length > 0 ? 1 : 0) +
      (cv.education.length > 0 ? 1 : 0)) /
      7 *
      100,
  );
}

export function sectionProgress(cv: FullCV): {
  filled: number;
  total: number;
  sections: CvSectionStatus[];
} {
  const sections = cvSections(cv);
  return {
    filled: sections.filter((section) => section.filled).length,
    total: sections.length,
    sections,
  };
}
