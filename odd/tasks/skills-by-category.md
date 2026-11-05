# Habilidades del CV agrupadas por categoría

Branch: `feat/ats-harvard-export` · Delivery: work units en la feature branch · Test runner: `cd client && uv run pytest` + `cd front && npm run lint && npx tsc --noEmit && npm run build`

## Specs

- **S1** (usuario, verbatim) — "el problema es coo esta organizado lo de habilidades tecnologias y skill adicionalies ya que estos no estan bien organizado".
- **S2** (usuario, elección) — "pienso que seria bueno dejar una solo coso pero que cada cosa tenga su categoria de cada habilidad tecnica y blanpara que quede en distintas columnasdas": **una sola sección de HABILIDADES**, con cada habilidad dentro de **su categoría**, y las técnicas separadas de las blandas.
- **S3** — Se eliminan las secciones separadas "TECNOLOGÍAS" (hoy alimentada por `Program`) y la mezcla de técnicas + blandas en una sola línea de HABILIDADES. Todo queda bajo el encabezado **HABILIDADES**, en líneas tipo `Categoría: habilidad, habilidad`.
- **S4** — Las columnas literales se descartan y se documenta por qué: el propio requisito de formato ATS (S2 de `odd/tasks/ats-harvard-export.md`: una sola columna, texto real, sin tablas) se rompe con un layout multicolución. Las líneas con etiqueta cumplen la intención visual sin romper el parseo.
- **S5** — La categoría se **deriva del catálogo existente** (`skillcatalog.name → category`, normalizado sin acentos y en minúsculas). No se agrega columna a `skills`: la base no tiene migraciones y alterar Postgres está fuera de alcance.
- **S6** — Habilidades que no están en el catálogo (ej. `.NET`, `Podman`) y los programas (Scrum, metodologías ágiles) no se pierden: entran en líneas fijas `Otras herramientas` y `Metodologías`.
- **S7** — El orden de las líneas es estable y conocido (Lenguajes → Frontend → Backend → Bases de Datos → Datos e IA → DevOps y Cloud → Herramientas → Metodologías → Otras herramientas → Habilidades blandas), para que el CV exportado y la vista previa no cambien de una generación a otra.
- **S8** — El nombre de los bloques del editor y del asistente coincide con dónde termina cada dato en el CV: hoy "Tecnologías" carga skills que aparecen en HABILIDADES, y "Programas" alimenta una sección llamada TECNOLOGÍAS.
- **S9** — El ATS determinista no cambia de comportamiento: las habilidades siguen apareciendo en el texto plano que mide la cobertura de keywords.

## Tasks

| ID | Specs | Route | Status | Commit |
|----|-------|-------|--------|--------|
| T1 | S5,S6 | inline | done | d5d7a87 |
| T2 | S2,S3,S4,S7 | inline | done | d5d7a87 |
| T3 | S3,S7 | inline | done | (este commit) |
| T4 | S8 | inline | done | (este commit) |
| T5 | S9 | inline | done | d5d7a87 |

- **T1** — `get_user_cv_data` devuelve `category` por skill (mapa del catálogo, una sola consulta) y `SkillResponse`/`CvData.Skill` la exponen.
- **T2** — `harvard.py`: `_skills_line` pasa a `_skills_lines` (líneas por categoría, orden fijo), desaparece la sección TECNOLOGÍAS, y `build_layout`/`expected_fragments` se ajustan.
- **T3** — `preview/page.tsx` renderiza las mismas líneas agrupadas (misma data, mismo orden que el export).
- **T4** — Editor y asistente: bloques renombrados a "Habilidades técnicas", "Habilidades blandas" y "Programas y metodologías", cada uno con su categoría visible.
- **T5** — Verificación: `pytest` (render + texto plano del ATS), `lint`, `tsc`, `build`, y extracción de texto del PDF/DOCX generado.

## Log

