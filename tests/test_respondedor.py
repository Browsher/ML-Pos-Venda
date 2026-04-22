"""Testes do Respondedor — parsing de resposta e logica de confianca."""
import pytest
from unittest.mock import MagicMock, patch

from agents.respondedor import Respondedor, Resposta
from agents.monitor import Interacao, TipoInteracao
from agents.analisador import Analise, Intencao


def _make_analise(intencao=Intencao.DUVIDA_TECNICA, urgente=False):
    return Analise(intencao=intencao, resumo="teste", urgente=urgente)


def _make_interacao():
    return Interacao(tipo=TipoInteracao.PERGUNTA, id="q1", texto="Como instalar?")


@pytest.fixture
def respondedor():
    ml_mock = MagicMock()
    with patch("agents.respondedor.anthropic.Anthropic"):
        r = Respondedor(ml_mock)
        r._claude = MagicMock()
        return r


def test_parsear_resposta_com_confianca_alta(respondedor):
    texto_bruto = "A instalacao e simples, siga o manual.\nCONFIANCA: 0.9"
    resposta = respondedor._parsear(texto_bruto)
    assert resposta.confianca == 0.9
    assert "CONFIANCA" not in resposta.texto
    assert "A instalacao" in resposta.texto


def test_parsear_resposta_sem_confianca_usa_default(respondedor):
    from config import config
    texto_bruto = "Vou verificar e retorno em breve."
    resposta = respondedor._parsear(texto_bruto)
    # Sem CONFIANCA no texto, usa config.CONFIANCA_MINIMA - 0.1
    assert resposta.confianca == config.CONFIANCA_MINIMA - 0.1


def test_nao_posta_se_confianca_baixa(respondedor):
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Nao tenho certeza.\nCONFIANCA: 0.4")]
    )
    resposta = respondedor.gerar_e_postar(_make_interacao(), _make_analise(), "")
    assert resposta.postada is False
    respondedor._ml.responder_pergunta.assert_not_called()


def test_posta_se_confianca_alta(respondedor):
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="E compativel sim!\nCONFIANCA: 0.95")]
    )
    resposta = respondedor.gerar_e_postar(_make_interacao(), _make_analise(), "")
    assert resposta.postada is True
    respondedor._ml.responder_pergunta.assert_called_once()


def test_posta_se_confianca_alta_verifica_argumentos(respondedor):
    """Verifica que responder_pergunta recebe o id e texto corretos."""
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="E compativel sim!\nCONFIANCA: 0.95")]
    )
    interacao = Interacao(tipo=TipoInteracao.PERGUNTA, id="q42", texto="Funciona com DVR?")
    respondedor.gerar_e_postar(interacao, _make_analise(), "")
    respondedor._ml.responder_pergunta.assert_called_once_with("q42", "E compativel sim!")


def test_posta_se_confianca_alta_valor_exato(respondedor):
    """A confianca deve ser exatamente 0.95, nao apenas >= 0.75."""
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Resposta certa.\nCONFIANCA: 0.95")]
    )
    resposta = respondedor.gerar_e_postar(_make_interacao(), _make_analise(), "")
    assert resposta.confianca == 0.95


def test_gerar_e_postar_mensagem_usa_responder_mensagem(respondedor):
    """Quando tipo e MENSAGEM, deve chamar responder_mensagem em vez de responder_pergunta."""
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Entendido, vamos resolver.\nCONFIANCA: 0.90")]
    )
    interacao = Interacao(tipo=TipoInteracao.MENSAGEM, id="pack_99", texto="Produto com defeito")
    respondedor.gerar_e_postar(interacao, _make_analise(), "")
    respondedor._ml.responder_mensagem.assert_called_once_with(
        "pack_99", "Entendido, vamos resolver."
    )
    respondedor._ml.responder_pergunta.assert_not_called()


def test_gerar_e_postar_mensagem_nao_posta_com_confianca_baixa(respondedor):
    """Com confianca baixa e tipo MENSAGEM, nao deve postar."""
    respondedor._claude.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Nao sei.\nCONFIANCA: 0.3")]
    )
    interacao = Interacao(tipo=TipoInteracao.MENSAGEM, id="pack_77", texto="Pergunta")
    resposta = respondedor.gerar_e_postar(interacao, _make_analise(), "")
    assert resposta.postada is False
    respondedor._ml.responder_mensagem.assert_not_called()
