# 🤖 DataPilot — Assistente Virtual de Dados

DataPilot é um assistente de análise de dados que responde perguntas em linguagem natural sobre um banco de dados SQLite empresarial. Ele usa um agente LangGraph com ferramentas de descoberta e consulta dinâmica, sem nenhuma query hardcoded.

---

## ✨ Funcionalidades

- **Linguagem Natural** — faça perguntas como faria a um analista júnior
- **Descoberta Dinâmica** — o agente lê o schema do banco automaticamente antes de cada análise
- **Perguntas Complexas** — suporta múltiplas queries encadeadas e raciocínio em etapas
- **Autocorreção de SQL** — se uma query falhar, o agente detecta o erro e tenta corrigir (até 3 tentativas)
- **Streaming de Resposta** — a resposta aparece token a token, como o ChatGPT
- **Histórico de Conversas** — sessões persistidas em SQLite com títulos gerados por IA
- **Visualizações** — gráficos automáticos via Plotly quando a resposta contém dados tabulares
- **Guardrail de Escopo** — recusa perguntas fora do domínio de negócio

---

## 🗂️ Estrutura do Projeto

```
DataPilotFranq/
├── app.py                  # Entry point Streamlit
├── requirements.txt
├── .env                    # Variáveis de ambiente (não versionar)
├── .env.example
├── .streamlit/
│   └── config.toml         # Tema escuro
├── data/
│   ├── anexo_desafio_1.db  # Banco de dados principal
│   └── chat_history.db     # Histórico de conversas (gerado)
└── src/
    ├── config.py           # Configurações centralizadas
    ├── database.py         # Conexão e schema discovery
    ├── history.py          # CRUD de sessões e mensagens
    ├── agent/
    │   ├── graph.py        # LangGraph: nodes, routing, streaming
    │   ├── tools.py        # Ferramentas: get_db_schema, execute_sql
    │   ├── prompts.py      # System prompt em português
    │   └── title_agent.py  # Geração de título de sessão via LLM
    └── ui/
        ├── sidebar.py      # Lista de sessões + nova conversa
        ├── chat.py         # Renderização do histórico de chat
        ├── charts.py       # Visualizações Plotly
        └── styles.py       # CSS injetado (tema dark)
```

---

## ⚙️ Setup

### Pré-requisitos
- Python 3.10+
- Chave de API da OpenAI

### Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd DataPilotFranq

# 2. Crie o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e preencha OPENAI_API_KEY
```

### Variáveis de Ambiente

```env
OPENAI_API_KEY=sk-...          # Obrigatório
MODEL=gpt-4o-mini              # Opcional (padrão: gpt-4o-mini)
DB_PATH=./data/anexo_desafio_1.db  # Opcional
```

### Executar

```bash
streamlit run app.py
```

Acesse em **http://localhost:8501**

---

## 🧠 Arquitetura do Agente

O agente usa **LangGraph** com o padrão ReAct (Reason + Act):

```
START → agent_node → [tem tool_calls?]
                         ├── sim   → tools_node → agent_node (loop)
                         ├── não   → END
                         └── erro³ → fail_node → END
```

**Ferramentas disponíveis:**
| Ferramenta | Descrição |
|---|---|
| `get_db_schema` | Lê o schema completo do banco (tabelas, colunas, amostras) |
| `execute_sql` | Executa uma query SQLite e retorna o resultado como JSON |

**Fluxo de uma pergunta:**
1. Agente chama `get_db_schema` para entender a estrutura
2. Gera e executa queries SQL com `execute_sql`
3. Analisa os resultados e formula a resposta em português
4. Se SQL falhar → corrige e tenta novamente (máx. 3 vezes)

---

## 🛡️ Requisitos Atendidos

| Requisito | Status | Implementação |
|---|---|---|
| Perguntas complexas | ✅ | Loop ReAct com múltiplas queries encadeadas |
| Autocorreção de SQL | ✅ | `retry_count` + `fail_node` após 3 falhas consecutivas |
| Descoberta dinâmica | ✅ | `get_db_schema` lê `sqlite_master` em runtime |

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| LLM | OpenAI `gpt-4o-mini` |
| Orquestração | LangGraph + LangChain |
| Frontend | Streamlit 1.40+ |
| Banco de dados | SQLite |
| Visualização | Plotly |
| Histórico | SQLite (`chat_history.db`) |
