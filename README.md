# Transaction ETL

A PySpark batch pipeline for validating, cleaning, and aggregating synthetic
bank transaction data. The project uses a `src` package layout.

## Project layout

- `src/transaction_etl/jobs`: batch pipeline entry point.
- `src/transaction_etl/io`: CSV readers, schemas, and Parquet writers.
- `src/transaction_etl/transformations`: transaction cleaning and aggregation.
- `src/transaction_etl/validation`: transaction schema and business validation.
- `produce`: scripts that generate synthetic transaction and account CSVs.
- `configs`: environment-specific settings.
- `tests`: unit and integration test suites.

## Set up

From the project root, activate your virtual environment and install the project
with its test dependencies:

```shell
python -m pip install -e ".[test]"
```

For Windows, running Spark locally through WSL/Linux avoids Hadoop's Windows
native file-writing issues. Use a Linux virtual environment inside WSL rather
than reusing the Windows `venv`.

## Generate sample data

Generate transactions:

```shell
python produce/producer.py batch --records 1000 --seed 42
```

This writes a timestamped `transactions_*.csv` file under `files/`.

Generate accounts:

```shell
python produce/acct_producer.py --records 20000 --customer-count 10000 --seed 42
```

This writes a timestamped `accounts_*.csv` file under `files/` by default.
Use `--output path/to/accounts.csv` to choose an exact output filename, or
`--output-dir path/to/directory` to change the destination directory.
`ACCOUNT_SCHEMA` is defined in `src/transaction_etl/io/schemas.py`; the account
producer currently generates sample account data, but there is not yet an
account ingestion pipeline.

## Run the transaction batch pipeline

Pass the transaction CSV path as a positional argument:

```shell
python -m transaction_etl.jobs.batch "files/transactions_YYYYMMDD_HHMMSS.csv"
```

Replace the example filename with the actual generated file. You can also
specify the output directory:

```shell
python -m transaction_etl.jobs.batch "files/transactions_YYYYMMDD_HHMMSS.csv" \
  --output-path "$HOME/transactions-output"
```

The pipeline applies the explicit transaction schema, rejects malformed rows,
filters records with missing/blank IDs or non-positive amounts, trims IDs,
removes duplicate transaction IDs, and derives `transaction_date`. It writes:

- cleaned transactions to the output directory;
- rejected rows and validation reasons to `rejected/`;
- totals and transaction counts grouped by account and transaction date to
  `aggregated/`.

The default output directory is `data/processed/transactions`. Writes use
overwrite mode, so choose a different output path if you want to preserve an
earlier run.

To keep Spark alive and inspect its UI:

```shell
python -m transaction_etl.jobs.batch "files/transactions_YYYYMMDD_HHMMSS.csv" \
  --output-path "$HOME/transactions-output" \
  --keep-alive
```

Open the Spark UI URL printed by the job (usually `http://localhost:4040`) in
your browser while the terminal is waiting. Press Enter in the terminal to stop
Spark.

## Tests

Run the test suite with:

```shell
python -m pytest
```
