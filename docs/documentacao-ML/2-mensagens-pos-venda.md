# Mensagens Pós-Venda — API do Mercado Livre

Compradores que já compraram podem enviar mensagens pelo chat do pedido.
Este documento cobre como receber notificações, ler e responder essas mensagens.

---

## Visão geral

- Mensagens ficam vinculadas a um `pack_id` (identificador da conversa do pedido)
- `tag=post_sale` é **obrigatório** em todos os endpoints de mensagens
- Desde **fevereiro de 2026**, para MLB (Brasil), as mensagens são intermediadas por um agente de IA
- O seller não pode iniciar conversa — apenas responder após o comprador escrever
- Limite de **350 caracteres** por mensagem do seller (comprador tem 3500)
- O webhook envia um **UUID** de mensagem, não o pack_id — é preciso resolver

---

## Webhook

**Tópico a ativar no ML Developer:** `messages`

**Payload recebido:**
```json
{
  "resource": "/messages/0033b582a1474fa98c02d229abcec43c",
  "user_id": 291982050,
  "topic": "messages",
  "application_id": 123456,
  "attempts": 1,
  "sent": "2026-04-17T10:00:00Z"
}
```

> **Atenção:** O campo `resource` contém um **UUID de mensagem**, não um pack_id.
> Para obter o pack_id, é preciso fazer `GET /messages/{uuid}?tag=post_sale` primeiro.

### Fluxo correto ao receber o webhook:
```
1. Extrair UUID do resource: "0033b582a1474fa98c02d229abcec43c"
2. GET /messages/{uuid}?tag=post_sale → obter pack_id
3. GET /messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale → listar mensagens
4. Identificar a mensagem do comprador (from.user_id != seller_id)
5. Processar e responder se necessário
```

---

## Endpoints

### Buscar mensagem por UUID

Necessário para resolver o UUID do webhook em pack_id.

```
GET /messages/{uuid}?tag=post_sale
Authorization: Bearer {access_token}
```

**Request:**
```bash
curl -X GET \
  -H 'Authorization: Bearer $ACCESS_TOKEN' \
  'https://api.mercadolibre.com/messages/0033b582a1474fa98c02d229abcec43c?tag=post_sale'
```

**Response:**
```json
{
  "id": "0033b582a1474fa98c02d229abcec43c",
  "pack_id": 2000012546698451,
  "from": {
    "user_id": "441782523"
  },
  "to": {
    "user_id": "291982050"
  },
  "text": "Meu produto chegou com defeito"
}
```

---

### Listar mensagens não lidas

```
GET /messages/unread?role=seller&tag=post_sale
Authorization: Bearer {access_token}
```

**Parâmetros obrigatórios:**

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `role` | `seller` | **Obrigatório.** Sem ele a requisição falha |
| `tag` | `post_sale` | **Obrigatório** em todos endpoints de mensagens |

**Parâmetros opcionais:**

| Parâmetro | Descrição |
|-----------|-----------|
| `mark_as_read=false` | Não marca como lido ao consultar |

**Retorna:** Até 1000 conversas

**Request:**
```bash
curl -X GET \
  -H 'Authorization: Bearer $ACCESS_TOKEN' \
  'https://api.mercadolibre.com/messages/unread?role=seller&tag=post_sale&mark_as_read=false'
```

---

### Buscar todas as mensagens de um pack

```
GET /messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale
Authorization: Bearer {access_token}
```

**Nota:** Se o pedido não tem `pack_id` (é null), usar o `order_id` no lugar.

**Request:**
```bash
curl -X GET \
  -H 'Authorization: Bearer $ACCESS_TOKEN' \
  'https://api.mercadolibre.com/messages/packs/2000012546698451/sellers/291982050?tag=post_sale'
```

**Response:**
```json
{
  "paging": {
    "limit": 50,
    "offset": 0,
    "total": 3
  },
  "messages": [
    {
      "id": "0033b582a1474fa98c02d229abcec43c",
      "date_created": "2026-04-17T10:00:00Z",
      "text": "Meu produto chegou com defeito",
      "from": {
        "user_id": "441782523"
      },
      "to": {
        "user_id": "291982050"
      },
      "status": "available"
    }
  ],
  "seller_max_message_length": 350,
  "buyer_max_message_length": 3500
}
```

**Como identificar quem enviou cada mensagem:**

```python
# Compara user_id do remetente com o seller_id
# NÃO use user_type ou nickname — nem sempre existem
if msg["from"]["user_id"] != str(seller_id):
    # mensagem do comprador
```

