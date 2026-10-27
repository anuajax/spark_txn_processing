from pathlib import Path

from pyspark.sql import DataFrame


def write_transactions(
    transactions: DataFrame, rejected: DataFrame, output_path: Path
) -> None:
    transactions.write.mode("overwrite").parquet(str(output_path))
    rejected.write.mode("overwrite").parquet(str(output_path / "rejected"))


def write_df(df: DataFrame, output_path: Path, name: str) -> None:
    df.write.mode("overwrite").parquet(str(output_path / name))
