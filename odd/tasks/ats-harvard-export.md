# ATS real + exportación Harvard (PDF/DOCX)

Branch: `feat/ats-harvard-export` · Delivery: single PR (feature branch) · Test runner: `uv run pytest` (backend), `npm run lint && npx tsc --noEmit` (frontend)

## Specs

- **S1** — El ATS debe funcionar de verdad: el puntaje de compatibilidad ATS se calcula de forma determinista a partir del contenido del CV y de la vacante, no lo inventa el LLM. La validación de formato se hace sobre el archivo generado (texto extraíble, sin tablas ni imágenes).
- **S2** — Los CV generados deben cumplir formato ATS: una sola columna, texto real, encabezados de sección estándar, sin tablas, imágenes, cuadros de texto, encabezados/pies ni columnas múltiples.
- **S3** — Usar la plantilla de Harvard ("me gustaria utilizar la plantilla de harvard"): nombre centrado en mayúsculas, línea de contacto centrada, encabezados de sección en mayúsculas con línea inferior, entradas con organización en negrita a la izquierda y fecha alineada a la derecha, viñetas con `•`. A4, una página objetivo.
- **S4** — La generación de CV debe ser exportable en PDF y DOCX.
- **S5** — Cobertura de keywords contra la vacante: lista determinista de palabras clave extraídas de la descripción del puesto, cuáles aparecen en el CV y cuáles faltan.
- **S6** — La versión adaptada al puesto se genera como archivo separado (sufijo `_adapted`), sin sobrescribir el CV base.
- **S7** — El export no escribe archivos en `client/output/`: los renderers devuelven `bytes`.
- **S8** — El CV separa experiencia laboral de proyectos personales: los proyectos se listan bajo `PROYECTOS DESTACADOS`, el empleo bajo `EXPERIENCIA PROFESIONAL`, y cada encabezado se imprime solo si tiene entradas.
- **S9** — El marcador es el texto `proyecto personal` en el campo organización, comparado normalizado (minúsculas, sin acentos, espacios colapsados). No se agrega una columna `tipo` porque el proyecto no usa migraciones. La regla queda espejada entre `client/src/Cv_made/harvard.py` y `front/app/lib/cv-experience-split.ts`, igual que las categorías de habilidades.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1,S2,S4,S6 | inline | done | 8fb3ce9 |
| T2 | S1,S5 | inline | done | f9c45a8 |
| T3 | S3,S4,S7 | inline | done | 8fb3ce9 |
| T4 | S4,S6,S7 | inline | done | 8fb3ce9, 84dea3f |
| T5 | S1,S2,S4 | inline | done | 84dea3f |
| T6 | S4,S5,S6 | inline | done | ab3a183 |
| T7 | S1,S2,S3 | inline | done | f9c45a8, 8fb3ce9, 84dea3f |
| T8 | — | inline | done | 8fb3ce9, 3983f2d, ab3a183 |
| T9 | S8,S9 | inline | done | 2ee2f4b |

- **T1** — Modelo único de exportación: `CvData` con `skills: list[Skill]`, `from_db()`, y `get_user_cv_data()` completo (achievements, programs, languages, skill.type).
- **T2** — Motor ATS determinista: `metrics/keywords.py` + reescritura de `metrics/ats.py`, `KeywordCoverage` en `models/cv_analysis.py`, cableado en `cv_analyzer`.
- **T3** — Renderer Harvard DOCX (`harvard.py`, devuelve bytes).
- **T4** — Renderer Harvard PDF (`harvard.py`, devuelve bytes) + renderizado de la versión adaptada.
- **T5** — Validación post-generación + `POST /api/cv/export` + `POST /api/cv/ats-report`.
- **T6** — Frontend: `exportCV`/`atsReport` en `api.ts`, botones activos en generar, descarga adaptada en comparar, cobertura de keywords en UI, preview alineado.
- **T7** — Tests `pytest` (motor ATS, keywords, renderers, validación) + lint/tsc.
- **T8** — Borrar código muerto verificado: `docx_creator.py`/`pdf_creator.py` (reemplazados por `harvard.py`), `plantilla.docx` (sin referencias), `_deterministic_completeness` de `cv_analyzer`, rama falsa de `languages` en `_section_to_text`, imports sin uso y `test_cache.py` si queda huérfano.

## Log

