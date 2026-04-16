# Pos-Venda ML

Sistema unificado com dois subsistemas no Mercado Livre. Nicho: cameras de seguranca e acessorios.

1. **Pos-venda** — responde perguntas e mensagens de compradores (com supervisao humana via Telegram)
2. **Follow-up** — envia mensagens automaticas em cada etapa do pedido (compra, envio, entrega)

## Comandos

```bash
# Iniciar servidor webhook (Railway)
uv run python main.py

# Testes
uv run python -m pytest tests/ -v
```

## Stack

- Python 3.12+, uv
- Anthropic SDK (claude-haiku-4-5)
- FastAPI + uvicorn (webhook server)
- httpx (chamadas API ML e Telegram)
- python-dotenv

## Regra de Uso de Agentes Claude

**OBRIGATORIO — sem excecao:**

O contexto principal atua como **orquestrador**. Ele NUNCA implementa nem analisa diretamente.
Ele coordena os agentes especializados e apresenta o resultado ao usuario.

### Fluxo obrigatorio

```
Usuario pede algo
      ↓
Orquestrador (contexto principal)
      ↓
      ├── ANALISAR / INVESTIGAR / PLANEJAR → Explore (subagent_type=Explore)
      │         retorna analise/plano
      │
      └── IMPLEMENTAR / CORRIGIR / EXECUTAR → Plan ou Agent dev
                retorna codigo pronto
```

### Regras

- NUNCA implementar diretamente no contexto principal
- NUNCA analisar codigo sem usar o agente Explore primeiro
- SEMPRE usar subagent_type=Explore para investigar
- SEMPRE usar subagent_type=Plan ou Agent para implementar
- O orquestrador apenas coordena e apresenta resultados

| Tarefa | Agente correto |
|--------|----------------|
| Explorar codigo, entender fluxo, investigar bug | `subagent_type=Explore` |
| Planejar nova feature ou mudanca de arquitetura | `subagent_type=Plan` |
| Implementar feature, corrigir bug, escrever teste | `subagent_type=Plan` com isolamento |
| Qualquer duvida sobre o que um modulo faz | `subagent_type=Explore` |

## Agentes do Sistema (codigo)

### Pos-venda
| Agente | Arquivo | Funcao |
|--------|---------|--------|
| Orquestrador | agents/orquestrador.py | Coordena perguntas e mensagens |
| Monitor | agents/monitor.py | Busca perguntas novas via API ML |
| Analisador | agents/analisador.py | Classifica intencao com Claude |
| Especialista | agents/especialista.py | Carrega base de conhecimento relevante |
| Respondedor | agents/respondedor.py | Gera resposta com Claude e posta via API ML |
| Escalador | agents/escalador.py | Notifica humano via Telegram se confianca baixa |
| TelegramListener | agents/telegram_listener.py | Recebe comandos do Telegram |
| Formatador | agents/formatador.py | Polida resposta (saudacao + horario) |
| Pendentes | agents/pendentes.py | Persiste interacoes aguardando resposta |
| Memoria | agents/memoria.py | Persiste respostas aprovadas para aprendizado |

### Follow-up
| Agente | Arquivo | Funcao |
|--------|---------|--------|
| Enviador | agents/enviador.py | Processa eventos compra/envio/entrega |
| Gerador | agents/gerador.py | Gera mensagens com Claude + templates |
| Enviados | agents/enviados.py | Persiste eventos processados (evita duplicatas) |

## Fluxo Pos-venda

```
Webhook (questions/messages)
    → Orquestrador → Monitor → Analisador → Especialista → Respondedor
        confianca >= 0.75 → posta no ML automaticamente
        confianca < 0.75  → Escalador → Telegram → /r <id> resposta
```

## Fluxo Follow-up

```
Webhook orders_v2 (paid)      → Enviador.processar_compra()
Webhook shipments (shipped)   → Enviador.processar_envio()
Webhook shipments (delivered) → Enviador.processar_entrega()
    → Gerador cria mensagem com Claude + template
    → MLClient.enviar_followup() posta na conversa
    → Enviados.marcar() salva em data/enviados.json
```

## Comandos Telegram

| Comando | Funcao |
|---------|--------|
| `/r <id> <resposta>` | Responde uma pendente no ML |
| `/listar` | Lista todas as pendentes |
| `/status` | Resumo de pendentes e base de conhecimento |
| `/cancelar <id>` | Remove pendente sem responder |
| `/comandos` | Mostra esta lista |

Apenas mensagens do `TELEGRAM_CHAT_ID` configurado sao processadas.

## Configuracao

Variaveis de ambiente necessarias:
- `ANTHROPIC_API_KEY`
- `ML_CLIENT_ID`, `ML_CLIENT_SECRET`, `ML_REFRESH_TOKEN`, `ML_SELLER_ID`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Base de Conhecimento

Em `base_conhecimento/` (preencher antes de producao):
- `produtos.md` — specs dos produtos
- `faq.md` — perguntas frequentes
- `garantia.md` — politica de garantia e devolucao
- `instalacao.md` — guia de instalacao

Em `templates/` (follow-up):
- `compra.md`, `envio.md`, `entrega.md` — templates das mensagens automaticas

## Autenticacao ML

OAuth2 com refresh token. Renovacao automatica em qualquer 401.
Rota `/callback` no Railway troca o code OAuth e atualiza os tokens via Railway GraphQL API.

## Deploy (Railway)

1. Crie projeto no Railway, conecte este repositorio
2. Configure as variaveis de ambiente
3. Start command: `uv run python main.py`
4. No ML Developer: ative topics `questions`, `messages`, `orders_v2`, `shipments`
5. URL de notificacao: `https://sua-url.railway.app/webhook`

---

## Status atual (2026-04-16)

### Concluido
- Estrutura completa do projeto criada e em producao no Railway
- 8 agentes implementados (orquestrador, monitor, analisador, especialista, respondedor, escalador, telegram_listener, formatador)
- 11 testes passando (test_analisador, test_respondedor, test_escalador)
- Webhook server com FastAPI (perguntas + mensagens pos-venda com debounce 8s)
- Autenticacao OAuth automatica via rota /callback no Railway (atualiza tokens via GraphQL)
- Refresh token obtido e configurado — renovacao automatica sem intervencao
- Mensagens pos-venda: leitura do texto real do comprador via buscar_mensagens_pack
- tag=post_sale corrigido em todos os endpoints de mensagens
- Comandos Telegram: /r, /listar, /status, /cancelar, /comandos
- Seguranca: apenas chat_id autorizado pode usar comandos do bot
- docs/ criado com arquitetura, api-ml, deploy e telegram
- CLAUDE.md atualizado com regras de uso de agentes (Explore/Plan obrigatorio)
