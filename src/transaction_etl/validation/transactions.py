from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, trim


def validate_transactions(transactions: DataFrame) -> tuple[DataFrame, DataFrame]:
    rejected_records = transactions.filter(transactions["_corrupt_record"].isNotNull())
    valid_records = transactions.filter(transactions["_corrupt_record"].isNull())

    rejected_records = (
        rejected_records.withColumn("valid", lit(False))
        .withColumn("reason", lit("Schema mismatch"))
        .select(col("transaction_id"), col("valid"), col("reason"))
    )

    invalid_condition = (
        col("amount").isNull()
        | (col("amount") <= 0)
        | col("transaction_id").isNull()
        | (trim(col("transaction_id")) == "")
    )
    invalid_records = (
        valid_records.filter(invalid_condition)
        .withColumn("valid", lit(False))
        .withColumn("reason", lit("Invalid amount or transaction_id"))
        .select(col("transaction_id"), col("valid"), col("reason"))
    )

    valid_records = valid_records.filter(~invalid_condition).withColumn(
        "valid", lit(True)
    )

    rejected_records = rejected_records.unionAll(invalid_records)

    return valid_records, rejected_records
