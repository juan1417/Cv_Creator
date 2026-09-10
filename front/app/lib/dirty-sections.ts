/**
 * Tracking de secciones modificadas del CV.
 * Usa localStorage para persistir entre páginas (edit → analysis).
 *
 * Cuando el usuario edita una sección, se marca como "dirty".
 * Al ir a análisis, se envían solo las secciones dirty y se limpiean.
 */

const STORAGE_KEY = "cv_dirty_sections";

export type CVSection = "personal" | "experience" | "education" | "skills" | "languages";

/** Obtiene las secciones marcadas como modificadas. */
export function getDirtySections(): CVSection[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as CVSection[];
  } catch {
    return [];
  }
}

/** Marca una sección como modificada. */
export function markSectionDirty(section: CVSection): void {
  if (typeof window === "undefined") return;
  const current = getDirtySections();
  if (!current.includes(section)) {
    current.push(section);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  }
}

/** Limpia las secciones marcadas (después de análisis). */
export function clearDirtySections(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

/** Marca múltiples secciones como modificadas. */
export function markSectionsDirty(sections: CVSection[]): void {
  if (typeof window === "undefined") return;
  const current = getDirtySections();
  for (const s of sections) {
    if (!current.includes(s)) {
      current.push(s);
    }
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
}
