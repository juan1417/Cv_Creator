# Unificar y endurecer el editor de CV

Branch: `feat/ats-harvard-export` · Delivery: work units en la feature branch · Test runner: `cd front && npm run lint && npx tsc --noEmit` (+ `npm run build`)

## Specs

- **S1** (usuario, verbatim) — "puedes mejorar la ux/ui de editar cv".
- **S2** (usuario, elección) — entre (a) unificar formularios + endurecer, (b) solo pulido visual, (c) funcional primero y visual después → eligió **unificar formularios + endurecer**: "El editor adopta los mismos formularios del asistente (los 8 bloques duplicados pasan a ser uno), validación en línea con mensaje en cada campo, confirmación al borrar, feedback de guardado real y estados vacíos con acción. Misma UX en crear y editar, y el archivo baja mucho de tamaño."
- **S3** — Una implementación por entidad: datos personales, experiencia, formación, logros, habilidades técnicas, habilidades blandas, programas e idiomas viven en un solo módulo compartido por `/cv/edit` y `/cv/create`.
- **S4** — Ningún campo vacío se guarda en silencio: la validación bloquea con mensaje junto al campo (antes: Experiencia y Formación guardaban títulos vacíos y Logros/Idiomas no hacían nada sin avisar).
- **S5** — Borrar un item con contenido (experiencia, formación, logro) pide confirmación en dos pasos; un clic nunca borra.
- **S6** — Feedback de guardado real: estado visible (`Guardando…`/`Guardado`) y los fallos del autoguardado de datos personales aparecen en el banner, no en un `catch {}` vacío.
- **S7** — Estados vacíos con acción: cada sección sin datos dice qué cargar y por qué.
- **S8** — Sin cambios de backend ni de API: se reusa `/api/cv/*` y `/api/chat/cv/*` tal cual.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S3 | inline | done | 729516a |
| T2 | S3,S4,S5,S6,S7 | inline | done | 876b11e |
| T3 | S3,S4,S5,S7 | inline | done | 729516a |
| T4 | S1,S2 | inline | done | 729516a, 876b11e, 7544e55 |

- **T1** — Módulos compartidos: `app/components/cv-form-ui.tsx` (primitivas: campos, `SaveState`, `ItemCard`, `ChipList`, `FormError`, `ConfirmDeleteButton`) y `app/components/cv-forms.tsx` (los seis formularios por entidad más `PersonalFields`).
- **T2** — El editor pasa a consumirlos: se borran los seis componentes de sección y `Field` duplicados.
- **T3** — El asistente pasa a consumirlos: los pasos quedan como orquestación fina (texto de orientación + `StepActions`).
- **T4** — Verificación: `lint`, `tsc`, `build` y verificador independiente por el ítem de riesgo (código compartido que consumen dos rutas).

## Log

- **L1 (2026-11-04, usuario, verbatim):** "puedes mejorar la ux/ui de editar cv"
- **L2 (2026-11-04, usuario, elección):** eligió **unificar formularios + endurecer** (opción a) descrita en S2.
- **L3 (2026-11-04, evidencia del estado previo):** en `/cv/edit` había **0 confirmaciones de borrado**; Experiencia y Formación guardaban sin validar (`handleSave` sin ninguna regla); Logros e Idiomas hacían `if (!title.trim()) return;` **sin mensaje**, o sea que el botón no hacía nada y no decía nada; 4 bloques `showForm` y 6 `saving` duplicados en 1287 líneas; el autoguardado de datos personales tragaba errores en `catch {}`.
- **L4 (2026-11-04, desviación de proceso):** el trabajo se escribió antes de crear este documento (el usuario pidió la mejora y eligió el rumbo en la misma sesión). El documento se crea al cierre para dejar el alcance y la evidencia registrados, no para planificar.
- **L5 (2026-11-04, decisión):** los formularios viven en `app/components/`, no en la carpeta del asistente: así ninguna ruta importa componentes desde la otra. `plain` permite al asistente renderizar el mismo formulario sin meter una tarjeta dentro de otra.
- **L6 (2026-11-04, decisión):** confirmar solo lo caro de recuperar (experiencia, formación, logros) y no los chips de skills/programas/idiomas, que se reagregan en dos segundos: confirmar todo haría el flujo lento sin reducir el daño.
- **L7 (2026-11-04, decisión):** editar formación sigue siendo alta + baja porque la API no tiene `update`, pero **el alta va primero** y conserva la descripción original, para que un fallo no pierda datos.
- **L8 (2026-11-04, incidencia):** un script de reescritura cortó el archivo en un cierre de JSX ambiguo y duplicó `edit/page.tsx` (dos `export default`). Se detectó con `tsc` (`Duplicate function implementation`), se restauró desde git y se rehizo con marcas inequívocas. Lección: al editar por script, verificar marcadores de inicio **y** de fin y recontar `export default` después.
- **L9 (2026-11-04, evidencia):** `npx tsc --noEmit` → 0 errores, `npm run lint` → 0 errores (3 warnings preexistentes), `npm run build` → OK. `edit/page.tsx` pasó de **1287 a 241 líneas**.
- **L10 (2026-11-04, verificación independiente):** verificador de solo lectobre sobre el rango → VERDICT **pass, BLOCKERS none**. Confirmó con file:line: los siete formularios existen solo en `cv-forms.tsx` y no quedan restos de los seis componentes ni de `Field` (`grep` → 0 hits); ninguna ruta importa desde la carpeta de otra; los cuatro arreglos están en código (validación previa a la llamada con `errors.*` bajo el campo, `ConfirmDeleteButton` en los tres `ItemCard`, `setError(apiErrorMessage(...))` en el autoguardado, seis estados vacíos con texto de orientación); el editor conserva el debounce, la pantalla de reintento precede a `if (!cv) return null`, y `refreshCV` nunca dispara el spinner; el asistente mantiene sus 6 pasos con `plain` y `StepActions`. Comandos observados: `tsc` exit 0, `lint` exit 0 (3 warnings preexistentes), `build` exit 0 con `/cv/edit` y `/cv/create`.
- **L11 (2026-11-04, advisories del verificador):** el directive `eslint-disable` sin uso en `edit/page.tsx:32` es idéntico al baseline (no lo toco); se eliminó el directorio vacío `create/components/`; los chips de skills/programas/idiomas borran en un clic, que es la decisión de L6, no un hueco.
- **L12 (2026-11-04, RDD):** `gentle-ai review assess --base-ref e1e3452 --committed-only --untracked-scope=exclude` → riesgo `medium`, `review_due: false` (`under_budget`): el candidato queda pendiente en el slice.

