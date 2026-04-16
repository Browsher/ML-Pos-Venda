"""Gerador: usa Claude para criar mensagem personalizada de follow-up."""
import logging
from pathlib import Path

import anthropic
from config import config

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_PROMPT_SISTEMA = """Voce gera mensagens de follow-up para compradores no Mercado Livre.
Siga o template fornecido. Seja cordial, breve e profissional.
Responda APENAS com o texto da mensagem, sem explicacoes.
NUNCA invente informacoes que nao foram fornecidas."""


class Gerador:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def gerar(self, evento: str, dados: dict) -> str:
        template = self._carregar_template(evento)
        prompt = f"{template}\n\nDados do pedido:\n{self._formatar_dados(dados)}"

        msg = self._client.messages.create(
            model=config.MODEL_ANALISADOR,
            max_tokens=300,
            system=_PROMPT_SISTEMA,
            messages=[{"role": "user", "content": prompt}],
        )
        texto = msg.content[0].text.strip() if msg.content else ""
        log.info(f"Mensagem gerada para evento={evento}: {texto[:60]}...")
        return texto

    def _carregar_template(self, evento: str) -> str:
        path = TEMPLATES_DIR / f"{evento}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"Gere uma mensagem de follow-up para o evento: {evento}"

    def _formatar_dados(self, dados: dict) -> str:
        return "\n".join(f"- {k}: {v}" for k, v in dados.items() if v)
