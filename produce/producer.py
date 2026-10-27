#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterator

CURRENCIES = ("GBP", "USD", "EUR", "INR", "HKD", "SGD")
TRANSACTION_TYPES = ("PURCHASE", "REFUND", "TRANSFER", "WITHDRAWAL", "PAYMENT")
CHANNELS = ("MOBILE", "WEB", "ATM", "BRANCH", "POS")
COUNTRIES = ("GB", "US", "IN", "HK", "SG", "FR", "DE", "AU")
MERCHANT_CATEGORIES = (
    "GROCERIES",
    "TRAVEL",
    "RESTAURANT",
    "UTILITIES",
    "RETAIL",
    "HEALTHCARE",
    "ENTERTAINMENT",
)
STATUSES = ("COMPLETED", "PENDING", "DECLINED")
FIELDNAMES = (
    "transaction_id",
    "customer_id",
    "account_id",
    "transaction_timestamp",
    "transaction_type",
    "amount",
    "currency",
    "channel",
    "country",
    "merchant_category",
    "status",
    "is_cross_border",
    "reference",
    "original_transaction_id",
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def random_amount(
    rng: random.Random,
    minimum: float = 1.0,
    maximum: float = 5000.0,
) -> float:
    if minimum < 0 or maximum < minimum:
        raise ValueError("amount bounds must satisfy 0 <= minimum <= maximum")
    value = Decimal(str(rng.uniform(minimum, maximum)))
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_transaction(
    customer_count: int = 10_000,
    account_count: int = 20_000,
    rng: random.Random | None = None,
    minimum_amount: float = 1.0,
    maximum_amount: float = 5000.0,
) -> dict[str, object]:
    if customer_count < 1:
        raise ValueError("customer_count must be greater than zero")
    if account_count < 1:
        raise ValueError("account_count must be greater than zero")

    generator = rng or random.Random()
    account_number = generator.randint(1, account_count)
    customer_number = (account_number - 1) % customer_count + 1
    transaction_type = generator.choice(TRANSACTION_TYPES)
    transaction_id = f"TXN-{generator.getrandbits(64):016X}"
    transaction_timestamp = utc_timestamp()
    transaction_date = transaction_timestamp[:10].replace("-", "")

    return {
        "transaction_id": transaction_id,
        "customer_id": f"CUST-{customer_number:08d}",
        "account_id": f"ACCT-{account_number:010d}",
        "transaction_timestamp": transaction_timestamp,
        "transaction_type": transaction_type,
        "amount": random_amount(generator, minimum_amount, maximum_amount),
        "currency": generator.choice(CURRENCIES),
        "channel": generator.choice(CHANNELS),
        "country": generator.choice(COUNTRIES),
        "merchant_category": generator.choice(MERCHANT_CATEGORIES),
        "status": generator.choices(STATUSES, weights=(92, 5, 3), k=1)[0],
        "is_cross_border": generator.choice((True, False)),
        "reference": f"REF-{transaction_date}-{uuid.uuid4().hex}",
        "original_transaction_id": (
            str(uuid.UUID(int=generator.getrandbits(128)))
            if transaction_type == "REFUND"
            else None
        ),
    }


def transaction_stream(
    customer_count: int = 10_000,
    account_count: int = 20_000,
    seed: int | None = None,
    minimum_amount: float = 1.0,
    maximum_amount: float = 5000.0,
    duplicate_rate: float = 0.0,
) -> Iterator[dict[str, object]]:
    if not 0.0 <= duplicate_rate <= 1.0:
        raise ValueError("duplicate_rate must be between zero and one")

    rng = random.Random(seed)
    recent_transactions: list[dict[str, object]] = []
    while True:
        if (
            recent_transactions
            and duplicate_rate > 0.0
            and rng.random() < duplicate_rate
        ):
            yield recent_transactions[rng.randrange(len(recent_transactions))].copy()
            continue

        transaction = generate_transaction(
            customer_count, account_count, rng, minimum_amount, maximum_amount
        )
        if len(recent_transactions) == 1_000:
            del recent_transactions[0]
        recent_transactions.append(transaction)
        yield transaction


def write_batch_csv(
    records: int,
    output: Path,
    customer_count: int,
    account_count: int,
    seed: int | None = None,
    minimum_amount: float = 1.0,
    maximum_amount: float = 5000.0,
    duplicate_rate: float = 0.0,
) -> None:
    if records <= 0:
        raise ValueError("records must be greater than zero")
    if not 0.0 <= duplicate_rate <= 1.0:
        raise ValueError("duplicate-rate must be between zero and one")

    output.parent.mkdir(parents=True, exist_ok=True)
    transactions = transaction_stream(
        customer_count,
        account_count,
        seed,
        minimum_amount,
        maximum_amount,
        duplicate_rate,
    )
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _ in range(records):
            writer.writerow(next(transactions))


def write_realtime_jsonl(
    interval: float,
    output: Path | None,
    customer_count: int,
    account_count: int,
    seed: int | None = None,
    minimum_amount: float = 1.0,
    maximum_amount: float = 5000.0,
    duplicate_rate: float = 0.0,
) -> None:
    if interval < 0:
        raise ValueError("interval cannot be negative")
    if not 0.0 <= duplicate_rate <= 1.0:
        raise ValueError("duplicate-rate must be between zero and one")

    transactions = transaction_stream(
        customer_count,
        account_count,
        seed,
        minimum_amount,
        maximum_amount,
        duplicate_rate,
    )
    file_handle = None
    try:
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            file_handle = output.open("a", encoding="utf-8")

        print("Real-time generation started. Press Ctrl+C to stop.", file=sys.stderr)
        for transaction in transactions:
            line = json.dumps(transaction, separators=(",", ":"))
            destination = file_handle if file_handle is not None else sys.stdout
            destination.write(line + "\n")
            destination.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Real-time generation stopped.", file=sys.stderr)
    finally:
        if file_handle is not None:
            file_handle.close()


def add_data_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--customer-count",
        "--customers",
        dest="customer_count",
        type=int,
        default=10_000,
    )
    parser.add_argument(
        "--account-count", "--accounts", dest="account_count", type=int, default=20_000
    )
    parser.add_argument("--minimum-amount", type=float, default=1.0)
    parser.add_argument("--maximum-amount", type=float, default=5000.0)
    parser.add_argument("--duplicate-rate", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    batch_parser = subparsers.add_parser("batch")
    batch_parser.add_argument("--records", type=int, default=10_000)
    batch_parser.add_argument("--output", type=Path, default=None)
    batch_parser.add_argument("--output-dir", type=Path, default=Path("files"))
    add_data_arguments(batch_parser)

    realtime_parser = subparsers.add_parser("realtime")
    realtime_parser.add_argument("--interval", type=float, default=1.0)
    realtime_parser.add_argument("--output", type=Path, default=None)
    add_data_arguments(realtime_parser)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.customer_count <= 0:
            raise ValueError("customer-count must be greater than zero")
        if args.account_count <= 0:
            raise ValueError("account-count must be greater than zero")

        if args.mode == "batch":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = args.output or (
                args.output_dir / f"transactions_{timestamp}.csv"
            )
            write_batch_csv(
                args.records,
                output_path,
                args.customer_count,
                args.account_count,
                args.seed,
                args.minimum_amount,
                args.maximum_amount,
                args.duplicate_rate,
            )
            print(f"Wrote {args.records:,} transactions to {output_path}")
        else:
            write_realtime_jsonl(
                args.interval,
                args.output,
                args.customer_count,
                args.account_count,
                args.seed,
                args.minimum_amount,
                args.maximum_amount,
                args.duplicate_rate,
            )
        return 0
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