- **L1 (2026-11-04, usuario, verbatim):** "vamos a actulizar el proyecto, la actualizacion va a estar relacionado con el funciona miento del sistema ats y en la forma en que se crean los cvs"
- **L2 (2026-11-04, usuario, verbatim):** "bueno y por otro lado tambien hay que incluir que los cv deben de estar en el formato ats"
- **L3 (2026-11-04, usuario, verbatim):** "no axactamente pero me gustaria utilizar la plantilla de  harvard"
- **L4 (2026-11-04, usuario, verbatim):** "perfecto implementemos estos cambios por el momento"
- **L5 (2026-11-04, decisión):** se usa Harvard *resume* (una página), no el CV académico de Harvard, porque el modelo de datos no tiene publicaciones ni investigación. Se mantiene A4.
- **L6 (2026-11-04, decisión):** `metrics/content.py`, `metrics/structure.py` y `metrics/completeness.py` estaban muertos; se cablean en `cv_analyzer` para que las cuatro métricas sean deterministas y el LLM quede solo para resumen y sugerencias cualitativas.
- **L7 (2026-11-04, decisión):** la validación de exportación se hace leyendo el archivo generado (DOCX con `python-docx`, PDF con `pypdf`), no confiando en el renderer. `pypdf` pasa a dependencia de runtime.
- **L8 (2026-11-04, evidencia):** `plantilla.docx` ya era A4 (11906×16838 twips), márgenes 720 twips, sin tablas ni imágenes; los renderers nuevos generan el documento por código y no dependen de la plantilla binaria.
- **L9 (2026-11-04, decisión):** sin descripción de la vacante no se puede medir la cobertura de keywords, así que el bloque de keywords queda "sin medir" y el score ATS se normaliza sobre los 75 puntos aplicables, en vez de castigar al candidato por un dato que no aportó.
- **L10 (2026-11-04, decisión):** el endpoint `POST /api/chat/cv-analysis` deja de aceptar `sections` (el cache por sección murió con las métricas deterministas) y recibe `{ "job_description": ... }`; el tracker `dirty-sections.ts` y `addCustomSkillCatalog` pasan a ser código muerto y se borran.
- **L11 (2026-11-04, decisión):** `apply_adaptation` trabaja sobre una copia profunda del `CvData` y solo reemplaza skills si la lista adaptada trae al menos un nombre válido: una respuesta vacía del LLM no debe vaciar las habilidades del CV base (defecto encontrado por `test_apply_adaptation_ignores_empty_entries`).
- **L12 (2026-11-04, evidencia):** `cd client && uv run pytest` → 29 passed (keywords, motor ATS, renderers DOCX/PDF, validación, rutas de export). `cd front && npm run lint` → 0 errores (3 warnings preexistentes); `npx tsc --noEmit` → 0 errores. `format_date("2019", None)` devuelve `2019 - Presente` (corregido el test, no el código).
- **L13 (2026-11-04, evidencia/restricción):** el rango se verificó con `FastAPI TestClient` (HTTP real sobre `/api/cv/export` y `/api/cv/ats-report` con datos fixture, validación post-generación incluida). No se pudo levantar el servidor contra Neon ni llamar a OpenRouter: no hay `.env` ni `DATABASE_URL`/`OPENROUTER_API` en este entorno. Falta una request viva con datos reales antes de afirmar el comportamiento en producción.
- **L14 (2026-11-04, RDD):** `gentle-ai review mode status` → on (global). `gentle-ai review assess --base-ref e1e3452 --committed-only --untracked-scope=exclude` → risk `medium`, `review_due: false` (`under_budget`): el candidato queda pendiente en el slice hasta que alcance el presupuesto. El inventario de no-trackeados (`.atl/`, `AGENTS.md`) quedó excluido del alcance porque no forma parte del cambio.
- **L15 (2026-11-04, verificación independiente):** verificador de solo lectura sobre `f9c45a8..f71790a` → VERDICT pass, BLOCKERS none. Confirmó: ningún llamador restante de `sections`/`dirty-sections`, contrato `api.ts → chat_routes → analyze_cv` coherente de punta a punta, export no destructivo (`model_copy(deep=True)` + `Response` en memoria), renderers sin escritura a disco (`BytesIO`) y ATS sin `generate_response` en `IA_rag/metrics/`. `pytest` 32 passed, lint 0 errores, tsc 0 errores. Su advisory: un campo desconocido dentro del objeto body se aceptaba y se ignoraba en silencio → corregido con `extra="forbid"` (422) en `999f607` y fijado por test (33 passed). Advisory 2: sin servidor vivo contra Neon/LLM (ver L13).
- **L16 (2026-11-04, verificación viva — cierra L13):** con `.env` real (`DATABASE_URL`, `OPENROUTER_API`, `MODELO`) y la API corriendo en `127.0.0.1:8000` contra Neon: `POST /api/cv/export` → 200 en PDF (1 página, 1951 caracteres extraídos) y DOCX (1947), `content-disposition: attachment; filename="CV_Juan_Manuel_Machado_Acosta.pdf"`, headers `x-export-*` presentes; `git status` limpio en `client/output/` y `client/src/Cv_made/output/` → **S7 confirmado en vivo**. `POST /api/cv/ats-report` → 87.5, `export_check.ok: true`, 4/9 keywords presentes. `POST /api/chat/cv-analysis` → 200 en **11.6 s** con resumen y mejoras redactados por el LLM.
- **L17 (2026-11-04, decisión — elección de modelo):** se evaluaron los 16 modelos gratuitos de OpenRouter con el prompt real. `nvidia/nemotron-3.5-lightning:free` devolvía contenido vacío (gasta el presupuesto razonando), `google/gemma-4-31b-it:free` y `xingchen-agi/xing4.0-29b-a4b:free` respondían 429 del pool compartido, `dots-studio`/`recursive/flint` sí respondían; `openrouter/free` y `cohere/north-mini-code:free` devolvían JSON truncado. Se eligió **`recursive/flint-v1.0:free`** (chat 3.4 s, JSON 4.7 s, buen español) para `MODELO` en `client/.env` (gitignored, no se commitea). De paso: los `max_tokens` del narrador subieron a 4000 y los reintentos internos a 0, y la prueba real reveló keywords basura (`valora`, `vacante`, `perfil`) que se agregaron a los stopwords (`082bd1c`).
- **L18 (2026-11-05, pedido del usuario, verbatim):** "puedes separa lo que son los proyectos con la experiencia y pon 2 proyectos destacados".
- **L19 (2026-11-05, decisión):** el marcador `proyecto personal` vive en el texto de `company`, no en una columna: el proyecto no usa migraciones y `create_all_tables()` no altera tablas existentes. Se compara con `text_norm.normalize` (el mismo helper del ATS) y queda espejado en `front/app/lib/cv-experience-split.ts`, como ya pasa con las categorías de habilidades.
- **L20 (2026-11-05, evidencia):** test-first: 4 tests nuevos en `tests/test_renderers.py` observados en ROJO (4 failed / 10 passed) y luego VERDE → `uv run pytest` **49 passed**. `npx tsc --noEmit` 0 errores, `npm run lint` 0 errores (2 warnings preexistentes), `npm run build` OK. Export real con el renderer nuevo (instancia temporal en `127.0.0.1:8003`): **PDF de 1 página**, secciones `EXPERIENCIA PROFESIONAL` (Data Hack) y `PROYECTOS DESTACADOS` (Cv_Creator, ProFinancas). Medición contra la vacante: ATS **83.3/100**, overall **88.0**, keywords 10/30, `export_check.ok: true`, 2025 caracteres legibles.
- **L21 (2026-11-05, datos del usuario):** CV `a99de9b3-…`: 3 experiencias con fechas verificadas en GitHub (Cv_Creator 2026-09-04→presente, ProFinancas 2026-02-13→2026-07-24, Data Hack 2025-05-20→2025-05-21) y 6 skills del catálogo (Astro, Vite, Next.js, Tailwind CSS, SQL, ESLint, Vercel). Se eliminó la fila "Gestor de proyectos" para dejar **2 proyectos destacados** y el logro duplicado del hackathon; se corrigieron acentos en `Español`/`Inglés` sin tocar el nivel (B1 sigue pendiente de confirmación del usuario).
- **L22 (2026-11-05, pendiente):** el servidor que el usuario tiene en `127.0.0.1:8000` corre `uv run client` **sin `--reload`**: todavía sirve el código anterior a `2ee2f4b`, así que la vista previa y el export en vivo no muestran `PROYECTOS DESTACADOS` hasta que lo reinicie.
- **L23 (2026-11-05, RDD):** `gentle-ai review mode status` → activo por defecto (nadie lo apagó). `gentle-ai review assess --base-ref d99f158 --committed-only --untracked-scope exclude --expected-untracked-inventory sha256:14e6bf0e…` → risk **medium**, `review_due: false`, razón **under_budget** (275 líneas en 6 paths). No se abre revisión nativa ni ceremonia de consentimiento para esta unidad; el slice queda abierto y la frontera revisada sigue en el último límite ya acknowledged. Los no-trackeados `.atl/` y `AGENTS.md` siguen excluidos del alcance.