> **Campos do objeto `from` que existem de verdade:**
> - `user_id` — sempre presente ✅
> - `user_type` — pode aparecer em algumas respostas, mas não confiável para identificar comprador/seller
> - `nickname` — pode aparecer em algumas respostas
>
> **Campo `text`:** É uma **string simples**, não um objeto. `msg["text"]` direto, nunca `msg["text"]["plain"]`.

---

### Responder mensagem em um pack

```
POST /messages/packs/{pack_id}/sellers/{seller_id}?tag=post_sale
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Body obrigatório:**
```json
{
  "from": {
    "user_id": 291982050
  },
  "to": {
    "user_id": 3037675074
  },
  "text": "Olá! Pode nos enviar uma foto do defeito? Vamos resolver imediatamente."
}
```

**Campos do body:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `from.user_id` | int | Seu seller_id (inteiro, não string) |
| `to.user_id` | int | **Agent ID do Brasil: `3037675074`** (não o user_id do comprador) |
| `text` | string | Texto da mensagem — máx 350 caracteres |
| `attachments` | array | Opcional. IDs de arquivos enviados via POST /messages/attachments |

> **Por que `to.user_id = 3037675074`?**
> Desde fevereiro de 2026, o ML Brasil introduziu uma camada de agentes de IA que intermedia as mensagens. O seller envia para o agente (3037675074), que entrega ao comprador.

**Response (201 Created):**
```json
{
  "message_id": "a1b2c3d4e5f6789012345678901234ab",
  "date_created": "2026-04-17T10:30:45.123Z",
  "status": "available"
}
```

---

## Agent IDs por país (desde fev/2026)

| País | Site | Agent ID |
|------|------|----------|
| Brasil | MLB | `3037675074` |
| Chile | MLC | `3020819166` |
| Colômbia | MCO | `3037204123` |
| México | MLM | `3037204279` |
| Argentina | MLA | `3037674934` |

---

## Regras e restrições

| Regra | Detalhe |
|-------|---------|
| Máximo por mensagem (seller) | **350 caracteres** |
| Máximo por mensagem (comprador) | 3500 caracteres |
| Quem pode iniciar | **Apenas o comprador.** Seller não pode iniciar conversa |
| Prazo para responder | 48 horas úteis antes de conversar travar |
| tag=post_sale | Obrigatório em **todos** os endpoints |
| Encoding | ISO-8859-1 (caracteres latinos) + emoticons aprovados |
| HTML simples | Funciona: `<a href="url">texto</a>` |
| Pedidos cancelados | Conversa bloqueada automaticamente |
| Mensagens em massa | Não permitido — 1 mensagem por requisição |

---

## Quando a conversa fica bloqueada

| Motivo (`substatus`) | Descrição |
|----------------------|-----------|
| `blocked_by_time` | Mais de 30 dias sem resposta |
| `blocked_by_buyer` | Comprador bloqueou o seller |
| `blocked_by_fulfillment` | Pedido em fulfillment, ainda não entregue |
| `blocked_by_cancelled` | Pedido cancelado |
| `blocked_by_mediation` | Mediação em andamento |
| `blocked_by_claim` | Reclamação ativa |
| `blocked_by_deactivated_account` | Conta desativada |

---

## Upload de anexos

```
POST /messages/attachments?tag=post_sale&site_id=MLB
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

- Formatos aceitos: JPG, PNG, PDF, TXT
- Tamanho máximo: 25 MB por arquivo
- Até 25 arquivos por mensagem
- Arquivo é deletado automaticamente se não usado em 48 horas
- Retorna um `attachment_id` para usar no campo `attachments` do POST de resposta

---

## Erros comuns

| Código | Causa | Solução |
|--------|-------|---------|
| 401 | Token expirado | Renovar via refresh_token |
| 403 | Token de outro usuário / permissão não ativada / pedido cancelado / agent_id errado | Verificar permissão "Comunicação pré e pós-venda" no ML Developer + usar agent_id correto |
| 404 | pack_id ou UUID inválido | Verificar IDs |
| 422 | Texto vazio ou acima de 350 chars | Ajustar texto |
| 429 | Rate limit atingido (500 req/min) | Aguardar com backoff exponencial |

---

## Rate limit

- **500 requisições por minuto** (GET e POST compartilham o mesmo pool)
- HTTP 429 quando excedido

---

## Permissão necessária no ML Developer

No painel do ML Developer → sua aplicação → Permissões funcionais:

- **"Comunicação pré e pós-venda"** com acesso de **leitura e escrita**

Sem essa permissão ativa, todos os endpoints de mensagens retornam 403.
Após ativar, é necessário gerar um novo token OAuth para que o novo escopo seja incluído.
