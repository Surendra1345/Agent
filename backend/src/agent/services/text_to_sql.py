"""
Text-to-SQL service using LLM.
Converts any natural language prompt about contracts or invoices into a safe PostgreSQL SELECT query.
"""
import json
import re
from sqlalchemy import text
from sqlalchemy.orm import Session

from agent.config.database import engine
from agent.services.llm import client, MODEL, TEMPERATURE

DATABASE_SCHEMA = """
Tables in PostgreSQL Database:

1. Table: contracts
   Columns:
     - contract_id      TEXT        (Primary Key, e.g. "C001", "C_ORBI_AF36")
     - contract_name    TEXT        (Title / Project name of the contract)
     - contract_amount  NUMERIC     (Total contract agreed value in INR, e.g. 14000000 = 1.4 Crore)
     - tax_rate         NUMERIC     (Applicable tax percentage, e.g. 18.0)
     - start_date       DATE        (Effective start date, format: YYYY-MM-DD)
     - end_date         DATE        (Completion date, format: YYYY-MM-DD)
     - file_url         TEXT        (PDF document path or URL)
     - created_at       DATE        (Record creation date)

2. Table: invoices
   Columns:
     - invoice_id       TEXT        (Primary Key, e.g. "INV001", "BRC/2026/INV-006")
     - contract_id      TEXT        (Foreign Key references contracts.contract_id)
     - invoice_amount   NUMERIC     (Billed base amount in INR)
     - invoice_tax      NUMERIC     (Billed tax amount in INR)
     - due_date         DATE        (Payment due date, format: YYYY-MM-DD)
     - status           TEXT        ('Pending', 'Paid')
     - paid_date        DATE        (Date when paid, NULL if pending)
     - created_at       DATE        (Record creation date)

Relationship:
   invoices i JOIN contracts c ON c.contract_id = i.contract_id

Indian Currency Units (for understanding user input):
   - 1 Lakh  = 100,000
   - 1 Crore = 10,000,000

CRITICAL RULES:
   - Always generate valid PostgreSQL SELECT queries.
   - Understanding Tax Fields:
     * `contracts.tax_rate` is a PERCENTAGE (e.g. 18.0 means 18%), NOT a currency amount.
     * `invoices.invoice_tax` is the ACTUAL CURRENCY AMOUNT in INR (e.g. 22500000 = 2.25 Crore).
     * If the user asks for contracts having a "tax value" or "tax amount" in Lakhs/Crores, JOIN `contracts c JOIN invoices i ON c.contract_id = i.contract_id` and check `i.invoice_tax`, or check both `i.invoice_tax` and `(c.contract_amount * c.tax_rate / 100)`.
   - You can query `contracts`, `invoices`, or JOIN both tables as needed based on the user's question.
   - Use :name style placeholders for values if filtering (e.g. :amount, :status).
   - Today's date in PostgreSQL is: CURRENT_DATE
   - Never generate INSERT, UPDATE, DELETE, ALTER, or DROP statements.
   - Return ONLY valid JSON in format: {"sql": "SELECT ...", "params": {}}
"""


def generate_sql_from_prompt(user_prompt: str) -> tuple[str, dict]:
    """
    Uses LLM to convert a natural language prompt into a parameterized SQL query.
    Returns (sql_string, params_dict).
    """
    system_prompt = f"""You are a PostgreSQL SQL expert.
A user will ask a question about contracts or invoices stored in a database.
Your job is to convert it into a safe PostgreSQL SELECT query.

{DATABASE_SCHEMA}

Output format (JSON only, no markdown):
{{"sql": "SELECT ...", "params": {{}}}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Query: {user_prompt}"},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    sql = data.get("sql", "SELECT * FROM contracts")
    params = data.get("params", {})

    #--Safety Guardrail--
    clean_sql=sql.strip()
    clean_sql=clean_sql.upper()
    #1.must be select query 
    if not clean_sql.startswith("SELECT"):
        raise ValueError("only select queries allowed")
    #2.prevent multi statment injection (semicolouns)
    clean_sql=clean_sql.rstrip(";")
    if ";" in clean_sql:
        raise ValueError("Multi Statments are blocked")
    
    #3.Block  destrcutive mutation
    forbidden=["DROP","INSERT","DELETE","ALTER","CREATE","TRUNCATE","GRANT","REVOKE", "UPDATE"]
    for word in forbidden:
        if clean_sql.startswith(word):
            raise ValueError(f"Only SELECT queries are allowed. {word} is blocked.")

    # Auto enforced Limit 50 is missing
    if "LIMIT" not in clean_sql:
        clean_sql=f"{clean_sql} LIMIT 50"
    return clean_sql, params




def execute_db_query(sql: str, params: dict) -> list[dict]:
    """
    Executes a safe parameterized SQL query against PostgreSQL.
    Returns a list of JSON-serializable row dicts.
    """
    with Session(engine) as session:
        result = session.execute(text(sql), params)
        columns = list(result.keys())
        rows = result.fetchall()
        formatted_rows = []
        for row in rows:
            row_dict = {}
            for col, val in zip(columns, row):
                if hasattr(val, "isoformat"):
                    row_dict[col] = val.isoformat()
                elif hasattr(val, "__float__"):
                    row_dict[col] = float(val)
                else:
                    row_dict[col] = val
            formatted_rows.append(row_dict)
        return formatted_rows


def query_database_with_llm(user_prompt: str) -> tuple[list[dict], str]:
    """
    Full pipeline: user_prompt -> LLM -> SQL -> PostgreSQL -> results
    Returns (list of row dicts, the generated SQL string)
    """
    sql, params = generate_sql_from_prompt(user_prompt)
    rows = execute_db_query(sql, params)
    return rows, sql


# Backward compatibility aliases
def query_contracts_with_llm(user_prompt: str) -> tuple[list[dict], str]:
    return query_database_with_llm(user_prompt)


def query_invoices_with_llm(user_prompt: str) -> tuple[list[dict], str]:
    return query_database_with_llm(user_prompt)
