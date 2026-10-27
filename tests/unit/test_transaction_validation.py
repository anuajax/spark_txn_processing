from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from transaction_etl.validation.transactions import validate_transactions


def test_validate_transactions_separates_invalid_records() -> None:
    spark = SparkSession.builder.master("local[1]").appName(
        "transaction-validation-test"
    ).getOrCreate()
    source = spark.sql(
        """
        SELECT 'TXN-VALID' AS transaction_id, CAST(12.50 AS DECIMAL(12, 2)) AS amount,
               CAST(NULL AS STRING) AS _corrupt_record
        UNION ALL
        SELECT 'TXN-ZERO', CAST(0.00 AS DECIMAL(12, 2)), CAST(NULL AS STRING)
        UNION ALL
        SELECT CAST(NULL AS STRING), CAST(10.00 AS DECIMAL(12, 2)), CAST(NULL AS STRING)
        UNION ALL
        SELECT '   ', CAST(10.00 AS DECIMAL(12, 2)), CAST(NULL AS STRING)
        UNION ALL
        SELECT 'TXN-BAD-SCHEMA', CAST(NULL AS DECIMAL(12, 2)), 'malformed'
        """
    )

    try:
        valid, rejected = validate_transactions(source)

        assert valid.count() == 1
        assert valid.filter(col("transaction_id") != "TXN-VALID").count() == 0
        assert rejected.count() == 4
        assert rejected.filter(col("reason") == "Schema mismatch").count() == 1
        assert (
            rejected.filter(col("reason") == "Invalid amount or transaction_id").count()
            == 3
        )
    finally:
        spark.stop()
