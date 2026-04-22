"""Testes do Especialista — selecao de base de conhecimento por intencao."""
import pytest
from unittest.mock import patch, MagicMock


def _make_especialista(arquivos: dict):
    """
    Cria Especialista com leitura de arquivos mockada.
    arquivos: {nome: conteudo_str}  (sem extensao)
    """
    from agents.especialista import Especialista

    def fake_carregar(self, nome: str) -> str:
        return arquivos.get(nome, "")

    memoria_mock = MagicMock()
    memoria_mock.formatar_contexto.return_value = ""

    with patch("agents.especialista.Memoria", return_value=memoria_mock):
        esp = Especialista()

    # Substitui metodo de carregamento para nao tocar disco
    esp._carregar = fake_carregar.__get__(esp, type(esp))
    # Limpa cache para forcar uso do fake
    esp._cache = {}
    return esp


def test_contexto_troca_devolucao_inclui_garantia():
    esp = _make_especialista({
        "produtos": "catalogo de cameras",
        "faq": "perguntas frequentes",
        "garantia": "POLITICA DE GARANTIA E DEVOLUCAO",
        "instalacao": "guia de instalacao",
    })
    contexto = esp.contexto_para("troca_devolucao")
    assert "POLITICA DE GARANTIA E DEVOLUCAO" in contexto


def test_contexto_reclamacao_inclui_garantia():
    esp = _make_especialista({
        "produtos": "catalogo",
        "faq": "faq",
        "garantia": "GARANTIA_CONTEUDO",
    })
    contexto = esp.contexto_para("reclamacao")
    assert "GARANTIA_CONTEUDO" in contexto


def test_contexto_duvida_tecnica_inclui_instalacao():
    esp = _make_especialista({
        "produtos": "catalogo",
        "faq": "faq",
        "instalacao": "GUIA DE INSTALACAO DETALHADO",
    })
    contexto = esp.contexto_para("duvida_tecnica")
    assert "GUIA DE INSTALACAO DETALHADO" in contexto


def test_contexto_duvida_tecnica_nao_inclui_garantia():
    esp = _make_especialista({
        "produtos": "catalogo",
        "faq": "faq",
        "garantia": "GARANTIA_EXCLUSIVA",
        "instalacao": "instalacao",
    })
    contexto = esp.contexto_para("duvida_tecnica")
    assert "GARANTIA_EXCLUSIVA" not in contexto


def test_contexto_troca_devolucao_nao_inclui_instalacao():
    esp = _make_especialista({
        "produtos": "catalogo",
        "faq": "faq",
        "garantia": "garantia",
        "instalacao": "INSTALACAO_EXCLUSIVA",
    })
    contexto = esp.contexto_para("troca_devolucao")
    assert "INSTALACAO_EXCLUSIVA" not in contexto


def test_contexto_sempre_inclui_produtos_e_faq():
    esp = _make_especialista({
        "produtos": "CATALOGO_PRODUTOS",
        "faq": "FAQ_CONTEUDO",
    })
    for intencao in ("prazo_entrega", "confirmacao_pedido", "outro"):
        contexto = esp.contexto_para(intencao)
        assert "CATALOGO_PRODUTOS" in contexto
        assert "FAQ_CONTEUDO" in contexto


def test_contexto_arquivos_ausentes_nao_falha():
    esp = _make_especialista({})  # nenhum arquivo disponivel
    contexto = esp.contexto_para("duvida_tecnica")
    # Deve retornar string (vazia ou nao) sem lancar excecao
    assert isinstance(contexto, str)
