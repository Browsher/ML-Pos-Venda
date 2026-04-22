"""Testes do Enviador — logica de follow-up com mocks."""
from unittest.mock import MagicMock

from agents.enviador import Enviador


def _make_enviador(pack_id, order_id):
    env = Enviador.__new__(Enviador)
    env._ml = MagicMock()
    env._gerador = MagicMock()
    env._enviados = MagicMock()

    env._enviados.verificar_e_marcar.return_value = False
    env._ml.buscar_pedido.return_value = {
        "pack_id": pack_id,
        "id": order_id,
        "buyer": {"nickname": "COMPRADOR_TESTE"},
        "order_items": [{"item": {"title": "Camera de Seguranca"}}],
    }
    env._ml.buscar_cap_disponivel.return_value = True
    env._gerador.gerar.return_value = "Mensagem teste"
    return env


def test_processar_compra_sem_pack_id_usa_order_id():
    env = _make_enviador(pack_id=None, order_id="777")
    env.processar_compra("777")
    env._ml.enviar_followup.assert_called_once()
    args, _ = env._ml.enviar_followup.call_args
    assert args[0] == "777"


def test_processar_compra_com_pack_id_usa_pack_id():
    env = _make_enviador(pack_id=888, order_id="777")
    env.processar_compra("777")
    env._ml.enviar_followup.assert_called_once()
    args, _ = env._ml.enviar_followup.call_args
    assert args[0] == "888"


def test_processar_compra_ja_enviado_nao_reenvia():
    env = _make_enviador(pack_id=888, order_id="777")
    env._enviados.verificar_e_marcar.return_value = True
    env.processar_compra("777")
    env._ml.enviar_followup.assert_not_called()
