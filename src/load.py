from datetime import datetime
from pathlib import Path

from sqlalchemy import text, insert
from db import engine, accounts, daily_status, monthly_status
import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# tables = {
#     "accounts": accounts,
#     "daily_status": daily_status,
#     "monthly_status": monthly_status,
# }
#
# csv_paths = {
#     "accounts": [Path("data/accounts.csv")],
#     "daily_status": sorted(Path("data").glob("daily_*.csv")),
#     "monthly_status": sorted(Path("data").glob("monthly_*.csv")),
# }

def parse_datetime(df):
    raw = pl.col("changed_datetime")
    serial_days = raw.cast(pl.Float64, strict=False)

    parsed_datetime = pl.coalesce([
        raw.str.strptime(
            pl.Datetime,
            format="%Y-%m-%d %H:%M:%S",
            strict=False,
        ),
        raw.str.strptime(
            pl.Datetime,
            format="%d-%m-%y %H:%M",
            strict=False,
        ),
        pl.lit(datetime(1899, 12, 30))
        + pl.duration(
            microseconds=(serial_days * 86_400_000_000).cast(pl.Int64)
        ),
    ])

    return df.with_columns(parsed_datetime.alias("changed_datetime"))

def prepare_accounts(df):
    return df.with_columns(pl.col("account_id").cast(pl.Int64))

def prepare_daily(df, path):
    file_date = datetime.strptime(path.stem.removeprefix("daily_"), "%Y%m%d").date()
    df = df.with_columns(
        pl.col("account").cast(pl.Int64),
        pl.col("changed_datetime").alias("changed_datetime_raw"),
        pl.lit(path.name).alias("source_file"),
        pl.lit(file_date).alias("file_date"),
        )
    df =parse_datetime(df)


    if df["changed_datetime"].null_count():
        raise ValueError(f"Unrecognized timestamp in {path}")

    return df

def prepare_monthly(df, path):
    snapshot_ym = path.stem.split("_")[1]

    return df.with_columns(
        pl.col("account").cast(pl.Int64),
        pl.col("month").cast(pl.Int64),
        pl.lit(snapshot_ym).alias("snapshot_ym"),
        pl.lit(int(snapshot_ym[:4])).alias("snapshot_year"),
        pl.lit(path.name).alias("source_file"),
    )
def load_table(conn, current_table, paths, prepare_function):
    conn.execute(text(f"TRUNCATE {current_table.name} CASCADE"))
    total_rows = 0
    skipped_files = 0

    for path in paths:
        df = pl.read_csv(path, infer_schema_length=0)

        if df.is_empty():
            skipped_files += 1
            print(f"Skipping empty file: {path}")
            continue

        rows = prepare_function(df,path).to_dicts()
        conn.execute(insert(current_table), rows)
        total_rows += len(rows)

    if skipped_files:
        print(f"!- Skipped {skipped_files} files while loading in {current_table.name}")

    print(total_rows, "rows loaded into ", current_table.name)
    return total_rows

def main():
    jobs = [
        (accounts, [DATA_DIR / "accounts.csv"], prepare_accounts),
        (daily_status, sorted(DATA_DIR.glob("daily_*.csv")), prepare_daily),
        (monthly_status, sorted(DATA_DIR.glob("monthly_*.csv")), prepare_monthly),
    ]

    with engine.begin() as conn:
        for table, paths, prepare in jobs:
            load_table(conn, table, paths, prepare)

if __name__ == "__main__":
    main()








