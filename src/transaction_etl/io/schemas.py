from pyspark.sql.types import (
    BooleanType,
    DecimalType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

TRANSACTION_SCHEMA = StructType(
    [
        StructField("transaction_id", StringType(), nullable=False),
        StructField("customer_id", StringType(), nullable=False),
        StructField("account_id", StringType(), nullable=False),
        StructField("transaction_timestamp", TimestampType(), nullable=False),
        StructField("transaction_type", StringType(), nullable=False),
        StructField("amount", DecimalType(12, 2), nullable=False),
        StructField("currency", StringType(), nullable=False),
        StructField("channel", StringType(), nullable=False),
        StructField("country", StringType(), nullable=False),
        StructField("merchant_category", StringType(), nullable=False),
        StructField("status", StringType(), nullable=False),
        StructField("is_cross_border", BooleanType(), nullable=False),
        StructField("reference", StringType(), nullable=False),
        StructField("original_transaction_id", StringType(), nullable=True),
        StructField("_corrupt_record", StringType(), nullable=True),
    ]
)

ACCOUNT_SCHEMA = StructType(
    [
        StructField("account_id", StringType(), nullable=False),
        StructField("customer_id", StringType(), nullable=False),
        StructField("account_type", StringType(), nullable=False),
        StructField("currency", StringType(), nullable=False),
        StructField("account_status", StringType(), nullable=False),
        StructField("opened_at", TimestampType(), nullable=False),
        StructField("closed_at", TimestampType(), nullable=True),
        StructField("current_balance", DecimalType(14, 2), nullable=False),
        StructField("_corrupt_record", StringType(), nullable=True),
    ]
)
