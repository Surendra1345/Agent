# Agent

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

```
User Input          LLM Output                  PostgreSQL Execution
─────────           ──────────                  ────────────────────
"15%"     ──────►  sql    = "WHERE tax_rate > :tax"   ◄─── Value bound
                   params = {"tax": 15}          ──────────────────
                                                 Treats 15 as DATA,
                                                 not as SQL command ✅

                   ❌ NEVER:
                   "WHERE tax_rate > 15"  (inline string = SQL injection risk)
```

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
