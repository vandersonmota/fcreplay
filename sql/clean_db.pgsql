-- WARNING! THIS WILL DELETE ALL DATA!
DELETE FROM replays;
DELETE FROM job WHERE id NOT IN (SELECT id FROM replays);
DELETE FROM descriptions WHERE id NOT IN (SELECT id FROM replays);
DELETE FROM character_detect WHERE challenge_id NOT IN (SELECT id FROM replays);
