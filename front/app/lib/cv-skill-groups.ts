import type { ProgramResponse, SkillResponse } from "./types";

/**
 * Agrupación de habilidades por categoría, igual que `harvard._skill_groups`.
 *
 * El CV y la vista previa tienen que coincidir, así que el orden y las
 * etiquetas viven acá en un solo lugar: si se cambia uno de los dos, cambiar
 * también `client/src/Cv_made/harvard.py` (SKILL_CATEGORY_ORDER, SKILL_OTHERS,
 * SKILL_SOFT).
 */

export const SKILL_CATEGORY_ORDER = [
  "Lenguajes",
  "Frontend",
  "Backend",
  "Bases de Datos",
  "Datos e IA",
  "DevOps y Cloud",
  "Herramientas",
] as const;

export const SKILL_OTHERS = "Otros conocimientos";
export const SKILL_SOFT = "Habilidades blandas";

export interface SkillGroup {
  label: string;
  names: string[];
}

export function groupSkills(
  skills: SkillResponse[],
  programs: ProgramResponse[],
): SkillGroup[] {
  const buckets = new Map<string, string[]>();

  const add = (label: string, name: string) => {
    const existing = buckets.get(label) ?? [];
    if (name && !existing.includes(name)) {
      existing.push(name);
      buckets.set(label, existing);
    }
  };

  for (const skill of skills) {
    const name = (skill.name || "").trim();
    if (!name) continue;
    if (skill.type === "soft") {
      add(SKILL_SOFT, name);
    } else {
      add((skill.category || "").trim() || SKILL_OTHERS, name);
    }
  }

  // Los programas entran en la misma sección; el catálogo decide la categoría.
  for (const program of programs) {
    const name = (program.name || "").trim();
    if (name) add(SKILL_OTHERS, name);
  }

  const groups: SkillGroup[] = [];
  for (const label of SKILL_CATEGORY_ORDER) {
    const names = buckets.get(label);
    if (names?.length) groups.push({ label, names });
  }
  for (const label of [SKILL_OTHERS, SKILL_SOFT]) {
    const names = buckets.get(label);
    if (names?.length) groups.push({ label, names });
  }
  return groups;
}
