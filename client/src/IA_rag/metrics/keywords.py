"""Extracción y cobertura determinista de palabras clave.

Sin LLM: el mismo CV y la misma vacante producen siempre el mismo resultado.
Se comparan tokens normalizados (minúsculas, sin acentos) contra el texto
completo del CV.
"""

import re
import unicodedata
from collections import Counter

from models.cv_analysis import KeywordCoverage

# Palabras funcionales y muletillas de las ofertas de empleo. No son keywords:
# si se contaran, cualquier CV "coincidiría" con cualquier vacante.
STOPWORDS: frozenset[str] = frozenset({
    # Español
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
    "en", "con", "sin", "por", "para", "al", "del", "que", "se", "su", "sus",
    "es", "son", "ser", "estar", "como", "mas", "muy", "no", "si", "te", "tu",
    "tus", "nuestro", "nuestra", "lo", "le", "les", "este", "esta", "estos",
    "estas", "ese", "esa", "esos", "esas", "otros", "otras", "donde", "cuando",
    "sobre", "entre", "hasta", "desde", "nos", "les", "cada", "todo", "toda",
    "todos", "todas", "tambien", "solo", "sólo", "sea", "sera", "será", "hay",
    "han", "has", "ha", "fue", "era", "más", "pero", "porque", "aunque", "asi",
    "así", "que", "quien", "quienes", "cual", "cuales", "muy", "bien",
    # Boilerplate de ofertas
    "puesto", "trabajo", "empleo", "empresa", "compañia", "compania",
    "candidato", "candidata", "candidatos", "postulante", "funcion",
    "funciones", "requisito", "requisitos", "responsabilidad",
    "responsabilidades", "tarea", "tareas", "jornada", "salario", "contrato",
    "modalidad", "beneficio", "beneficios", "buscamos", "buscando", "ofrecemos",
    "ofrecer", "requerimos", "requiere", "requerido", "requerida",
    "deseable", "imprescindible", "valorable", "experiencia", "experiencias",
    "año", "años", "ano", "anos", "mes", "meses", "nivel", "conocimiento",
    "conocimientos", "manejo", "uso", "ademas", "además", "tener", "tiene",
    "debe", "deberá", "debera", "zona", "horario", "remoto", "remota",
    "hibrido", "hibrida", "inmediata",
    # Muletillas de avisos (encontradas en ofertas reales)
    "vacante", "perfil", "disponible", "valora", "valoramos", "postular",
    "postulacion", "incorporacion", "contratacion", "sumarte", "sumamos",
    "sumate", "busca", "buscan", "busqueda", "lugar", "area", "equipo",
    # Inglés
    "the", "and", "or", "of", "to", "in", "on", "for", "with", "a", "an", "is",
    "are", "be", "as", "at", "by", "from", "will", "you", "your", "we", "our",
    "this", "that", "these", "those", "it", "its", "they", "them", "their",
    "have", "has", "had", "was", "were", "been", "being", "not", "but", "if",
    "can", "could", "should", "would", "may", "might", "must", "about", "into",
    "than", "then", "there", "here", "who", "what", "which", "when", "where",
    "why", "how", "all", "any", "both", "each", "more", "most", "other",
    "some", "such", "only", "own", "same", "so", "too", "very", "just",
    "role", "job", "company", "candidate", "experience", "years", "year",
    "requirements", "responsibilities", "skills", "ability", "work", "working",
    "team", "teams", "plus", "nice", "must", "ideal", "offer", "benefits",
})

# Tokens técnicos cortos que sí son keywords.
SHORT_TECH: frozenset[str] = frozenset({
    "c", "c++", "c#", "go", "r", "js", "ts", "ai", "ml", "bi", "qa", "ux", "ui",
    "sql", "css", "php", "aws", "gcp", "api", "etl", "ci", "cd", "db",
})

_TOKEN_RE = re.compile(r"[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ][A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ+#._\-]*")

DEFAULT_KEYWORD_LIMIT = 30
KEYWORD_MAX_SCORE = 25.0


def normalize(text: str) -> str:
    """Minúsculas, sin acentos y con espacios colapsados."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _is_candidate(key: str) -> bool:
    if not key or key in STOPWORDS:
        return False
    if len(key) < 3 and key not in SHORT_TECH:
        return False
    return any(char.isalnum() for char in key)


def tokens_with_display(text: str) -> list[tuple[str, str]]:
    """Devuelve pares ``(normalizado, forma original)`` en orden de aparición."""
    pairs: list[tuple[str, str]] = []
    for raw in _TOKEN_RE.findall(text or ""):
        display = raw.strip("._-")
        if not display:
            continue
        key = normalize(display)
        if not _is_candidate(key):
            continue
        pairs.append((key, display))
    return pairs


def extract_keywords(text: str, limit: int = DEFAULT_KEYWORD_LIMIT) -> list[str]:
    """Keywords de un texto, ordenadas por frecuencia y luego alfabéticamente."""
    pairs = tokens_with_display(text)
    counts = Counter(key for key, _ in pairs)
    display: dict[str, str] = {}
    for key, original in pairs:
        display.setdefault(key, original)

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [display[key] for key, _ in ranked[:limit]]


def keyword_coverage(
    cv_text: str,
    job_description: str,
    limit: int = DEFAULT_KEYWORD_LIMIT,
) -> KeywordCoverage:
    """Compara las keywords de la vacante contra el texto del CV."""
    keywords = extract_keywords(job_description, limit=limit)
    if not keywords:
        return KeywordCoverage(
            score=0.0,
            max_score=KEYWORD_MAX_SCORE,
            matched=[],
            missing=[],
            total=0,
            job_description_provided=bool((job_description or "").strip()),
            message="Sin palabras clave reconocibles en la descripción del puesto.",
        )

    cv_tokens = {key for key, _ in tokens_with_display(cv_text)}
    matched: list[str] = []
    missing: list[str] = []
    for keyword in keywords:
        if normalize(keyword) in cv_tokens:
            matched.append(keyword)
        else:
            missing.append(keyword)

    score = round(KEYWORD_MAX_SCORE * len(matched) / len(keywords), 1)
    return KeywordCoverage(
        score=score,
        max_score=KEYWORD_MAX_SCORE,
        matched=matched,
        missing=missing,
        total=len(keywords),
        job_description_provided=True,
        message=f"{len(matched)}/{len(keywords)} palabras clave de la vacante presentes en el CV",
    )
