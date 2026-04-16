"""Analisador: classifica a intencao da mensagem recebida."""
import json
import logging
import re
from dataclasses import dataclass
from enum import Enum

import anthropic

from config import config
from agents.monitor import Interacao

log = logging.getLogger(__name__)


class Intencao(Enum):
    DUVIDA_TECNICA = "duvida_tecnica"
    PRAZO_ENTREGA = "prazo_entrega"
    TROCA_DEVOLUCAO = "troca_devolucao"
    RECLAMACAO = "reclamacao"
    CONFIRMACAO_PEDIDO = "confirmacao_pedido"
    OUTRO = "outro"


@dataclass
class Analise:
    intencao: Intencao
    resumo: str
    urgente: bool


_PROMPT_SISTEMA = """Voce classifica mensagens de compradores no Mercado Livre.
Responda SOMENTE com JSON no formato:
{"intencao": "<valor>", "resumo": "<uma frase>", "urgente": <true|false>}

Valores validos para intencao:
- duvida_tecnica
- prazo_entrega
- troca_devolucao
- reclamacao
- confirmacao_pedido
- outro
"""


def _extrair_json(texto: str) -> dict:
    """Extrai JSON mesmo se vier com texto ao redor."""
    texto = texto.strip()
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"JSON nao encontrado na resposta: {texto!r}")


class Analisador:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def analisar(self, interacao: Interacao) -> Analise:
        contexto = interacao.texto
        if interacao.historico:
            historico_fmt = "\n".join(f"- {m}" for m in interacao.historico[-5:])
            contexto = f"Historico:\n{historico_fmt}\n\nUltima mensagem: {interacao.texto}"

        msg = self._client.messages.create(
            model=config.MODEL_ANALISADOR,
            max_tokens=200,
            system=_PROMPT_SISTEMA,
            messages=[{"role": "user", "content": contexto}],
        )

        texto = msg.content[0].text if msg.content else ""
        log.debug(f"Analisador resposta: {texto!r}")

        try:
            dados = _extrair_json(texto)
            intencao = Intencao(dados.get("intencao", "outro"))
        except Exception as e:
            log.warning(f"Falha ao parsear analise ({e}), usando fallback outro")
            return Analise(intencao=Intencao.OUTRO, resumo=interacao.texto[:80], urgente=False)

        return Analise(
            intencao=intencao,
            resumo=dados.get("resumo", ""),
            urgente=dados.get("urgente", False),
        )
