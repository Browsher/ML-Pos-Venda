"""Enviador: processa eventos do ML e envia mensagens de follow-up."""
import logging
from ml_client import MLClient
from agents.gerador import Gerador
from agents.enviados import Enviados

log = logging.getLogger(__name__)


class Enviador:
    def __init__(self):
        self._ml = MLClient()
        self._gerador = Gerador()
        self._enviados = Enviados()

    def processar_compra(self, order_id: str) -> None:
        if self._enviados.verificar_e_marcar(order_id, "compra"):
            log.info(f"Compra {order_id} ja processada, ignorando")
            return
        try:
            pedido = self._ml.buscar_pedido(order_id)
            pack_id = pedido.get("pack_id")
            if not pack_id:
                log.info(f"Compra {order_id} sem pack_id — Action Guide nao suporta order_id, pulando follow-up")
                return
            pack_id_str = str(pack_id)
            if not self._ml.buscar_cap_disponivel(pack_id_str):
                log.warning(f"CAP indisponivel para pack={pack_id_str} (compra {order_id}) — abortando")
                return
            dados = self._extrair_dados_pedido(pedido, order_id)
            mensagem = self._gerador.gerar("compra", dados)
            self._ml.enviar_followup(pack_id_str, mensagem)
            log.info(f"Mensagem de compra enviada para order={order_id}")
        except Exception as e:
            log.error(f"Erro ao processar compra {order_id}: {e}")

    def processar_envio(self, order_id: str, shipment_id: str) -> None:
        if self._enviados.verificar_e_marcar(order_id, "envio"):
            log.info(f"Envio {order_id} ja processado, ignorando")
            return
        try:
            pedido = self._ml.buscar_pedido(order_id)
            pack_id = pedido.get("pack_id")
            if not pack_id:
                log.info(f"Envio {order_id} sem pack_id — Action Guide nao suporta order_id, pulando follow-up")
                return
            pack_id_str = str(pack_id)
            if not self._ml.buscar_cap_disponivel(pack_id_str):
                log.warning(f"CAP indisponivel para pack={pack_id_str} (envio {order_id}) — abortando")
                return
            dados = self._extrair_dados_pedido(pedido, order_id)
            mensagem = self._gerador.gerar("envio", dados)
            self._ml.enviar_followup(pack_id_str, mensagem)
            log.info(f"Mensagem de envio enviada para order={order_id}")
        except Exception as e:
            log.error(f"Erro ao processar envio {order_id}: {e}")

    def processar_entrega(self, order_id: str) -> None:
        if self._enviados.verificar_e_marcar(order_id, "entrega"):
            log.info(f"Entrega {order_id} ja processada, ignorando")
            return
        try:
            pedido = self._ml.buscar_pedido(order_id)
            pack_id = pedido.get("pack_id")
            if not pack_id:
                log.info(f"Entrega {order_id} sem pack_id — Action Guide nao suporta order_id, pulando follow-up")
                return
            pack_id_str = str(pack_id)
            cap_other = self._ml.buscar_cap_disponivel(pack_id_str, "OTHER")
            cap_invoice = self._ml.buscar_cap_disponivel(pack_id_str, "SEND_INVOICE_LINK")
            if not cap_other and not cap_invoice:
                log.warning(f"CAP indisponivel para pack={pack_id_str} (entrega {order_id}) — abortando")
                return
            option_id = "OTHER" if cap_other else "SEND_INVOICE_LINK"
            dados = self._extrair_dados_pedido(pedido, order_id)
            mensagem = self._gerador.gerar("entrega", dados)
            self._ml.enviar_followup(pack_id_str, mensagem, option_id=option_id)
            log.info(f"Mensagem de entrega enviada para order={order_id} option_id={option_id}")
        except Exception as e:
            log.error(f"Erro ao processar entrega {order_id}: {e}")

    def _extrair_dados_pedido(self, pedido: dict, order_id: str) -> dict:
        itens = pedido.get("order_items", [])
        produto = itens[0].get("item", {}).get("title", "") if itens else ""
        nome_comprador = self._ml.buscar_nome_comprador(order_id, pedido)
        return {
            "nome_comprador": nome_comprador,
            "produto": produto,
            "order_id": str(pedido.get("id", "")),
        }
