"""Monitor: busca perguntas e mensagens novas no Mercado Livre."""
import logging
from dataclasses import dataclass, field
from enum import Enum

from ml_client import MLClient

log = logging.getLogger(__name__)


class TipoInteracao(Enum):
    PERGUNTA = "pergunta"
    MENSAGEM = "mensagem"


@dataclass
class Interacao:
    tipo: TipoInteracao
    id: str               # question_id ou pack_id
    texto: str            # ultima mensagem ou pergunta
    item_id: str = ""     # MLB... do anuncio relacionado
    titulo_item: str = "" # titulo do anuncio
    ordem_id: str = ""    # numero do pedido (mensagens pos-venda)
    nome_comprador: str = ""
    historico: list[str] = field(default_factory=list)


class Monitor:
    def __init__(self, client: MLClient):
        self._client = client
        self._respondidas: set[str] = set()  # IDs ja processados nessa sessao

    def buscar_novas(self) -> list[Interacao]:
        interacoes: list[Interacao] = []
        try:
            interacoes.extend(self._buscar_perguntas())
        except Exception as e:
            log.error(f"Erro ao buscar perguntas: {e}")
        return interacoes

    def _buscar_perguntas(self) -> list[Interacao]:
        perguntas = self._client.listar_perguntas_novas()
        resultado = []
        for p in perguntas:
            qid = str(p["id"])
            if qid in self._respondidas:
                continue
            from_data = p.get("from", {})
            nome = from_data.get("nickname", "")
            item_id = p.get("item_id", "")
            resultado.append(
                Interacao(
                    tipo=TipoInteracao.PERGUNTA,
                    id=qid,
                    texto=p["text"],
                    item_id=item_id,
                    nome_comprador=nome,
                )
            )
        return resultado

    def marcar_processada(self, interacao_id: str) -> None:
        self._respondidas.add(interacao_id)
