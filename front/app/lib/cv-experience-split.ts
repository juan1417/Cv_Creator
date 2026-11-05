import type { ExperienceResponse } from "./types";

/**
 * Separación entre experiencia laboral y proyectos personales, igual que
 * `harvard.is_personal_project`.
 *
 * La vista previa y el export tienen que coincidir, así que la regla vive acá en
 * un solo lugar: si se cambia, cambiar también `client/src/Cv_made/harvard.py`
 * (PROJECT_MARKER, SECTION_EXPERIENCE, SECTION_PROJECTS).
 */

export const PROJECT_MARKER = "proyecto personal";

export const SECTION_EXPERIENCE = "EXPERIENCIA PROFESIONAL";
export const SECTION_PROJECTS = "PROYECTOS DESTACADOS";

/** Minúsculas, sin acentos y con espacios colapsados (espejo de `text_norm.normalize`). */
function normalize(text: string): string {
  return text
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

export function isPersonalProject(company?: string | null): boolean {
  return normalize(company ?? "").includes(PROJECT_MARKER);
}

/**
 * La organización sin el marcador, igual que `harvard.project_label`: el
 * marcador es un mecanismo del layout, no algo que un reclutador deba leer.
 */
export function projectLabel(company?: string | null): string {
  const texto = (company ?? "").replace(/\(\s*proyecto\s+personal\s*\)/gi, " ");
  const limpio = texto.replace(/\s+/g, " ").trim().replace(/^[\s,;·\-–—]+|[\s,;·\-–—]+$/g, "");
  return limpio || (company ?? "").trim();
}

export interface ExperienceSplit {
  jobs: ExperienceResponse[];
  projects: ExperienceResponse[];
}

/** Separa (empleos, proyectos) sin perder el orden original. */
export function splitExperience(
  experiences: ExperienceResponse[],
): ExperienceSplit {
  const jobs: ExperienceResponse[] = [];
  const projects: ExperienceResponse[] = [];

  for (const experience of experiences) {
    if (isPersonalProject(experience.company)) projects.push(experience);
    else jobs.push(experience);
  }

  return { jobs, projects };
}
