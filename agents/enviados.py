"""Enviados: rastreia eventos de follow-up ja processados para evitar duplicatas."""
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

ARQUIVO = Path(__file__).parent.parent / "data" / "enviados.json"


class Enviados:
    def ja_enviou(self, order_id: str, evento: str) -> bool:
        dados = self._carregar()
        return f"{order_id}_{evento}" in dados

    def marcar(self, order_id: str, evento: str) -> None:
        dados = self._carregar()
        dados[f"{order_id}_{evento}"] = True
        ARQUIVO.parent.mkdir(exist_ok=True)
        ARQUIVO.write_text(json.dumps(dados, indent=2), encoding="utf-8")

    def _carregar(self) -> dict:
        if ARQUIVO.exists():
            try:
                return json.loads(ARQUIVO.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}
