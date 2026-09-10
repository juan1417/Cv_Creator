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
    max_tokens: int = 2000,
    response_format: dict | None = None,
    max_retries: int = 2,
) -> str:
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
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            if response.choices and response.choices[0].message.content is not None:
                return response.choices[0].message.content
            last_error = "Empty response from model"
            logger.warning(f"Attempt {attempt + 1}: Model returned empty response, retrying...")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Attempt {attempt + 1}: {last_error}")
        
        if attempt < max_retries:
            time.sleep(1)  # Wait before retry
    
    raise ValueError(f"El modelo no respondio despues de {max_retries + 1} intentos: {last_error}")
