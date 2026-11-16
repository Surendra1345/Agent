# Agent — Construction Contract & Invoice Review

An AI agent that reviews construction contracts against a company rulebook, validates invoices against their
contracts, answers questions about stored documents, and turns plain-English questions into safe SQL.

- **Backend:** FastAPI + LangGraph, PostgreSQL with pgvector, OpenRouter LLM (default `openai/gpt-4o-mini`)
- **Frontend:** React + Vite + TypeScript
- **Single endpoint:** `POST /api/chat` handles chat, PDF upload, review, save confirmation and queries

## Getting Started

### Prerequisites
Python 3.11–3.13, [uv](https://docs.astral.sh/uv/), Node 20+, PostgreSQL with the `pgvector` extension.

### Backend
```bash
cd backend
cp .env.example .env        # then fill in the values below
uv sync
uv run alembic upgrade head
uv run uvicorn agent.api:app --reload --app-dir src
```

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | e.g. `postgresql+psycopg2://user:pass@localhost:5432/Agent` (use the `+psycopg2` driver) |
| `OPENROUTER_API_KEY` | yes | OpenRouter key (`Api-Key` still works as a fallback) |
| `CONTRACT_RULEBOOK_PATH` | for ingestion | Path to the rulebook PDF used by `embedding/embed.py` |
| `LLM_MODEL` | no | Defaults to `openai/gpt-4o-mini` |
| `CORS_ORIGINS` | no | Comma-separated allowed origins. Defaults to `http://localhost:5173` |

Never commit `.env`. Database credentials live only in `DATABASE_URL`; `alembic.ini` holds a placeholder.

### Frontend
```bash
cd frontend
npm ci
npm run dev        # http://localhost:5173
```

### Tests
```bash
cd backend
uv run pytest
```

To regenerate the workflow diagram (needs internet): `uv run python -c "from agent.services.graph_agent import export_graph_diagram as e; e()"`

---

# Text-to-SQL Architecture

## High-Level Overview

```mermaid
flowchart TB
    subgraph USER["👤 User / Frontend"]
        A["Natural Language Prompt\ne.g. 'get contracts where tax > 15%'"]
    end

    subgraph API["🌐 FastAPI Layer\n(api.py)"]
        B["GET /api/search?prompt=..."]
        B1{"Is prompt an\nexact contract_id?"}
        B2["Fast-path: Direct DB lookup\nget_contract_by_id()"]
        B3["Pass to Text-to-SQL pipeline"]
    end

    subgraph T2S["🧠 Text-to-SQL Service\n(text_to_sql.py)"]
        C["generate_sql_from_prompt()"]
        D["execute_contract_query()"]
    end

    subgraph LLM["🤖 LLM\n(GPT-4o-mini via OpenRouter)"]
        E["System Prompt:\n+ DB Schema\n+ Column descriptions\n+ Indian currency units\n+ Safety rules"]
        F["User Prompt:\nNatural Language Query"]
        G["Output JSON:\n{sql: 'SELECT ...', params: {...}}"]
    end

    subgraph DB["🐘 PostgreSQL\n(contracts table)"]
        H["Parameterized Query Execution\nSELECT * FROM contracts\nWHERE tax_rate > :tax"]
        I["Query Results\n(rows as dicts)"]
    end

    A --> B
    B --> B1
    B1 -->|"Yes (e.g. 'C001')"| B2
    B1 -->|"No"| B3
    B2 --> DB
    B3 --> C
    C --> E
    C --> F
    E & F --> G
    G --> D
    D --> H
    H --> I
    I --> USER
```

---

## Detailed Step-by-Step Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI\n(api.py)
    participant T2S as Text-to-SQL Service\n(text_to_sql.py)
    participant LLM as LLM (GPT-4o-mini)\n(OpenRouter)
    participant PG as PostgreSQL\n(contracts table)

    User->>API: GET /api/search?prompt="tax more than 15%"

    API->>API: Check if prompt == contract_id (fast-path)
    note over API: "tax more than 15%" is NOT a contract_id
    
    API->>T2S: query_contracts_with_llm("tax more than 15%")

    T2S->>LLM: System Prompt (DB schema + safety rules)\n+ User: "tax more than 15%"
    
    note over LLM: LLM understands:\n- "tax" → tax_rate column\n- "more than" → > operator\n- "15%" → value 15
    
    LLM-->>T2S: {"sql": "SELECT * FROM contracts\nWHERE tax_rate > :tax", "params": {"tax": 15}}

    T2S->>T2S: Validate SQL starts with SELECT\n(safety guard, reject INSERT/DELETE etc.)
    
    T2S->>PG: session.execute(text(sql), params)\n→ Safe parameterized execution
    
    PG-->>T2S: Matching rows (tax_rate > 15)
    
    T2S-->>API: (rows=[], generated_sql="SELECT ...")
    
    API-->>User: JSON Response\n{message, generated_sql, total, contracts: [...]}
```

---

## What the LLM Receives (Context)

```
┌──────────────────────────────────────────────────────────────┐
│                    LLM INPUT (System Prompt)                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Table: contracts                                             │
│  Columns:                                                     │
│    contract_id      TEXT     (e.g. "C001", "C_CONS_BEBF")    │
│    contract_name    TEXT     (project name)                   │
│    contract_amount  NUMERIC  (in Rupees)                      │
│    tax_rate         NUMERIC  (e.g. 18.0 = 18%)               │
│    start_date       DATE     (YYYY-MM-DD)                     │
│    end_date         DATE     (completion date)                │
│    file_url         TEXT     (document path)                  │
│    created_at       DATE     (when saved in DB)               │
│                                                               │
│  Indian Currency:                                             │
│    1 Lakh  = 100,000                                          │
│    1 Crore = 10,000,000                                       │
│                                                               │
│  RULES:                                                       │
│    ✅ Use :name style params (e.g. :amount, :tax)             │
│    ✅ Only generate SELECT queries                             │
│    ✅ Return JSON: {"sql": "...", "params": {...}}             │
│    ❌ Never INSERT, UPDATE, DELETE, DROP                       │
│    ❌ Never inline values directly into SQL                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                              +
┌──────────────────────────────────────────────────────────────┐
│                    LLM INPUT (User Message)                   │
├──────────────────────────────────────────────────────────────┤
│  "get contracts where tax is more than 15%"                   │
└──────────────────────────────────────────────────────────────┘
```

---

## What the LLM Outputs

```
┌──────────────────────────────────────────────────────────────┐
│                    LLM OUTPUT (JSON)                          │
├──────────────────────────────────────────────────────────────┤
│  {                                                            │
│    "sql": "SELECT * FROM contracts                            │
│             WHERE tax_rate > :tax",                           │
│    "params": {                                                │
│       "tax": 15                                               │
│    }                                                          │
│  }                                                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Safety Layer (SQL Injection Protection)

Generated SQL is never trusted. `validate_select_sql()` in `text_to_sql.py` parses it with `sqlglot` and enforces:

| Rule | Example blocked |
|---|---|
| Exactly one statement | `SELECT 1; DROP TABLE contracts` |
| Top level must be a `SELECT` | `DROP`, `UPDATE`, `INSERT`, `DELETE`, `CREATE` |
| No data-modifying CTEs | `WITH x AS (DELETE ... RETURNING *) SELECT ...` |
| Only `contracts` and `invoices` tables | `SELECT * FROM pg_user` |
| No server/file/sleep functions | `pg_sleep`, `lo_import`, `pg_read_file`, `dblink` |
| `LIMIT 50` added if missing | unbounded result sets |

The original SQL text is kept as-is (case and `:name` placeholders untouched). Execution also runs in a
`READ ONLY` transaction with a 10 s `statement_timeout`, so a validation miss still cannot write data.

```
User Input          LLM Output                          PostgreSQL Execution
─────────           ──────────                          ────────────────────
"15%"     ──────►  sql    = "WHERE tax_rate > :tax"     ◄─── Value bound
                   params = {"tax": 15}                 Treats 15 as DATA, not as SQL ✅
```

## Uploads

PDF only (checked by extension and `%PDF-` signature), max 25 MB. Files are stored with a unique prefix so uploads
never overwrite each other. A PDF that cannot be parsed returns `422` and is deleted.

## Known limitations

- Conversation memory is in-process (`MemorySaver`); it resets on restart. Send a `session_id` per user, otherwise all
  requests share one session.
- `invoices.contract_id` is unique, so a contract can hold only one invoice.
- No authentication or rate limiting on `/api/chat`; `/uploads` is served publicly.

---

## Example Prompt Translations

| User Natural Language Prompt | LLM Generated SQL |
|---|---|
| `"tax is more than 15%"` | `SELECT * FROM contracts WHERE tax_rate > :tax` → `{tax: 15}` |
| `"amount more than 2 crore"` | `SELECT * FROM contracts WHERE contract_amount > :amount` → `{amount: 20000000}` |
| `"completing in 5 days"` | `SELECT * FROM contracts WHERE end_date <= CURRENT_DATE + INTERVAL '5 days'` |
| `"Hoskote contracts"` | `SELECT * FROM contracts WHERE contract_name ILIKE :name` → `{name: '%Hoskote%'}` |
| `"top 3 by amount"` | `SELECT * FROM contracts ORDER BY contract_amount DESC LIMIT 3` |
| `"created after Sept 2026"` | `SELECT * FROM contracts WHERE created_at > :date` → `{date: '2026-09-01'}` |
| `"C001"` | *(Fast-path: skips LLM, direct DB lookup)* |
