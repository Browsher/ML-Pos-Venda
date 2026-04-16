# Arquitetura: ML Pós-Venda + Follow-up

## Fluxo Pos-venda: Perguntas

```
Webhook ML (topic=questions)
        ↓
    Orquestrador.ciclo()
        ↓
    Monitor.buscar_novas()        → lista de Interacao
        ↓
    Analisador.analisar()         → Analise (intencao, resumo, urgente)
        ↓
    Especialista.contexto_para()  → base de conhecimento relevante
        ↓
    Respondedor.gerar_e_postar()  → Resposta (texto, confianca, postada)
        ↓
    confianca >= 0.75 → posta no ML automaticamente
    confianca <  0.75 → Escalador.escalar() → Telegram
```

## Fluxo Pos-venda: Resposta Humana

```
Humano envia /r <id> <texto> no Telegram
        ↓
    TelegramListener._processar_resposta()
        ↓
    Formatador.formatar()         → saudacao + hora + polimento
        ↓
    MLClient.responder_pergunta() ou responder_mensagem()
        ↓
    Memoria.adicionar()           → salva para aprendizado
        ↓
    Pendentes.remover()
        ↓
    Confirmacao no Telegram
```

## Fluxo Pos-venda: Mensagens de Compradores

```
Webhook ML (topic=messages, resource=pack_id)
        ↓
    debounce 8s por pack_id
    (aguarda mensagens subsequentes do mesmo comprador)
        ↓
    Orquestrador.processar_mensagem_pack()
        ↓
    MLClient.buscar_mensagens_pack() → ultima mensagem do comprador
        ↓
    Escalador.escalar_mensagem()
        ↓
    Telegram: "💬 Mensagem. /r <pack_id> resposta"
```

## Fluxo Follow-up

```
Webhook ML (topic=orders_v2, status=paid)
        ↓
    _processar_order() → Enviador.processar_compra()

Webhook ML (topic=shipments, status=shipped)
        ↓
    _processar_shipment() → Enviador.processar_envio()

Webhook ML (topic=shipments, status=delivered)
        ↓
    _processar_shipment() → Enviador.processar_entrega()

Em todos os casos:
        ↓
    Enviados.ja_enviou() → ignora se ja processado (evita duplicata)
        ↓
    Gerador.gerar(evento, dados) → Claude + template markdown
        ↓
    MLClient.enviar_followup(pack_id, texto) → API ML
        ↓
    Enviados.marcar() → salva em data/enviados.json
```

---

## Agentes

### Pos-venda

| Agente | Arquivo | Entrada | Saída |
|--------|---------|---------|-------|
| Orquestrador | orquestrador.py | Webhook / loop | Coordena todos |
| Monitor | monitor.py | API ML | Lista de Interacao |
| Analisador | analisador.py | Interacao | Analise |
| Especialista | especialista.py | intencao (str) | contexto (str) |
| Respondedor | respondedor.py | Interacao + Analise + contexto | Resposta |
| Escalador | escalador.py | Interacao + Analise + Resposta | Telegram |
| TelegramListener | telegram_listener.py | Updates Telegram | Resposta no ML |
| Formatador | formatador.py | texto bruto + nome | texto polido |
| Pendentes | pendentes.py | dados da escalada | pendentes.json |
| Memoria | memoria.py | pergunta + resposta | memoria.json |

### Follow-up

| Agente | Arquivo | Entrada | Saída |
|--------|---------|---------|-------|
| Enviador | enviador.py | order_id / shipment_id | Mensagem no ML |
| Gerador | gerador.py | evento + dados do pedido | texto gerado por Claude |
| Enviados | enviados.py | order_id + evento | enviados.json |

---

## Decisões Técnicas

| Decisão | Motivo |
|---------|--------|
| Pendentes sempre relê do disco | Evita race condition entre Escalador e TelegramListener |
| Debounce 8s para mensagens | Acumula mensagens seguidas do mesmo comprador |
| Especialista com cache em memória | Evita reler arquivos .md a cada ciclo |
| Retry automático em 401 | Renova token e repete a requisição sem interrupção |
| Fallback intencao=OUTRO | Se Claude falhar no JSON, escala para humano em vez de crashar |
| Loop Telegram independente (10s) | /r funciona sem depender de webhook do ML |
| Startup cycle (2s delay) | Pega perguntas abertas que chegaram durante downtime |
| chat_id autorizado | Apenas TELEGRAM_CHAT_ID pode usar comandos do bot |
| Enviados sempre relê do disco | Evita duplicatas mesmo após restart do Railway |
| enviar_followup separado de responder_mensagem | Formatos de corpo diferentes: followup usa agente ML (fev/2026) |
| Limite 350 chars no follow-up | Limite da API ML para mensagens |

---

## Estrutura de Arquivos

```
ml-pos-venda/
├── agents/
│   ├── orquestrador.py       ← pos-venda: loop principal
│   ├── monitor.py            ← pos-venda: busca perguntas
│   ├── analisador.py         ← pos-venda: classifica intencao
│   ├── especialista.py       ← pos-venda: base de conhecimento
│   ├── respondedor.py        ← pos-venda: gera e posta resposta
│   ├── escalador.py          ← pos-venda: notifica via Telegram
│   ├── telegram_listener.py  ← pos-venda: recebe comandos
│   ├── formatador.py         ← pos-venda: polida resposta
│   ├── pendentes.py          ← pos-venda: fila de pendentes
│   ├── memoria.py            ← pos-venda: aprendizado
│   ├── enviador.py           ← follow-up: processa eventos
│   ├── gerador.py            ← follow-up: gera mensagens com Claude
│   └── enviados.py           ← follow-up: evita duplicatas
├── templates/
│   ├── compra.md             ← follow-up: pedido confirmado
│   ├── envio.md              ← follow-up: produto enviado
│   └── entrega.md            ← follow-up: produto entregue
├── base_conhecimento/
│   ├── produtos.md           ← preencher com specs reais
│   ├── faq.md                ← preencher com perguntas comuns
│   ├── garantia.md           ← preencher com politicas
│   ├── instalacao.md         ← preencher com guias
│   ├── memoria.json          ← auto-gerado (respostas aprovadas)
│   └── pendentes.json        ← auto-gerado (aguardando resposta)
├── data/
│   └── enviados.json         ← auto-gerado (follow-ups enviados)
├── docs/
│   ├── arquitetura.md        ← este arquivo
│   ├── api-ml.md             ← endpoints e limitações da API ML
│   ├── deploy.md             ← variáveis de ambiente e Railway
│   └── telegram.md           ← comandos e notificações
├── tests/
├── ml_client.py
├── webhook_server.py
├── config.py
├── auth_ml.py
└── main.py
```

---

## Intenções Suportadas (Analisador)

| Valor | Quando usar |
|-------|-------------|
| `duvida_tecnica` | Perguntas sobre especificações, compatibilidade |
| `prazo_entrega` | "Quando chega?", "Qual o prazo?" |
| `troca_devolucao` | "Quero devolver", "Veio errado" |
| `reclamacao` | "Não funciona", "Com defeito" |
| `confirmacao_pedido` | "Confirma meu pedido?" |
| `outro` | Não classificado → sempre escala para humano |
