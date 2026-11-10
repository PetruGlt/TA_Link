from datetime import datetime
from pathlib import Path

from sqlalchemy import text, insert
from db import engine, accounts, daily_status, monthly_status
import polars as pl

tables = {
    "accounts": accounts,
    "daily_status": daily_status,
    "monthly_status": monthly_status,
}

csv_paths = {
    "accounts": [Path("data/accounts.csv")],
    "daily_status": sorted(Path("data").glob("daily_*.csv")),
    "monthly_status": sorted(Path("data").glob("monthly_*.csv")),
}

for name, paths in csv_paths.items():
    current_table = tables[name]
    total_rows = 0

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {name} CASCADE"))

        for path in paths:
            df = pl.read_csv(path, infer_schema_length=0)

            if df.is_empty():
                print(f"Skipping empty file: {path}")
                continue

            account_column = "account_id" if name == "accounts" else "account"

            df = df.with_columns(pl.col(account_column).cast(pl.Int64))

            if name == "daily_status":
                file_date = datetime.strptime(path.stem.removeprefix("daily_"), "%Y%m%d").date()

                df = df.with_columns(pl.col("changed_datetime").alias("changed_datetime_raw"),
                                     pl.lit(path.name).alias("source_file"),
                                     pl.lit(file_date).alias("file_date"),
                                     )

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

                df = df.with_columns(parsed_datetime.alias("changed_datetime"))

                if df["changed_datetime"].null_count():
                    raise ValueError(f"Unrecognized timestamp in {path}")


            elif name == "monthly_status":

                snapshot_ym = path.stem.split("_")[1]

                df = df.with_columns(
                    pl.col("month").cast(pl.Int64),
                    pl.lit(snapshot_ym).alias("snapshot_ym"),
                    pl.lit(int(snapshot_ym[:4])).alias("snapshot_year"),
                    pl.lit(path.name).alias("source_file"),
                )

            rows = df.to_dicts()
            # if not rows:
            #     print(f"Skipping empty file: {path}")
            #     continue

            conn.execute(insert(current_table), rows)
            total_rows += len(rows)

    print(total_rows, " rows loaded into ", name)





