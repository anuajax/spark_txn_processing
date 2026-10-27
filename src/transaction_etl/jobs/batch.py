import argparse
from pathlib import Path

from pyspark.sql import SparkSession

from transaction_etl.io.readers import read_transactions
from transaction_etl.io.writers import write_df, write_transactions
from transaction_etl.transformations.transactions import transform_transactions
from transaction_etl.transformations.transactions import aggregate_transactions
from transaction_etl.validation.transactions import validate_transactions


def run(spark: SparkSession, input_path: Path | None, output_path: Path):
    source = read_transactions(spark, input_path)
    validated, rejected = validate_transactions(source)
    cleaned = transform_transactions(validated)
    aggregated = aggregate_transactions(cleaned)
    write_transactions(cleaned, rejected, output_path)
    write_df(aggregated, output_path, "aggregated")
    return cleaned, aggregated, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the transaction batch ETL job.")
    parser.add_argument("input_path", type=Path)
    parser.add_argument(
        "--output-path", type=Path, default=Path("data/processed/transactions")
    )
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep Spark running so its web UI can be inspected.",
    )
    args = parser.parse_args()

    spark = SparkSession.builder.appName("TransactionETL").getOrCreate()
    try:
        transactions, acctlevel, _rejected = run(
            spark, args.input_path, args.output_path
        )
        print(f"Wrote transformed data to {args.output_path}")

        transactions.printSchema()
        acctlevel.show(5, truncate=False)

        if args.keep_alive:
            print(f"Spark UI: {spark.sparkContext.uiWebUrl}")
            input("Press Enter to stop Spark...")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
