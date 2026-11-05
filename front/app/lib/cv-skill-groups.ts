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

  // Cada categoría se emite UNA sola vez: al imprimirla se saca del mapa, si
  // no los bucles siguientes la vuelven a agregar (ese fue el bug que duplicó
  // las líneas en la vista previa).
  const emit = (label: string) => {
    const names = buckets.get(label);
    if (names?.length) {
      groups.push({ label, names });
      buckets.delete(label);
    }
  };

  for (const label of SKILL_CATEGORY_ORDER) emit(label);

  // Categorías fuera de la lista canónica ("Soft Skills", "Idiomas", ...):
  // se muestran igual, ordenadas, para no perder ninguna habilidad.
  const restantes = [...buckets.keys()]
    .filter((label) => label !== SKILL_OTHERS && label !== SKILL_SOFT)
    .sort();
  for (const label of restantes) emit(label);

  emit(SKILL_OTHERS);
  emit(SKILL_SOFT);

  return groups;
}
