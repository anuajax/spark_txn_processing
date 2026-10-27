from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, sum, to_date, trim


def transform_transactions(transactions: DataFrame) -> DataFrame:
    cleaned = (
        transactions.withColumn("transaction_id", trim(col("transaction_id")))
        .withColumn("customer_id", trim(col("customer_id")))
        .withColumn("account_id", trim(col("account_id")))
        .filter(col("transaction_id").isNotNull() & (col("transaction_id") != ""))
        .filter(col("amount").isNotNull() & (col("amount") > 0))
        .dropDuplicates(["transaction_id"])
        .drop("_corrupt_record")
    )
    cleaned = cleaned.withColumn(
        "transaction_date", to_date(col("transaction_timestamp"))
    )
    return cleaned


def aggregate_transactions(df: DataFrame) -> DataFrame:
    acctlevel = (
        df.groupBy("account_id", "transaction_date")
        .agg(
            sum("amount").alias("total_amount"),
            count("transaction_id").alias("transaction_count"),
        )
        .withColumn("total_amount", col("total_amount").cast("decimal(12,2)"))
    )
    return acctlevel
