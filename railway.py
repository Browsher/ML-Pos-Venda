"""Utilitario para atualizar variaveis de ambiente no Railway via GraphQL API."""
import logging
import httpx

log = logging.getLogger(__name__)

RAILWAY_API_TOKEN = "9165c94a-5cce-42f9-8ae3-160b38b290b1"
RAILWAY_PROJECT_ID = "b12551c3-7c69-4bb6-be0b-884141f51198"
RAILWAY_SERVICE_ID = "96a04753-9183-444c-8ec6-4742ddaf0323"
RAILWAY_ENVIRONMENT_ID = "c2cff01d-acc3-4fd4-a6de-9fc0c2d2bcf9"

_MUTATION = """
mutation upsertVariables($input: VariableCollectionUpsertInput!) {
    variableCollectionUpsert(input: $input)
}
"""


def atualizar_variavel(nome: str, valor: str) -> bool:
    """Atualiza uma variavel de ambiente no Railway via API GraphQL.
    Retorna True se bem-sucedido, False caso contrario.
    """
    variables = {
        "input": {
            "projectId": RAILWAY_PROJECT_ID,
            "serviceId": RAILWAY_SERVICE_ID,
            "environmentId": RAILWAY_ENVIRONMENT_ID,
            "variables": {nome: valor},
        }
    }
    try:
        resp = httpx.post(
            "https://backboard.railway.com/graphql/v2",
            json={"query": _MUTATION, "variables": variables},
            headers={
                "Authorization": f"Bearer {RAILWAY_API_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        ok = resp.is_success and "errors" not in resp.json()
        if ok:
            log.info(f"Railway: variavel {nome} atualizada com sucesso")
        else:
            log.error(f"Railway: falha ao atualizar {nome} — {resp.text}")
        return ok
    except Exception as e:
        log.error(f"Railway: erro ao chamar API — {e}")
        return False
