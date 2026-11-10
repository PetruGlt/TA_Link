-- basic
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM daily_status d
JOIN accounts a ON a.account_id = d.account
WHERE d.account IN (
    SELECT account FROM daily_status WHERE queue IN ('COLLECTIONS', 'LEGAL')
);
-- execution_time | buffers
-- 1.267, 103
-- 1.396, 103
-- 1.273, 103
-- 1.638, 103
-- 1.521, 103

-- only necessary columns
EXPLAIN (ANALYZE, BUFFERS)
SELECT d.account, d.queue, d.status, d.changed_datetime, a.name, a.address
FROM daily_status d
JOIN accounts a ON a.account_id = d.account
WHERE d.account IN (
    SELECT account FROM daily_status WHERE queue IN ('COLLECTIONS', 'LEGAL')
);
-- execution_time | buffers
-- 1.217, 103
-- 1.224, 103
-- 1.495, 103
-- 1.199, 103

-- index
CREATE INDEX idx_daily_queue_account ON daily_status (queue, account);
ANALYZE daily_status;

-- again, only necessary values
EXPLAIN (ANALYZE, BUFFERS)
SELECT d.account, d.queue, d.status, d.changed_datetime, a.name, a.address
FROM daily_status d
JOIN accounts a ON a.account_id = d.account
WHERE d.account IN (
    SELECT account FROM daily_status WHERE queue IN ('COLLECTIONS', 'LEGAL')
);
-- execution_time | buffers
-- 1.306, 56
-- 1.151, 62
-- 1.124, 62
-- 1.247, 62
-- 1.277, 62