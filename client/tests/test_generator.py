"""Tests del reintento con presupuesto ampliado en `generate_response`.

Los modelos que razonan antes de responder consumen tokens antes de escribir
nada; si el presupuesto se agota, la respuesta llega vacía. El generador debe
reintentar con el doble de tokens en lugar de repetir con el mismo límite.
"""

import pytest

from IA_rag import generator


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    """Devuelve las respuestas guionizadas y registra los `max_tokens` usados."""

    def __init__(self, script):
        self._script = list(script)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._script:
            raise AssertionError("se hicieron más pedidos de los guionizados")
        return _FakeResponse(self._script.pop(0))


class _FakeClient:
    def __init__(self, script):
        self.completions = _FakeCompletions(script)
        self.chat = self


@pytest.fixture(autouse=True)
def _sin_esperas(monkeypatch):
    monkeypatch.setattr(generator.time, "sleep", lambda _s: None)


def _client(script, monkeypatch):
    client = _FakeClient(script)
    monkeypatch.setattr(generator, "get_client", lambda: client)
    return client


def test_presupuesto_por_defecto_duplica_si_la_respuesta_vacia(monkeypatch):
    client = _client([None, "respuesta del modelo"], monkeypatch)

    result = generator.generate_response(
        [{"role": "user", "content": "hola"}], max_retries=2
    )

    assert result == "respuesta del modelo"
    budgets = [c["max_tokens"] for c in client.completions.calls]
    assert budgets[0] == 4000, "el presupuesto inicial debe ser 4000"
    assert budgets[1] == budgets[0] * 2, "un intento vacío debe duplicar el presupuesto"


def test_respuesta_en_blanco_tambien_se_reintenta(monkeypatch):
    client = _client(["   ", "contenido"], monkeypatch)

    result = generator.generate_response([{"role": "user", "content": "hola"}])

    assert result == "contenido"
    assert len(client.completions.calls) == 2


def test_presupuesto_se_limita_en_16000(monkeypatch):
    client = _client([None, None, None, "al final"], monkeypatch)

    generator.generate_response([{"role": "user", "content": "hola"}], max_retries=3)

    budgets = [c["max_tokens"] for c in client.completions.calls]
    assert budgets == [4000, 8000, 16000, 16000]


def test_agota_los_intentos_y_levanta_value_error(monkeypatch):
    client = _client([None, None, None], monkeypatch)

    with pytest.raises(ValueError, match="3 intentos"):
        generator.generate_response([{"role": "user", "content": "hola"}], max_retries=2)

    assert len(client.completions.calls) == 3


def test_los_errores_del_proveedor_tambien_se_reintentan(monkeypatch):
    class _Boom(_FakeCompletions):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise RuntimeError("429 rate limited")
            return _FakeResponse("ok")

    client = _FakeClient([])
    client.completions = _Boom([])
    monkeypatch.setattr(generator, "get_client", lambda: client)

    assert generator.generate_response([{"role": "user", "content": "hola"}]) == "ok"
