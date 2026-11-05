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


def test_las_respuestas_vacias_se_reintentan_una_sola_vez(monkeypatch):
    """El cupo gratuito es de 50 pedidos/día: no se lo puede quemar reintentando."""
    client = _client([None, None, None], monkeypatch)

    with pytest.raises(ValueError, match="intentos"):
        generator.generate_response([{"role": "user", "content": "hola"}], max_retries=3)

    budgets = [c["max_tokens"] for c in client.completions.calls]
    assert budgets == [4000, 8000], "un solo reintento con el doble de presupuesto"


def test_agota_los_intentos_y_levanta_value_error(monkeypatch):
    client = _client([None, None, None], monkeypatch)

    with pytest.raises(ValueError, match="intentos"):
        generator.generate_response([{"role": "user", "content": "hola"}], max_retries=2)

    assert len(client.completions.calls) == 2, "vacío: 2 pedidos, no 3"


def test_los_errores_del_proveedor_tambien_se_reintentan(monkeypatch):
    class _Boom(_FakeCompletions):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise RuntimeError("Error code: 503 - upstream exploded")
            return _FakeResponse("ok")

    client = _FakeClient([])
    client.completions = _Boom([])
    monkeypatch.setattr(generator, "get_client", lambda: client)

    assert generator.generate_response([{"role": "user", "content": "hola"}]) == "ok"


def test_el_rate_limit_no_se_reintenta_y_avisa_del_cupo(monkeypatch):
    """Un 429 quema cupo si se repite: hay que cortar de una."""
    class _RateLimited(_FakeCompletions):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            raise RuntimeError(
                "Error code: 429 - {'error': {'message': "
                "'Rate limit exceeded: free-models-per-day.'"
            )

    client = _FakeClient([])
    client.completions = _RateLimited([])
    monkeypatch.setattr(generator, "get_client", lambda: client)

    with pytest.raises(generator.RateLimitError, match="cupo diario"):
        generator.generate_response([{"role": "user", "content": "hola"}], max_retries=2)

    assert len(client.completions.calls) == 1, "un 429 no debe reintentarse"


def test_modo_economico_no_gasta_pedidos(monkeypatch):
    """Con MODO_ECONOMICO el análisis no hace NINGÚN pedido al modelo."""
    from IA_rag import cv_analyzer

    monkeypatch.setattr(cv_analyzer, "NARRATIVE_DISABLED", True)
    pedidos = []
    monkeypatch.setattr(
        cv_analyzer, "generate_response",
        lambda *a, **k: pedidos.append(1) or '{"summary": "x"}',
    )
    cv_data = {
        "cv": {"name": "Ana", "about": "Perfil"},
        "experience": [], "skills": [], "education": [],
        "achievements": [], "programs": [], "languages": [],
    }

    assert cv_analyzer._llm_narrative(cv_data, [("Contenido", [])], "Python") is None
    assert pedidos == []