- **L1 (2026-11-05, usuario, verbatim):** "el problema es coo esta organizado lo de habilidades tecnologias y skill adicionalies ya que estos no estan bien organizado"
- **L2 (2026-11-05, usuario, verbatim, elección de rumbo):** "pienso que seria bueno dejar una solo coso pero que cada cosa tenga su categoria de cada habilidad tecnica y blanpara que quede en distintas columnasdas"
- **L3 (2026-11-05, evidencia del desorden actual):** en el CV real del usuario, HABILIDADES muestra 16 skills (técnicas y blandas mezcladas en una línea) y la sección TECNOLOGÍAS muestra "Scrum, metodologias agiles", que no son tecnologías. El editor llama "Tecnologías" al formulario de skills técnicas (que van a HABILIDADES) y "Programas" al que alimenta TECNOLOGÍAS: tres nombres para dos cosas, mal rotulados.
- **L4 (2026-11-05, medición):** el catálogo (`skillcatalog`, 107 filas, 9 categorías) cubre 14 de las 16 skills del usuario; `.NET` y `Podman` no figuran, y "Scrum"/"metodologias agiles" tampoco. Por eso S6 define líneas de rebrote en vez de exigir que todo exista en el catálogo.
- **L5 (2026-11-05, decisión):** sin columnas literales ni tabla en el DOCX: la validación ATS (`ats_validation.validate_docx_bytes`) marca como problema cualquier `document.tables`, y el propio pedido del usuario exige una sola columna. Se usa "etiqueta: valores" por línea.
- **L6 (2026-11-05, decisión):** categoría derivada en lectura, no persistida. Si mañana se quiere editable por el usuario, hace falta columna `category` en `skills` + ALTER TABLE explícito (el proyecto no tiene migraciones), y eso es otro cambio con su propio riesgo.
- **L7 (2026-11-05, bug encontrado en el camino):** las líneas con etiqueta se armaban en el layout pero **no aparecían en el DOCX ni en el PDF**, porque ambos renderers de `kind === "text"` leían sólo `item.text` e ignoraban `segments`. Se arregló en los dos renderers y se fijó con `test_habilidades_aparecen_agrupadas_en_docx_y_pdf` (antes de esto ningún test lo detectaba).
- **L8 (2026-11-05, evidencia):** `pytest` → **42 passed** (39 previos + 3 nuevos). Texto extraído del PDF generado para el CV real: `Lenguajes: Python, C#, JavaScript, TypeScript` / `Frontend: React, Vue.js` / `Backend: FastAPI, Django, ASP.NET, Node.js` / `Bases de Datos: PostgreSQL` / `DevOps y Cloud: Docker` / `Herramientas: Git, GitHub` / `Otros conocimientos: .NET, Podman, Scrum, metodologias agiles`, con validación ATS OK en PDF y DOCX y sin tablas. Vista previa verificada en navegador con datos interceptados: mismas líneas, y `TECNOLOGÍAS` ya no aparece.
- **L9 (2026-11-05, límite):** el campo `category` lo devuelve la API (`SkillResponse`, `get_user_cv_data`), así que **hace falta reiniciar `uv run client`** para que las habilidades se agrupen de verdad; sin reinicio todo cae en "Otros conocimientos".
- **L10 (2026-11-05, decisión):** `normalize()` estaba duplicada en `IA_rag/metrics/keywords.py` y `Cv_made/ats_validation.py`; pasó a `client/src/text_norm.py`, usado también por el mapa de categorías.
- **L11 (2026-11-05, bug propio encontrado al revisar):** si una skill técnica venía con una categoría fuera de la lista canónica (el catálogo tiene `Soft Skills` e `Idiomas`, y el usuario puede marcar `Comunicación` como técnica), el grupo **se descartaba en silencio** y la habilidad desaparecía del CV. Ahora las categorías restantes se imprimen ordenadas después de las canónicas y antes de los rebrotes, igual en Python y en TypeScript. Fijado con `test_categorias_fuera_de_lista_no_se_pierden` (fallaba antes del arreglo): `pytest` → **43 passed**.
- **L12 (2026-11-05, reporte del usuario + bug propio):** el usuario pegó la vista previa mostrando cada categoría **dos veces** (una en orden canónico y otra alfabética). Causa: en el espejo TypeScript, el bucle de "categorías restantes" no sacaba del mapa las ya impresas (Python sí hace `pop`), así que las repetía. Afectaba solo a la vista previa del sitio; el DOCX y el PDF estaban bien. Arreglo: `emit()` borra del mapa al imprimir. Verificado en navegador con datos interceptados: orden exacto, cero duplicados, ninguna skill perdida, y paridad línea por línea con el PDF y el DOCX.
- **L13 (2026-11-05, por qué no lo había detectado):** mi verificación de la vista previa corrió **antes** del arreglo de L11, y `pytest` cubre el lado Python pero no el de `front/`, que no tiene runner de tests. Lección: después de tocar el espejo TS hay que volver a medir el DOM, no solo los tests del backend.

