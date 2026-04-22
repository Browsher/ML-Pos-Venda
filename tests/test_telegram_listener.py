"""Testes do TelegramListener — parsing de /r e casos de erro."""
import pytest
from unittest.mock import MagicMock, patch


def _make_listener(pendentes_mock=None, formatador_mock=None):
    """Cria TelegramListener com todas as dependencias mockadas."""
    from agents.telegram_listener import TelegramListener

    ml_mock = MagicMock()

    with (
        patch("agents.telegram_listener.Memoria"),
        patch("agents.telegram_listener.Pendentes"),
        patch("agents.telegram_listener.Formatador"),
        patch("agents.telegram_listener.httpx.post"),
        patch("agents.telegram_listener.httpx.get"),
    ):
        listener = TelegramListener(ml_mock)

    # Substitui instancias por mocks controlados
    if pendentes_mock is not None:
        listener._pendentes = pendentes_mock
    if formatador_mock is not None:
        listener._formatador = formatador_mock

    # Mock do envio para nao chamar Telegram real
    listener._enviar_telegram = MagicMock()
    return listener


def test_processar_resposta_formato_invalido_menos_de_3_partes():
    listener = _make_listener()
    resultado = listener._processar_resposta("/r")
    assert resultado == 0
    listener._enviar_telegram.assert_called_once()
    msg = listener._enviar_telegram.call_args[0][0]
    assert "Formato invalido" in msg


def test_processar_resposta_formato_invalido_sem_texto():
    listener = _make_listener()
    resultado = listener._processar_resposta("/r 1")
    assert resultado == 0
    listener._enviar_telegram.assert_called_once()


def test_processar_resposta_id_nao_numerico():
    listener = _make_listener()
    resultado = listener._processar_resposta("/r abc minha resposta aqui")
    assert resultado == 0
    listener._enviar_telegram.assert_called_once()
    msg = listener._enviar_telegram.call_args[0][0]
    assert "abc" in msg or "inv" in msg.lower()


def test_processar_resposta_id_nao_encontrado_nas_pendentes():
    pendentes_mock = MagicMock()
    pendentes_mock.buscar_por_codigo.return_value = None
    listener = _make_listener(pendentes_mock=pendentes_mock)

    resultado = listener._processar_resposta("/r 999 resposta qualquer")
    assert resultado == 0
    pendentes_mock.buscar_por_codigo.assert_called_once_with(999)
    listener._enviar_telegram.assert_called_once()
    msg = listener._enviar_telegram.call_args[0][0]
    assert "999" in msg


def test_processar_resposta_valido_posta_no_ml():
    pendentes_mock = MagicMock()
    pendentes_mock.buscar_por_codigo.return_value = (
        "pack_123",
        {
            "tipo": "mensagem",
            "texto": "Meu produto chegou errado",
            "intencao": "reclamacao",
            "nome_comprador": "Joao",
        },
    )

    formatador_mock = MagicMock()
    formatador_mock.formatar.return_value = "Boa tarde! Vamos resolver isso."

    listener = _make_listener(
        pendentes_mock=pendentes_mock,
        formatador_mock=formatador_mock,
    )
    listener._memoria = MagicMock()
    listener._memoria.total.return_value = 5
    listener._ml.responder_mensagem = MagicMock()

    resultado = listener._processar_resposta("/r 42 Vamos resolver isso")
    assert resultado == 1
    listener._ml.responder_mensagem.assert_called_once_with(
        "pack_123", "Boa tarde! Vamos resolver isso."
    )
    pendentes_mock.remover.assert_called_once_with("pack_123")


def test_processar_resposta_valido_pergunta_usa_responder_pergunta():
    pendentes_mock = MagicMock()
    pendentes_mock.buscar_por_codigo.return_value = (
        "q_456",
        {
            "tipo": "pergunta",
            "texto": "Qual a voltagem?",
            "intencao": "duvida_tecnica",
            "nome_comprador": "",
        },
    )

    formatador_mock = MagicMock()
    formatador_mock.formatar.return_value = "Bom dia! E bivolt."

    listener = _make_listener(
        pendentes_mock=pendentes_mock,
        formatador_mock=formatador_mock,
    )
    listener._memoria = MagicMock()
    listener._memoria.total.return_value = 3
    listener._ml.responder_pergunta = MagicMock()

    resultado = listener._processar_resposta("/r 7 E bivolt.")
    assert resultado == 1
    listener._ml.responder_pergunta.assert_called_once_with(
        "q_456", "Bom dia! E bivolt."
    )
