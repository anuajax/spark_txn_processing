from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

from transaction_etl.io.schemas import TRANSACTION_SCHEMA


def read_transactions(spark: SparkSession, input_path: Path | None) -> DataFrame:
    if input_path is None:
        raise ValueError("input_path is required")

    return (
        spark.read.option("header", "true")
        .option("mode", "PERMISSIVE")
        .option("timestampFormat", "yyyy-MM-dd'T'HH:mm:ss.SSSXXX")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .schema(TRANSACTION_SCHEMA)
        .csv(str(input_path))
    )
