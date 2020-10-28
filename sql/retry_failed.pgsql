delete from descriptions where id in (select id from replays where failed = true);
delete from job where id in (select id from replays where failed = true);
update replays
    set failed = false, status = 'ADDED'
    where created = false and failed = TRUE