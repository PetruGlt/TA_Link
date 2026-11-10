-- FIX for monthly timestamps
ALTER TABLE monthly_status ADD COLUMN snapshot_ts timestamp(0);

UPDATE monthly_status
SET snapshot_ts = to_date(snapshot_ym || '01', 'YYYYMMDD') + INTERVAL '1 month'
WHERE snapshot_ts IS NULL;

-- 4. The most recent queue and/or status change for accounts that as of 2025-11-27 are in queues "COLLECTIONS" and "LEGAL"
DROP TABLE IF EXISTS recent_queue_status_updates;

CREATE TABLE recent_queue_status_updates AS
WITH evidence AS (
    SELECT account,
           queue,
           status,
           changed_datetime AS effective_ts,
           changed_datetime AS last_change_datetime,
           'daily' AS state_source,
           source_file
    FROM daily_status
    WHERE changed_datetime < TIMESTAMP '2025-11-28 00:00:00'

    UNION ALL

    SELECT account,
           queue,
           status,
           snapshot_ts AS effective_ts,
           NULL::timestamp AS last_change_datetime,
           'monthly' AS state_source,
           source_file
    FROM monthly_status
    WHERE snapshot_ts <= TIMESTAMP '2025-11-28 00:00:00'
),
state AS (
    SELECT DISTINCT ON (account) *
    FROM evidence
    ORDER BY account, effective_ts DESC, state_source
),
last_daily AS (
    SELECT account, MAX(changed_datetime) AS last_known_daily_change
    FROM daily_status
    WHERE changed_datetime < TIMESTAMP '2025-11-28 00:00:00'
    GROUP BY account
)
SELECT a.account_id, a.name, a.address,
       st.queue, st.status,
       ld.last_known_daily_change,
       st.effective_ts AS state_as_of,
       st.state_source, st.source_file
FROM state st
JOIN accounts a ON a.account_id = st.account
LEFT JOIN last_daily ld ON ld.account = st.account
WHERE st.queue IN ('COLLECTIONS', 'LEGAL')
  AND a.account_id <> 99999;