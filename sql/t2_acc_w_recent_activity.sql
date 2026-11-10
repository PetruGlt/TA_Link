-- 2. Accounts with activity on/after 2025-01-01

select distinct on (account) account, changed_datetime, status, queue
from daily_status
where changed_datetime >= TIMESTAMP '2025-01-01 00:00:00' and account <> 99999 order by account, changed_datetime desc;



