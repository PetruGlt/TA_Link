DROP TABLE IF EXISTS recent_queue_status_updates;
CREATE TABLE recent_queue_status_updates AS
    WITH daily_state AS (
        SELECT DISTINCT ON (account)
               account,
               queue,
               status,
               changed_datetime
        FROM daily_status
        WHERE changed_datetime < TIMESTAMP '2025-11-28 00:00:00'
        ORDER BY account, changed_datetime DESC
    ),
    snap_state AS (
        SELECT DISTINCT ON (account)
               account,
               queue,
               status,
               snapshot_year,
               month,
               snapshot_ym
        FROM monthly_status
        WHERE snapshot_ym <= '202510'
        ORDER BY account, snapshot_ym DESC
    ),
    state AS (
        SELECT COALESCE(d.account, s.account)
                   AS account,
               COALESCE(d.queue, s.queue)
                   AS queue,
               COALESCE(d.status, s.status)
                   AS status,
               d.changed_datetime
                   AS last_change_datetime,
               CASE WHEN d.account IS NOT NULL
                   THEN 'daily'
                   ELSE 'monthly'
               END AS state_source

        FROM daily_state d
        FULL JOIN snap_state s ON s.account = d.account
    )
    SELECT a.account_id, a.name, a.address,
           st.queue, st.status, st.last_change_datetime,
           st.state_source
    FROM state st
    JOIN accounts a ON a.account_id = st.account
    WHERE st.queue IN ('COLLECTIONS', 'LEGAL') and a.account_id <> 99999;

