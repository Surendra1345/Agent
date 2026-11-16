import pytest

from agent.services.text_to_sql import validate_select_sql


def test_keeps_case_and_params_and_adds_limit():
    out = validate_select_sql("SELECT * FROM invoices WHERE status = :status AND note = 'limit x'")
    assert ":status" in out and "'limit x'" in out
    assert out.upper().endswith("LIMIT 50")


def test_existing_limit_is_kept():
    out = validate_select_sql("SELECT * FROM contracts ORDER BY contract_amount DESC LIMIT 3")
    assert out.upper().endswith("LIMIT 3")


def test_join_and_cte_allowed():
    validate_select_sql(
        "WITH t AS (SELECT * FROM invoices) SELECT c.contract_id FROM contracts c JOIN t ON t.contract_id = c.contract_id"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE contracts",
        "SELECT 1; DROP TABLE contracts",
        "WITH x AS (DELETE FROM invoices RETURNING *) SELECT * FROM x",
        "SELECT pg_sleep(100)",
        "SELECT lo_import('/etc/passwd')",
        "SELECT * FROM pg_user",
        "SELECT * FROM contracts INTO OUTFILE 'x'",
        "not sql at all (((",
    ],
)
def test_blocked(sql):
    with pytest.raises(ValueError):
        validate_select_sql(sql)
