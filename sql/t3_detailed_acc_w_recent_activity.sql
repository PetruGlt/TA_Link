-- 3. Join the data from the 2nd task with the accounts file to include account details
drop table if exists accounts_w_recent_activity;

create table accounts_w_recent_activity as
select distinct on (d.account)
    a.account_id,
    a.name,
    a.address,
    d.changed_datetime as latest_update_datetime,
    d.status,
    d.queue
from daily_status d
join accounts a on d.account = a.account_id
where d.changed_datetime >= TIMESTAMP '2025-01-01 00:00:00' and a.account_id <> 99999 order by d.account, d.changed_datetime desc;