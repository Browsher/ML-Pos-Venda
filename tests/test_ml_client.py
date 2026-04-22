"""Testes para MLClient — metodos de fallback e consultas."""
import pytest
from unittest.mock import patch, MagicMock

from ml_client import MLClient


def _make_client():
    """Cria MLClient sem depender de variaveis de ambiente."""
    cliente = MLClient()
    cliente._access_token = "fake_token"
    return cliente


def _make_resp(status_code: int, json_data: dict = None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        mock.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return mock


# --- Testes de retry em 401 ---

def test_get_renova_token_em_401():
    """_get deve chamar _renovar_token e repetir requisicao quando recebe 401."""
    cliente = _make_client()
    resp_401 = _make_resp(401)
    resp_ok  = _make_resp(200, {"ok": True})

    with patch.object(cliente._http, "get", side_effect=[resp_401, resp_ok]):
        with patch.object(cliente, "_renovar_token") as mock_renovar:
            result = cliente._get("/some/path")

    mock_renovar.assert_called_once()
    assert result == {"ok": True}


def test_post_renova_token_em_401():
    """_post deve chamar _renovar_token e repetir requisicao quando recebe 401."""
    cliente = _make_client()
    resp_401 = _make_resp(401)
    resp_ok  = _make_resp(200, {"created": True})

    with patch.object(cliente._http, "post", side_effect=[resp_401, resp_ok]):
        with patch.object(cliente, "_renovar_token") as mock_renovar:
            result = cliente._post("/some/path", {"key": "val"})

    mock_renovar.assert_called_once()
    assert result == {"created": True}


# --- Testes de truncamento de texto ---

def test_responder_mensagem_trunca_acima_de_350_chars():
    cliente = _make_client()
    texto_longo = "x" * 400

    resp_ok = _make_resp(200, {"id": "msg1"})
    resp_ok.raise_for_status = MagicMock()

    with patch.object(cliente._http, "post", return_value=resp_ok) as mock_post:
        cliente.responder_mensagem("pack1", texto_longo)

    corpo = mock_post.call_args.kwargs["json"]
    assert len(corpo["text"]) <= 350
    assert corpo["text"].endswith("...")


def test_responder_mensagem_nao_trunca_texto_curto():
    cliente = _make_client()
    texto_curto = "Texto normal de resposta."

    resp_ok = _make_resp(200, {"id": "msg2"})
    resp_ok.raise_for_status = MagicMock()

    with patch.object(cliente._http, "post", return_value=resp_ok) as mock_post:
        cliente.responder_mensagem("pack1", texto_curto)

    corpo = mock_post.call_args.kwargs["json"]
    assert corpo["text"] == texto_curto


def test_responder_pergunta_trunca_acima_de_2000_chars():
    cliente = _make_client()
    texto_longo = "p" * 2100

    resp_ok = _make_resp(200, {"id": "ans1"})
    resp_ok.raise_for_status = MagicMock()

    with patch.object(cliente._http, "post", return_value=resp_ok) as mock_post:
        cliente.responder_pergunta("12345", texto_longo)

    corpo = mock_post.call_args.kwargs["json"]
    assert len(corpo["text"]) <= 2000
    assert corpo["text"].endswith("...")
