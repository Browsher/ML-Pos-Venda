"""Testes do Formatador — saudacao baseada na hora com mock de datetime."""
import pytest
from unittest.mock import patch, MagicMock

from agents.formatador import _saudacao_horario, Formatador


@pytest.mark.parametrize("hora,esperado", [
    (5,  "Bom dia"),
    (8,  "Bom dia"),
    (11, "Bom dia"),
    (12, "Boa tarde"),
    (15, "Boa tarde"),
    (17, "Boa tarde"),
    (18, "Boa noite"),
    (21, "Boa noite"),
    (23, "Boa noite"),
    (0,  "Boa noite"),
    (4,  "Boa noite"),
])
def test_saudacao_horario(hora, esperado):
    with patch("agents.formatador.datetime") as mock_dt:
        mock_dt.now.return_value.hour = hora
        assert _saudacao_horario() == esperado


@pytest.fixture
def formatador():
    with patch("agents.formatador.anthropic.Anthropic"):
        f = Formatador()
        f._client = MagicMock()
        return f


def test_formatar_prefixo_bom_dia(formatador):
    formatador._client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Siga o manual de instalacao.")]
    )
    with patch("agents.formatador.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 9
        resultado = formatador.formatar("Siga o manual de instalacao.")
    assert resultado.startswith("Bom dia!")


def test_formatar_prefixo_boa_tarde(formatador):
    formatador._client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Seu pedido esta a caminho.")]
    )
    with patch("agents.formatador.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 14
        resultado = formatador.formatar("Seu pedido esta a caminho.")
    assert resultado.startswith("Boa tarde!")


def test_formatar_prefixo_boa_noite(formatador):
    formatador._client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Obrigado pelo contato.")]
    )
    with patch("agents.formatador.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 20
        resultado = formatador.formatar("Obrigado pelo contato.")
    assert resultado.startswith("Boa noite!")


def test_formatar_inclui_texto_corrigido(formatador):
    texto_corrigido = "Seu produto esta em transito."
    formatador._client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=texto_corrigido)]
    )
    with patch("agents.formatador.datetime") as mock_dt:
        mock_dt.now.return_value.hour = 10
        resultado = formatador.formatar("seu produto esta em transito")
    assert texto_corrigido in resultado
