"""Testes do webhook_server — validacao user_id e roteamento de topics."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient


def _make_app():
    """Cria a FastAPI app com lifespan mockado para evitar instanciar agentes reais."""
    orq_mock = MagicMock()
    orq_mock.ciclo = MagicMock()
    orq_mock.processar_mensagem_pack = MagicMock(return_value=True)
    orq_mock.telegram_listener = MagicMock()

    import webhook_server as ws
    ws.orq = orq_mock

    return ws.app, orq_mock


@pytest.fixture
def client_mocks():
    app, orq_mock = _make_app()
    with patch("webhook_server.Orquestrador", return_value=orq_mock):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, orq_mock


def test_health_retorna_ok(client_mocks):
    client, _ = client_mocks
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_webhook_rejeita_user_id_diferente(client_mocks):
    client, _ = client_mocks
    with patch("webhook_server.config") as mock_cfg:
        mock_cfg.ML_SELLER_ID = "123456"
        resp = client.post("/webhook", json={"user_id": 999999, "topic": "questions", "resource": "/questions/1"})
    assert resp.status_code == 403


def test_webhook_aceita_user_id_correto(client_mocks):
    client, orq_mock = client_mocks
    with patch("webhook_server.config") as mock_cfg:
        mock_cfg.ML_SELLER_ID = "123456"
        resp = client.post("/webhook", json={"user_id": 123456, "topic": "questions", "resource": "/questions/1"})
    assert resp.status_code == 200
    assert resp.json().get("received") is True


def test_webhook_deduplica_por_id(client_mocks):
    import webhook_server as ws
    client, orq_mock = client_mocks
    ws._notificacoes_vistas.clear()
    payload = {"user_id": 123456, "topic": "questions", "resource": "/questions/1", "_id": "notif-abc-123"}
    with patch("webhook_server.config") as mock_cfg:
        mock_cfg.ML_SELLER_ID = "123456"
        resp1 = client.post("/webhook", json=payload)
        resp2 = client.post("/webhook", json=payload)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert orq_mock.ciclo.call_count == 1


def test_webhook_sem_id_nao_deduplica(client_mocks):
    import webhook_server as ws
    client, orq_mock = client_mocks
    ws._notificacoes_vistas.clear()
    orq_mock.ciclo.reset_mock()
    payload = {"user_id": 123456, "topic": "questions", "resource": "/questions/1"}
    with patch("webhook_server.config") as mock_cfg:
        mock_cfg.ML_SELLER_ID = "123456"
        client.post("/webhook", json=payload)
        client.post("/webhook", json=payload)
    assert orq_mock.ciclo.call_count == 2
