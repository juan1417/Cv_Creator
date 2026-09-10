import json
import logging
import re
from uuid import UUID

from database.get_user_cv import get_user_cv_data, get_user_cv_formatted
from .generator import generate_response

logger = logging.getLogger(__name__)

JOB_MATCH_PROMPT = """Eres un experto en recursos humanos. Compara el siguiente CV con la descripción de un puesto de trabajo y devuelve un análisis detallado de compatibilidad.

## CV del usuario:
{cv_text}

## Descripción del puesto:
{job_description}

## Análisis requerido:

### 1. Score de compatibilidad (0-100)
Calcula un porcentaje general de cuán bien encaja el CV con el puesto.

### 2. Skills que tiene el candidato
Lista las habilidades del CV que son RELEVANTES para el puesto. Para cada una indica:
- name: nombre de la habilidad
- level: nivel estimado (Alto/Medio/Bajo)
- relevance: por qué es relevante para este puesto (1 frase corta)

### 3. Skills que faltan
Lista las habilidades que el puesto requiere pero el CV NO tiene. Para cada una:
- name: nombre de la habilidad
- importance: Alta/Media/Baja
- suggestion: cómo adquirirla o demostrarla (1 frase)

### 4. Fortalezas para este puesto
Lista 2-3 fortalezas específicas del CV que destacan para ESTE puesto particular.

### 5. Debilidades / áreas de mejora
Lista 2-3 puntos débiles o ausentes que podrían restar puntos para ESTE puesto.

### 6. Resumen ejecutivo
Un párrafo corto (2-3 frases) con el veredicto general.

## Formato de respuesta (JSON exacto):
{{
  "match_score": 75,
  "matching_skills": [
    {{"name": "Python", "level": "Alto", "relevance": "Requerido para desarrollo backend"}}
  ],
  "missing_skills": [
    {{"name": "Docker", "importance": "Alta", "suggestion": "Completá un curso básico y mencionalo en tu perfil"}}
  ],
  "strengths": [
    "Experiencia sólida en desarrollo web con tecnologías relevantes"
  ],
  "weaknesses": [
    "Falta experiencia con contenedores y DevOps"
  ],
  "summary": "Tu perfil es adecuado para el puesto, con buena base técnica. Las principales áreas de mejora son..."
}}

## Reglas:
- Responde SOLO con JSON válido
- TODO en español
- Sé ESPECÍFICO: referencia el contenido real del CV y del puesto
- Scores REALISTAS
- Máximo 6 matching_skills, 4 missing_skills, 3 strengths, 3 weaknesses
- Dentro de los strings usá SOLO comillas simples"""

ADAPT_CV_PROMPT = """Eres un experto en optimización de CVs. Adaptá el siguiente CV para que sea más competitivo para el puesto descrito.

## CV actual:
{cv_text}

## Descripción del puesto:
{job_description}

## Skills que faltan según análisis:
{missing_skills}

## Instrucciones de adaptación:

### 1. Resumen profesional (about)
Reescribí el "Sobre mí" enfatizando las habilidades y experiencias más relevantes para ESTE puesto. Mantené el tono profesional.

### 2. Experiencia laboral
Para cada experiencia, optimizá la descripción para destacar logros y habilidades que coinciden con el puesto. Usá verbos de acción y métricas cuando sea posible.

### 3. Habilidades
Reordená las skills poniendo primero las más relevantes para el puesto. Agregá skills que estén en el puesto y se puedan inferir de la experiencia.

### 4. Texto para copiar
Proporcioná el texto adaptado listo para copiar y pegar en cada sección del CV.

## Formato de respuesta (JSON exacto):
{{
  "adapted_about": "Texto del sobre mí adaptado para el puesto...",
  "adapted_experiences": [
    {{
      "company": "Nombre de la empresa",
      "title": "Cargo",
      "description": "Descripción optimizada con métricas y verbos de acción"
    }}
  ],
  "adapted_skills": [
    {{"name": "Skill", "level": "Nivel"}}
  ],
  "key_changes": [
    "Cambios principales realizados y por qué"
  ],
  "tips": [
    "Consejos adicionales para destacar en este puesto"
  ]
}}

## Reglas:
- Responde SOLO con JSON válido
- TODO en español
- NO inventes experiencias o habilidades falsas
- Mantené la honestidad: solo realzá lo que YA existe en el CV
- Si una skill no se puede inferir, NO la agregues
- Sé específico y práctico"""


def compare_cv_job(user_id: UUID, job_description: str) -> dict:
    """Compara el CV del usuario con una descripción de puesto."""
    cv_text = get_user_cv_formatted(user_id)
    if cv_text == "El usuario no tiene un CV registrado.":
        raise ValueError("No se encontro CV para este usuario")

    prompt = JOB_MATCH_PROMPT.format(cv_text=cv_text, job_description=job_description)

    messages = [
        {"role": "system", "content": "Eres un experto en RRHH. Responde SOLO con JSON valido y EXCLUSIVAMENTE en español."},
        {"role": "user", "content": prompt},
    ]

    response = generate_response(messages, temperature=0.3, max_tokens=3000)
    return _parse_match_response(response)


def adapt_cv_for_job(user_id: UUID, job_description: str, missing_skills: list[dict]) -> dict:
    """Adapta el CV del usuario para un puesto específico."""
    cv_text = get_user_cv_formatted(user_id)
    if cv_text == "El usuario no tiene un CV registrado.":
        raise ValueError("No se encontro CV para este usuario")

    missing_text = "\n".join(
        f"- {s['name']} (importancia: {s.get('importance', 'Media')})"
        for s in missing_skills
    ) if missing_skills else "Ninguna skill faltante identificada"

    prompt = ADAPT_CV_PROMPT.format(
        cv_text=cv_text,
        job_description=job_description,
        missing_skills=missing_text,
    )

    messages = [
        {"role": "system", "content": "Eres un experto en CVs. Responde SOLO con JSON valido y EXCLUSIVAMENTE en español."},
        {"role": "user", "content": prompt},
    ]

    response = generate_response(messages, temperature=0.4, max_tokens=4000)
    return _parse_adapt_response(response)


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    if start == -1:
        raise ValueError("No se encontro JSON en la respuesta")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return text[start:]


def _parse_match_response(response: str) -> dict:
    raw = _extract_json(response)
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", raw)
        return json.loads(repaired, strict=False)


def _parse_adapt_response(response: str) -> dict:
    raw = _extract_json(response)
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        repaired = re.sub(r",\s*([}\]])", r"\1", raw)
        return json.loads(repaired, strict=False)
