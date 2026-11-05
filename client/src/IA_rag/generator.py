from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import time

load_dotenv()

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API"),
            timeout=60.0,
            max_retries=2,
        )
    return _client


def generate_response(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    response_format: dict | None = None,
    max_retries: int = 2,
) -> str:
    """Pide una completión al modelo.

    Los modelos que razonan antes de responder gastan parte del presupuesto
    en razonamiento (medido: 217-614 tokens por pregunta corta). Si el
    presupuesto se agota, la respuesta llega vacía: en ese caso se reintenta
    con el doble de tokens en lugar de repetir con el mismo límite.
    """
    client = get_client()
    kwargs = {
        "model": model or os.getenv("MODELO"),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    last_error = None
    budget = max_tokens
    for attempt in range(max_retries + 1):
        kwargs["max_tokens"] = budget
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content if response.choices else None
            if content and content.strip():
                return content
            last_error = "Empty response from model"
            budget = min(budget * 2, 16000)
            logger.warning(
                "Attempt %d: empty response with max_tokens=%d, retrying with %d",
                attempt + 1, kwargs["max_tokens"], budget,
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1}: {last_error}")

        if attempt < max_retries:
            time.sleep(1)  # Wait before retry

    raise ValueError(f"El modelo no respondio despues de {max_retries + 1} intentos: {last_error}")
