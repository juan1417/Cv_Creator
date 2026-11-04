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

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S1,S2,S4,S6 | inline | pending | — |
| T2 | S1,S5 | inline | pending | — |
| T3 | S3,S4,S7 | inline | pending | — |
| T4 | S4,S6,S7 | inline | pending | — |
| T5 | S1,S2,S4 | inline | pending | — |
| T6 | S4,S5,S6 | inline | pending | — |
| T7 | S1,S2,S3 | inline | pending | — |
| T8 | — | inline | pending | — |

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
