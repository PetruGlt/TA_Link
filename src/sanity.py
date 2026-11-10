from sqlalchemy import text

from db import engine

CHECKS = [
    (
        "number of rows",
        """
        select 'accounts' as tbl, COUNT(*) AS n FROM accounts
        UNION ALL select 'daily_status', COUNT(*) from daily_status
        UNION ALL select 'monthly_status', COUNT(*) from monthly_status
        """,
    ),
    (
        "empty or null queue or status - daily_status",
        """
        SELECT SUM((queue IS NULL OR TRIM(queue) = '')::int) as no_queue,
               SUM((status IS NULL OR TRIM(status) = '')::int) as no_status,
               COUNT(*) as total
        FROM daily_status
        """,
    ),
    (
        "empty or null queue or status - monthly_status",
        """
        select SUM((queue is null or TRIM(queue) = '')::int) AS no_queue,
               SUM((status is null or TRIM(status) = '')::int) as no_status,
               COUNT(*) as total
        from monthly_status
        """,
    ),
    (
        "Dupe ids in accounts",
        """
        select account_id, COUNT(*) from accounts
        group by 1 having COUNT(*) > 1
        """,
    ),
    (
        "Dupes on (account,changed_datetime) in daily_status",
        """
        select account, changed_datetime, COUNT(*)
        FROM daily_status
        group by 1, 2 having COUNT(*) > 1
        """,
    ),
    (
        "duplicate rows in daily_status",
        """
        select account, queue, status, changed_datetime, COUNT(*)
        from daily_status
        group by 1, 2, 3, 4 having COUNT(*) > 1
        """,
    ),
    (
        "Duplicates on (account, snapshot_ym) - monthly_status",
        """
        select account, snapshot_ym, COUNT(*)
        from monthly_status
        GROUP BY 1, 2 having COUNT(*) > 1
        """,
    ),
    (
        "accounts that are in daily_status but not in accounts",
        """
        select distinct account FROM daily_status
        WHERE account NOT IN (select account_id from accounts)
        """,
    ),
    (
        "accounts that are in monthly_status but not in accounts",
        """
        select distinct account from monthly_status
        where account not in (select account_id FROM accounts)
        """,
    ),
    (
        "spaces in accounts",
        """
        select account_id, name, address from accounts
        where name <> TRIM(name) or address <> TRIM(address)
        """,
    ),
    (
        "distinct queues - daily_status",
        "select queue, COUNT(*) FROM daily_status group by 1 ORDER BY 1",
    ),
    (
        "Distinct queues - monthly_status",
        "select queue, COUNT(*) FROM monthly_status group by 1 ORDER BY 1",
    ),
    (
        "queue/status combinations - daily_status",
        """
        select queue, status, COUNT(*) from daily_status
        group by 1, 2 order by 1, 3 desc
        """,
    ),
    (
        "date range of daily_status",
        """
        select MIN(changed_datetime) as min_dt,
               MAX(changed_datetime) as max_dt,
               MAX(file_date) as last_file_date
        from daily_status
        """,
    ),
    (
        "changed_datetime date different from file_date",
        """
        select source_file, changed_datetime_raw, changed_datetime, file_date
        from daily_status
        where changed_datetime::date <> file_date
        order by changed_datetime
        limit 50
        """,
    ),
    (
        "Raw datetime formats in daily_status",
        """
        select LENGTH(changed_datetime_raw) as len,
               MIN(changed_datetime_raw) as example,
               COUNT(*)
        from daily_status group by 1 order by 1
        """,
    ),
    (
        "check years in daily_status",
        """
        select * from daily_status
        where EXTRACT(year from changed_datetime) not in (2024, 2025)
        limit 50
        """,
    ),
    (
        "Snapshots per file and month consistency",
        """
        select snapshot_ym,
               COUNT(*) as n,
               SUM((month <> RIGHT(snapshot_ym, 2)::int)::int) as month_mismatch
        from monthly_status group by 1 order by 1
        """,
    ),
    (
        "NULL snapshot_ts in monthly_status",
        "select COUNT(*) from monthly_status where snapshot_ts is null",
    ),
    (
        "snapshot_ts range per snapshot_ym",
        """
        select snapshot_ym, MIN(snapshot_ts), MAX(snapshot_ts)
        from monthly_status group by 1 order by 1
        """,
    ),
    (
        "account with id 99999 in raw tables",
        """
        select 'accounts' as tbl, COUNT(*) from accounts where account_id = 99999
        union all select 'daily_status', COUNT(*) from daily_status where account = 99999
        union all select 'monthly_status', COUNT(*) from monthly_status where account = 99999
        """,
    ),
    (
        "daily vs snapshot 202510 consistency",
        """
        with d as (
            select distinct on (account) account, queue, status
            from daily_status
            where changed_datetime < TIMESTAMP '2025-11-01'
            order by account, changed_datetime desc
        )
        select COUNT(*) filter (where d.queue =m.queue and d.status= m.status) as match,
               COUNT(*) filter (where d.queue <> m.queue or d.status <> m.status) as mismatch
        from d join monthly_status m
          on m.account = d.account and m.snapshot_ym = '202510'
        """,
    ),
    (
        "accounts only in monthly_status (no daily rows)",
        """
        select COUNT(distinct account) from monthly_status
        where account not in (select distinct account from daily_status)
        """,
    ),
]


def run_check(conn, title, sql):
    result = conn.execute(text(sql))
    columns = list(result.keys())
    rows = result.fetchall()

    print(f"\n--- {title} ---")
    if not rows:
        print("OK: 0 rows")
        return

    print(" | ".join(columns))
    for row in rows:
        print(" | ".join(str(value) for value in row))


def main():
    with engine.connect() as conn:
        for title, sql in CHECKS:
            run_check(conn, title, sql)


if __name__ == "__main__":
    main()