#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CURRENCIES = ("GBP", "USD", "EUR", "INR", "HKD", "SGD")
ACCOUNT_TYPES = ("CHECKING", "SAVINGS", "CREDIT")
ACCOUNT_STATUSES = ("ACTIVE", "FROZEN", "CLOSED")
FIELDNAMES = (
    "account_id",
    "customer_id",
    "account_type",
    "currency",
    "account_status",
    "opened_at",
    "closed_at",
    "current_balance",
)


def _format_timestamp(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def generate_account(
    account_number: int,
    customer_count: int = 10_000,
    rng: random.Random | None = None,
) -> dict[str, str | None]:
    if account_number < 1:
        raise ValueError("account_number must be greater than zero")
    if customer_count < 1:
        raise ValueError("customer_count must be greater than zero")

    generator = rng or random.Random()
    now = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    opened_at = now - timedelta(days=generator.randint(0, 3650))
    account_status = generator.choices(
        ACCOUNT_STATUSES, weights=(92, 5, 3), k=1
    )[0]
    closed_at = (
        _format_timestamp(
            opened_at
            + timedelta(
                seconds=generator.randint(
                    0, max(0, int((now - opened_at).total_seconds()))
                )
            )
        )
        if account_status == "CLOSED"
        else None
    )
    balance = Decimal(str(generator.uniform(-5000, 100000))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "account_id": f"ACCT-{account_number:010d}",
        "customer_id": f"CUST-{(account_number - 1) % customer_count + 1:08d}",
        "account_type": generator.choice(ACCOUNT_TYPES),
        "currency": generator.choice(CURRENCIES),
        "account_status": account_status,
        "opened_at": _format_timestamp(opened_at),
        "closed_at": closed_at,
        "current_balance": f"{balance:.2f}",
    }


def write_batch_csv(
    records: int,
    output: Path,
    customer_count: int = 10_000,
    seed: int | None = None,
) -> None:
    if records <= 0:
        raise ValueError("records must be greater than zero")
    if customer_count <= 0:
        raise ValueError("customer_count must be greater than zero")

    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for account_number in range(1, records + 1):
            writer.writerow(generate_account(account_number, customer_count, rng))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic account data.")
    parser.add_argument("--records", type=int, default=20_000)
    parser.add_argument("--customer-count", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("files"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.records <= 0:
        parser.error("records must be greater than zero")
    if args.customer_count <= 0:
        parser.error("customer-count must be greater than zero")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = args.output or (args.output_dir / f"accounts_{timestamp}.csv")
    write_batch_csv(args.records, output_path, args.customer_count, args.seed)
    print(f"Wrote {args.records:,} accounts to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
