# ML Pós-Venda

Sistema automatizado para lojas no **Mercado Livre** com dois subsistemas rodando em um único serviço:

- **Pós-venda** — responde perguntas e mensagens de compradores com supervisão via Telegram
- **Follow-up** — envia mensagens automáticas em cada etapa do pedido (compra, envio, entrega)

---

## Como funciona

### Pós-venda

```
Comprador faz pergunta ou envia mensagem no ML
        ↓
Claude analisa a intenção e gera uma resposta
        ↓
Confiança >= 75% → posta automaticamente no ML
Confiança < 75%  → você recebe no Telegram
        ↓
Você responde com /r <id> <texto>
        ↓
Formatador aplica: saudação + horário + polimento
        ↓
Resposta postada no ML e salva na memória
```

### Follow-up automático

```
Venda confirmada  → "Olá João! Seu pedido foi confirmado..."
Produto enviado   → "Seu pedido foi enviado! Acompanhe pelo ML..."
Produto entregue  → "Chegou tudo certo? Qualquer dúvida é só chamar!"
```

Mensagens geradas pelo Claude com base nos templates em `templates/`.

---

## Comandos Telegram

| Comando | O que faz |
|---------|-----------|
| `/r <id> <resposta>` | Responde uma pergunta ou mensagem pendente no ML |
| `/listar` | Lista todas as pendentes com o comando pronto |
| `/status` | Resumo de pendentes e tamanho da base de conhecimento |
| `/cancelar <id>` | Remove uma pendente sem responder |
| `/comandos` | Mostra esta lista |

Apenas o seu chat_id configurado pode usar o bot.

---

## Agentes

### Pós-venda

| Agente | Função |
|--------|--------|
| **Orquestrador** | Coordena o fluxo de perguntas e mensagens |
| **Monitor** | Busca perguntas novas via API ML |
| **Analisador** | Classifica a intenção com Claude |
| **Especialista** | Carrega a base de conhecimento relevante |
| **Respondedor** | Gera e posta resposta automática |
| **Escalador** | Notifica você via Telegram |
| **TelegramListener** | Recebe e processa seus comandos |
| **Formatador** | Polida a resposta antes de postar |

### Follow-up

| Agente | Função |
|--------|--------|
| **Enviador** | Processa eventos de compra, envio e entrega |
| **Gerador** | Gera mensagens personalizadas com Claude |
| **Enviados** | Evita enviar a mesma mensagem duas vezes |

---

## Base de conhecimento

Edite os arquivos em `base_conhecimento/` antes de ir para produção:

| Arquivo | Conteúdo |
|---------|----------|
| `produtos.md` | Especificações dos produtos |
| `faq.md` | Perguntas frequentes |
| `garantia.md` | Política de garantia e devolução |
| `instalacao.md` | Guia de instalação |

E os templates em `templates/` para personalizar as mensagens de follow-up:

| Arquivo | Quando é usado |
|---------|----------------|
| `compra.md` | Pedido confirmado |
| `envio.md` | Produto enviado |
| `entrega.md` | Produto entregue |

---

## Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/Browsher/ML-Pos-Venda.git
cd ML-Pos-Venda
```

### 2. Instale as dependências

```bash
uv sync
```

### 3. Configure as variáveis de ambiente

Crie um `.env` na raiz:

```env
ANTHROPIC_API_KEY=sk-ant-...

ML_CLIENT_ID=
ML_CLIENT_SECRET=
ML_REFRESH_TOKEN=
ML_SELLER_ID=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

CONFIANCA_MINIMA=0.75
POLLING_INTERVAL_SEGUNDOS=60
```

### 4. Rode os testes

```bash
uv run python -m pytest tests/ -v
```

### 5. Inicie o servidor

```bash
uv run python main.py
```

---

## Deploy (Railway)

1. Crie um projeto no [Railway](https://railway.app) conectando este repositório
2. Configure as variáveis de ambiente no painel
3. **Start command**: `uv run python main.py`
4. No [ML Developer](https://developers.mercadolivre.com.br/devcenter), configure:
   - **URL de notificação**: `https://sua-url.railway.app/webhook`
   - **Topics ativos**: `questions`, `messages`, `orders_v2`, `shipments`

### Autenticação ML (primeiro acesso)

Acesse no navegador:
```
https://sua-url.railway.app/callback?code=SEU_CODE
```

O sistema troca o code pelo token e atualiza o Railway automaticamente.
A partir daí, o `ML_REFRESH_TOKEN` é renovado sozinho a cada expiração.

---

## Stack

- Python 3.12+ · [uv](https://github.com/astral-sh/uv)
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — claude-haiku-4-5
- [FastAPI](https://fastapi.tiangolo.com/) + uvicorn — servidor webhook
- [httpx](https://www.python-httpx.org/) — chamadas API ML e Telegram
