update replays
    set failed = false, status = 'ADDED'
    where created = false and status not like 'ADDED'