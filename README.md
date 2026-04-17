# ML Pós-Venda

Sistema automatizado para lojas no **Mercado Livre** — responde compradores com IA e envia mensagens de follow-up em cada etapa do pedido. Feito para o nicho de câmeras de segurança e acessórios.

---

## O que faz

### Atendimento automático
Perguntas pré-venda e mensagens pós-venda são classificadas e respondidas pelo Claude automaticamente. Quando a confiança é baixa, você recebe uma notificação no Telegram e responde com um comando curto.

```
Comprador pergunta ou envia mensagem no ML
        ↓
Claude analisa a intenção e gera resposta
        ↓
Confiança ≥ 75% → posta automaticamente no ML
Confiança < 75% → notificação no Telegram
        ↓
/r 1 Sim, é compatível com qualquer DVR HDCVI
        ↓
Formatador aplica saudação por horário + polimento
        ↓
Resposta postada no ML · exemplo salvo na memória
```

### Follow-up automático
Mensagens personalizadas pelo Claude enviadas em cada etapa do pedido:

```
Venda confirmada  →  "Olá João! Seu pedido foi confirmado..."
Produto enviado   →  "Seu pedido foi enviado! Acompanhe pelo ML..."
Produto entregue  →  "Chegou tudo certo? Qualquer dúvida é só chamar!"
```

---

## Comandos Telegram

| Comando | O que faz |
|---------|-----------|
| `/r <n> <resposta>` | Responde a pendente de número `n` no ML |
| `/listar` | Lista todas as pendentes em uma mensagem |
| `/status` | Pendentes · pedidos para enviar · em trânsito · reclamações |
| `/cancelar <n>` | Remove a pendente `n` sem responder |
| `/comandos` | Mostra esta lista |

> Apenas o seu `TELEGRAM_CHAT_ID` pode usar o bot.

---

## Arquitetura

### Agentes de atendimento

| Agente | Arquivo | Função |
|--------|---------|--------|
| Orquestrador | `agents/orquestrador.py` | Coordena o fluxo completo |
| Monitor | `agents/monitor.py` | Busca perguntas novas via API ML |
| Analisador | `agents/analisador.py` | Classifica intenção com Claude |
| Especialista | `agents/especialista.py` | Monta contexto da base de conhecimento |
| Respondedor | `agents/respondedor.py` | Gera resposta e posta se confiança ≥ 75% |
| Escalador | `agents/escalador.py` | Notifica via Telegram quando confiança baixa |
| TelegramListener | `agents/telegram_listener.py` | Processa comandos do Telegram |
| Formatador | `agents/formatador.py` | Saudação por horário + polimento da resposta |
| Pendentes | `agents/pendentes.py` | Persiste interações aguardando resposta |
| Memória | `agents/memoria.py` | Salva exemplos aprovados para aprendizado |

### Agentes de follow-up

| Agente | Arquivo | Função |
|--------|---------|--------|
| Enviador | `agents/enviador.py` | Processa eventos compra / envio / entrega |
| Gerador | `agents/gerador.py` | Gera mensagens com Claude + templates |
| Enviados | `agents/enviados.py` | Evita mensagens duplicadas |

---

## Base de conhecimento

Preencha antes de ir para produção:

| Arquivo | Conteúdo |
|---------|----------|
| `base_conhecimento/produtos.md` | Especificações técnicas dos produtos |
| `base_conhecimento/faq.md` | Perguntas frequentes com respostas |
| `base_conhecimento/garantia.md` | Política de garantia e devolução |
| `base_conhecimento/instalacao.md` | Guias de instalação por produto |
| `base_conhecimento/politicas.md` | Cancelamento, NF, prazos de resposta |

Templates para follow-up:

| Arquivo | Quando é usado |
|---------|----------------|
| `templates/compra.md` | Pedido confirmado |
| `templates/envio.md` | Produto enviado |
| `templates/entrega.md` | Produto entregue |

> `base_conhecimento/memoria.json` e `pendentes.json` são gerados automaticamente — não edite manualmente.

---

## Configuração

### 1. Clone e instale

```bash
git clone https://github.com/Browsher/ML-Pos-Venda.git
cd ML-Pos-Venda
uv sync
```

### 2. Variáveis de ambiente

Crie um `.env` na raiz:

```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Mercado Livre
ML_CLIENT_ID=
ML_CLIENT_SECRET=
ML_REFRESH_TOKEN=
ML_SELLER_ID=
ML_REDIRECT_URI=https://sua-url.railway.app/callback

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Sistema (opcionais)
CONFIANCA_MINIMA=0.75
POLLING_INTERVAL_SEGUNDOS=60
```

### 3. Testes

```bash
uv run python -m pytest tests/ -v
```

### 4. Inicie

```bash
uv run python main.py
```

---

## Deploy no Railway

1. Crie um projeto no [Railway](https://railway.app) conectando este repositório
2. Configure as variáveis de ambiente no painel
3. **Start command:** `uv run python main.py`
4. No [ML Developer](https://developers.mercadolivre.com.br/devcenter):
   - Ative a permissão **"Comunicação pré e pós-venda"** (leitura e escrita)
   - **URL de notificação:** `https://sua-url.railway.app/webhook`
   - **Topics ativos:** `questions`, `messages`, `orders_v2`, `shipments`

### Autenticação OAuth (primeiro acesso)

Acesse no navegador para autorizar o app:
```
https://auth.mercadolivre.com.br/authorization?response_type=code
  &client_id=SEU_CLIENT_ID&redirect_uri=https://sua-url.railway.app/callback
```

O sistema troca o code pelo token e atualiza o Railway automaticamente. O `ML_REFRESH_TOKEN` é renovado sozinho a cada expiração.

---

## Stack

| | |
|-|-|
| Linguagem | Python 3.12+ · [uv](https://github.com/astral-sh/uv) |
| IA | [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — claude-haiku-4-5 |
| Servidor | [FastAPI](https://fastapi.tiangolo.com/) + uvicorn |
| HTTP | [httpx](https://www.python-httpx.org/) |
| Deploy | [Railway](https://railway.app) |
