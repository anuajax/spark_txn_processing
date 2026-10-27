import csv
import random
from datetime import datetime
from decimal import Decimal

import pytest

from produce.acct_producer import FIELDNAMES, generate_account, write_batch_csv
from transaction_etl.io.schemas import ACCOUNT_SCHEMA


def test_account_schema_matches_producer_fields() -> None:
    assert tuple(field.name for field in ACCOUNT_SCHEMA.fields[:-1]) == FIELDNAMES
    assert ACCOUNT_SCHEMA["current_balance"].dataType.simpleString() == "decimal(14,2)"


def test_generate_account_is_repeatable_and_links_customer() -> None:
    first = generate_account(12, customer_count=3, rng=random.Random(5))
    second = generate_account(12, customer_count=3, rng=random.Random(5))

    assert first == second
    assert first["account_id"] == "ACCT-0000000012"
    assert first["customer_id"] == "CUST-00000003"
    balance = Decimal(first["current_balance"])
    assert Decimal("-5000") <= balance <= Decimal("100000")
    assert balance.as_tuple().exponent == -2
    assert datetime.fromisoformat(first["opened_at"]).tzinfo is not None
    if first["closed_at"] is not None:
        assert datetime.fromisoformat(first["closed_at"]).tzinfo is not None


def test_generate_account_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="account_number"):
        generate_account(0)
    with pytest.raises(ValueError, match="customer_count"):
        generate_account(1, customer_count=0)


def test_write_batch_csv_outputs_schema_columns(tmp_path) -> None:
    output = tmp_path / "nested" / "accounts.csv"

    write_batch_csv(2, output, customer_count=1, seed=3)

    with output.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        rows = list(reader)
    assert tuple(reader.fieldnames) == FIELDNAMES
    assert len(rows) == 2
    assert [row["account_id"] for row in rows] == [
        "ACCT-0000000001",
        "ACCT-0000000002",
    ]
    assert all(row["customer_id"] == "CUST-00000001" for row in rows)
