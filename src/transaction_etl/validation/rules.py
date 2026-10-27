from collections.abc import Sequence

from pyspark.sql import Column


def transaction_rules() -> Sequence[Column]:
    raise NotImplementedError
