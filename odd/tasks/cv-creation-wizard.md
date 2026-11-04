# Wizard guiado para crear el CV

Branch: `feat/ats-harvard-export` · Delivery: work units en la feature branch · Test runner: `cd front && npm run lint && npx tsc --noEmit` (+ `npm run build`)

## Specs

- **S1** (usuario, verbatim) — "vamos a hacer un cambio en el sistema de edicion de cv mas que todo para mejorar la experiencia en la que uno ingresa los datos para crear el cv". Ruta elegida por el usuario: **wizard guiado por pasos para crear el CV**.
- **S2** — Pasos en orden: 1 Datos personales → 2 Experiencia → 3 Formación → 4 Habilidades (tecnologías, blandas, programas) → 5 Logros e idiomas → 6 Revisar. Barra de progreso, botón atrás/adelante y salto directo a cualquier paso ya visitado.
- **S3** — Al pasar a "Continuar" el paso guarda en el backend con la API que ya existe; si el usuario cierra la pestaña a mitad, lo guardado no se pierde y al volver retoma en el paso donde estaba.
- **S4** — Validación que bloquea solo lo que inutiliza el CV: paso 1 exige nombre y email con formato válido; un item a medio completar no se puede guardar. Lo opcional se puede saltear con una acción explícita ("Todavía no tengo esto"), nunca con un campo obligatorio inventado.
- **S5** — "Revisar" muestra qué hay y qué falta por sección, permite editar cada sección desde ahí, y ofrece la descarga PDF/DOCX con `/api/cv/export`.
- **S6** — Cargar datos no recarga ni desmonta el formulario: pasos como estado de cliente, feedback de guardado visible en el propio paso, sin spinner a pantalla completa.
- **S7** — `/cv/edit` sigue existiendo para retocar; el wizard es la ruta nueva `/cv/create`. El dashboard ofrece el wizard cuando el CV está vacío, y el editor ofrece abrir el asistente.
- **S8** — Sin cambios de backend ni de base de datos: se reusa `/api/cv/*` y `/api/chat/cv/*` tal cual.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S4,S6 | inline | done | 25dd047 |
| T2 | S2,S3,S6 | inline | done | 0c18fbb |
| T3 | S2,S3,S4 | inline | done | 0c18fbb |
| T4 | S2,S3,S4 | inline | done | 0c18fbb, 3b0c039 |
| T5 | S2,S3,S4,S5 | inline | done | 3b0c039 |
| T6 | S7 | inline | done | a55ee98 |
| T7 | S6 | inline | done | 25dd047, 0c18fbb, 3b0c039, a55ee98 |

- **T1** — `app/lib/cv-validation.ts` (reglas por paso + `cvSections()` de completitud, extraído de la lógica que hoy está incrustada en el dashboard) y primitivas de formulario compartidas (`TextField`, `DateField`, `ItemCard`, `StepActions`, `SaveState`).
- **T2** — Shell `/cv/create`: carga del CV real, lista de pasos, progreso, retomada del paso en `localStorage`, y el paso 1 (datos personales) con guardado al continuar.
- **T3** — Paso 2 (experiencia): alta/edición/baja dentro del paso, con ayuda de verbos de acción y métricas.
- **T4** — Paso 3 (formación) y paso 4 (habilidades técnicas, blandas y programas, con autocompletado del catálogo existente).
- **T5** — Paso 5 (logros e idiomas) y paso 6 (revisar: qué hay/quién falta, links por sección y descarga PDF/DOCX).
- **T6** — CTAs: dashboard manda al wizard cuando el CV está vacío (y el dashboard pasa a usar el `cvSections()` compartido); `/cv/edit` enlaza al asistente.
- **T7** — Verificación: `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## Log

- **L1 (2026-11-04, usuario, verbatim):** "perfecto vamos a hacer un cambio en el sistema de edicion de cv mas que todo para mejorar la experiencia en la que uno ingresa los datos para crear el cv"
- **L2 (2026-11-04, usuario, elección):** entre (a) wizard guiado por pasos, (b) pulir el editor actual in situ, (c) crear el CV conversando con la IA → eligió **wizard guiado por pasos**.
- **L3 (2026-11-04, evidencia del estado actual):** `/cv/edit` son 1285 líneas en una página con 7 secciones apiladas; cada sección repite su propio `showForm`/`editId`/`saving`/`resetForm` (8 `useState` de formulario duplicados) y no hay validación ni progreso. El dashboard calcula "secciones completadas" con lógica propia inline.
- **L4 (2026-11-04, decisión):** el wizard no reemplaza al editor: ruta nueva `/cv/create` para **crear**, `/cv/edit` queda para **retocar**. Así el cambio no toca el flujo que ya funciona (S7).
- **L5 (2026-11-04, decisión):** cero cambios de backend. El wizard persiste paso por paso con los endpoints existentes, así que "guardar y salir" nunca pierde datos y no hay estado intermedio propio del wizard.
- **L6 (2026-11-04, decisión):** la única validación bloqueante es nombre + email válido (sin eso el CV no sirve para un ATS ni para contactar). Todo lo demás es opcional con skip explícito; se documenta en S4 para no inventar requisitos.
- **L7 (2026-11-04, docs leídas):** `front/node_modules/next/dist/docs/01-app/01-getting-started/{03-layouts-and-pages,04-linking-and-navigating}.md` — páginas del App Router siguen siendo Server Components por defecto (`"use client"` para interactividad) y `<Link>` para navegación interna; no hay cambios que condicionen el diseño.
- **L8 (2026-11-04, decisión):** la API no tiene `update` para educación, programas ni idiomas (sí para experiencia). El asistente edita esos items como alta nueva y después baja de la anterior, y **el alta va primero**: si algo falla queda un duplicado visible, nunca un dato perdido. El editor actual hacía baja-primero, que en cambio pierde la entrada.
- **L9 (2026-11-04, decisión):** para no triplicar lógica, `cvSections()` y `cvCompleteness()` salieron del dashboard a `app/lib/cv-validation.ts` y `LEVELS`/`LANGUAGE_LEVELS` a `app/lib/cv-constants.ts`; el dashboard y el editor pasan a importarlos con los mismos valores de antes.
- **L10 (2026-11-04, evidencia):** `npm run lint` → 0 errores (3 warnings preexistentes), `npx tsc --noEmit` → 0 errores, `npm run build` → OK con la ruta `/cv/create` generada.
- **L11 (2026-11-04, limitación):** no hay credenciales de login en este entorno, así que el flujo completo del asistente **no se probó en un navegador**: la verificación es de tipos, lint y build. Queda pendiente que alguien recorra los 6 pasos con un usuario real.
- **L12 (2026-11-04, RDD):** tras los commits del asistente se corre `gentle-ai review assess --base-ref e1e3452 --committed-only --untracked-scope=exclude`; el resultado queda registrado abajo.
