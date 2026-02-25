# DataPilot — Assistente Virtual de Dados

DataPilot é um assistente de análise de dados que responde perguntas em linguagem natural sobre um banco de dados SQLite empresarial. O sistema utiliza um agente baseado em LangGraph com ferramentas de descoberta e consulta dinâmica, sem nenhuma query SQL pré-programada.

---

## Funcionalidades

- **Linguagem Natural** — perguntas formuladas livremente, sem necessidade de conhecimento técnico
- **Descoberta Dinâmica de Schema** — o agente lê a estrutura do banco em tempo de execução, sem dependência de queries fixas
- **Perguntas Complexas** — suporte a múltiplas consultas encadeadas e raciocínio em múltiplos passos
- **Autocorreção de SQL** — erros de execução são detectados automaticamente; o agente corrige e reexecuta (até 3 tentativas consecutivas)
- **Streaming de Resposta** — resposta exibida token a token, sem bloqueio de interface
- **Histórico de Conversas** — sessões persistidas em SQLite local com títulos gerados por IA
- **Visualizações Automáticas** — gráficos Plotly gerados quando a resposta contém dados tabulares
- **Guardrail de Escopo** — recusa perguntas fora do domínio de negócio com mensagem explicativa

---

## Estrutura do Projeto

```
DataPilotFranq/
├── app.py                      # Entry point Streamlit
├── requirements.txt
├── .env                        # Variáveis de ambiente (não versionar)
├── .env.example
├── .streamlit/
│   └── config.toml             # Configuração de tema
├── data/
│   ├── anexo_desafio_1.db      # Banco de dados principal
│   └── chat_history.db         # Histórico de conversas (gerado em runtime)
└── src/
    ├── config.py               # Configurações e variáveis de ambiente
    ├── database.py             # Conexão ao banco e schema discovery
    ├── history.py              # Persistência de sessões e mensagens
    ├── agent/
    │   ├── graph.py            # Grafo LangGraph: nós, roteamento e streaming
    │   ├── tools.py            # Ferramentas: get_db_schema, execute_sql
    │   ├── prompts.py          # System prompt em português
    │   └── title_agent.py      # Geração de título de sessão via LLM
    └── ui/
        ├── sidebar.py          # Lista de sessões e nova conversa
        ├── chat.py             # Renderização do histórico de mensagens
        ├── charts.py           # Visualizações Plotly
        └── styles.py           # CSS do tema escuro
```

---

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Chave de API da OpenAI

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/GuilhermeLeandro/DataPilotFranq.git
cd DataPilotFranq

# 2. Crie o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env e preencha os valores necessários
```

### Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `OPENAI_API_KEY` | Sim | — | Chave de API da OpenAI |
| `MODEL` | Não | `gpt-4o-mini` | Modelo a ser utilizado |
| `DB_PATH` | Não | `./data/anexo_desafio_1.db` | Caminho para o banco de dados |

### Execução

```bash
streamlit run app.py
```

Acesse em **http://localhost:8501**

---

## Arquitetura do Agente

O agente implementa o padrão **ReAct** (Reason + Act) via LangGraph:

```
START
  └─> agent_node
        ├── [tool_calls presentes]   → tools_node → agent_node (loop)
        ├── [sem tool_calls]         → END
        └── [3 erros consecutivos]   → fail_node  → END
```

### Ferramentas disponíveis

| Ferramenta | Descrição |
|---|---|
| `get_db_schema` | Lê o schema completo do banco em runtime (tabelas, colunas, tipos, amostras) |
| `execute_sql` | Executa uma query SQLite e retorna o resultado como JSON |

### Fluxo de uma consulta

1. O agente chama `get_db_schema` para entender a estrutura disponível
2. Gera e executa queries SQL com `execute_sql`
3. Analisa os resultados e formula a resposta em português
4. Em caso de erro de SQL, corrige e reexecuta (máximo de 3 tentativas consecutivas)
5. Após 3 falhas, retorna mensagem de erro ao usuário sem continuar em loop

---

## Requisitos Atendidos

| Requisito | Status | Implementação |
|---|---|---|
| Perguntas complexas | Atendido | Loop ReAct com múltiplas queries encadeadas e acumulação de contexto |
| Autocorreção de SQL | Atendido | `retry_count` incrementado por erro; `fail_node` acionado após 3 falhas |
| Descoberta dinâmica | Atendido | `get_db_schema` consulta `sqlite_master` em runtime; zero queries hardcoded |

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Modelo de Linguagem | OpenAI `gpt-4o-mini` |
| Orquestração do Agente | LangGraph + LangChain |
| Interface | Streamlit 1.40+ |
| Banco de Dados Principal | SQLite |
| Persistência de Histórico | SQLite |
| Visualizações | Plotly |

---

## Exemplos de Consultas Testadas

As consultas abaixo foram testadas durante o desenvolvimento e representam os diferentes tipos de raciocínio que o agente é capaz de executar:

| Consulta | Tipo de Raciocínio | Saída Esperada |
|---|---|---|
| "Liste os 5 estados com maior número de clientes que compraram via app em maio." | Filtro + agrupamento + ranking | Tabela e gráfico de barras |
| "Quantos clientes interagiram com campanhas de WhatsApp em 2024?" | Filtro por canal e período + contagem | Valor numérico |
| "Quais categorias de produto tiveram o maior número de compras em média por cliente?" | Agregação com média por grupo | Tabela ranqueada |
| "Qual o número de reclamações não resolvidas por canal?" | Filtro booleano + agrupamento | Gráfico de barras |
| "Qual a tendência de reclamações por canal no último ano?" | Série temporal + agrupamento múltiplo | Gráfico de linha |
| "Qual canal de suporte tem o maior índice de resolução?" | Cálculo de proporção por grupo | Tabela com percentuais |
| "Compare o ticket médio de compra entre homens e mulheres por categoria." | Múltiplas dimensões de agrupamento | Tabela comparativa |

---

## Sugestões de Melhorias e Extensões

### Melhorias Técnicas

- **Cache de schema**: armazenar o resultado de `get_db_schema` em cache com TTL para reduzir chamadas redundantes ao banco em conversas longas
- **Streaming de metadados**: exibir em tempo real qual ferramenta o agente está chamando (ex.: "Executando query 1 de 2...")
- **Suporte a múltiplos bancos**: permitir que o usuário selecione entre diferentes arquivos `.db` via interface

### Melhorias de Produto

- **Autenticação**: adição de login por usuário para separação de histórico e controle de acesso
- **Exportação de resultados**: botão para exportar tabelas como `.csv` e gráficos como `.png` diretamente da interface
- **Perguntas sugeridas**: exibir exemplos de perguntas contextuais com base no schema detectado na primeira inicialização
- **Feedback do usuário**: mecanismo de avaliação da resposta (positivo/negativo) para futura melhoria do sistema

### Extensões de Arquitetura

- **Suporte a LLMs locais**: substituir a OpenAI por modelos locais via Ollama para ambientes sem acesso à internet
- **Avaliação automática de respostas**: pipeline de avaliação com LangSmith para monitorar qualidade das respostas em produção
- **Agente multi-etapa com planejamento**: separar a fase de planejamento (quais queries executar) da fase de execução, aumentando a precisão em perguntas muito complexas

