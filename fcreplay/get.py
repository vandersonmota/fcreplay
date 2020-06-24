#!/usr/bin/env python3
import requests
import datetime
import json
import sys
import sqlite3
from retrying import retry
import logging
import time

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

@retry(wait_random_min=5000, wait_random_max=10000, stop_max_attempt_number=3)
def get_data(url):
    r = requests.get(url)
    if r.status_code == 500:
        logging.error("500 Code, trying up to 3 times")
        raise IOError("Unable to get data")
    else:
        return r


def addreplay(row, player_replay=False):
    # Connect to sqlite3
    sql_conn = sqlite3.connect(f"{config['fcreplay_dir']}/{config['sqlite_db']}")
    c = sql_conn.cursor()

    ftr = [3600, 60, 1]
    time = sum([a*b for a,b in zip(ftr, map(int,row[7].split(':')))])
    date_old = datetime.datetime.strptime(row[0], "%d %b %Y %H:%M:%S")
    date_formated = date_old.strftime("%Y_%m_%d-%H-%M-%S")
    date_now = str(datetime.datetime.today())
    fightcade_id = row[2]
    p1_loc = row[3]
    p1 = row[4]
    p2_loc = row[5]
    p2 = row[6]
    if player_replay:
        fc_data=(fightcade_id, p1_loc, p2_loc, p1, p2, date_formated, date_old, time, 'no', 'no', 'added', date_now, 'yes')
    else:
        fc_data=(fightcade_id, p1_loc, p2_loc, p1, p2, date_formated, date_old, time, 'no', 'no', 'added', date_now, 'no')

    # Insert into sqlite
    logging.info(f"Looking for {fc_data[0]}")
    c.execute('SELECT id FROM replays WHERE id=?', (fc_data[0],))
    data = c.fetchone()
    if data is None:
        # Don't bother with videos shorter than 60 seconds
        if time > 60:
            logging.info(f"Adding {fc_data[0]} to queue")
            c.execute('INSERT INTO replays VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', fc_data)
            sql_conn.commit()
            if player_replay:
                sql_conn.close()
                return('ADDED')
        else:
            logging.info(f"{fc_data[0]} is only {time} not adding")
            if player_replay:
                sql_conn.close()
                return('TOO_SHORT')
    
    else:
        logging.info(f"{fc_data[0]} already exists")
        if player_replay:
            sql_conn.close()
            return('ALREADY_EXISTS')
    
    sql_conn.close()


def check_player_record_status(challenge):
    sql_conn = sqlite3.connect(f"{config['fcreplay_dir']}/{config['sqlite_db']}")
    c = sql_conn.cursor()
    c.execute('SELECT id FROM replays WHERE id=?', (challenge,))
    data = c.fetchone()
    i = 0
    while data is not None:
        i += i
        return('added', i)
        



def check_for_profile(profile):
    r = requests.get(f"https://www.fightcade.com/id/{profile}")
    if "PROFILE NOT FOUND" in r.text:
        logging.error(f"Unable to find profile: {profile}")
        raise LookupError

def get_replays(fc_profile):
    replays = []
    profile = fc_profile
    epoch = datetime.datetime.utcfromtimestamp(0)

    # Check if user exists
    check_for_profile(profile)

    # Get replays
    for i in range(0, int(config['replay_pages'])):
        page = i * 10
        ms_time = str(int((datetime.datetime.now() - epoch).total_seconds() * 1000))
        # This could probably be better. But it works for usernames fine.
        url=f"https://www.fightcade.com/replay/server_processing.php?draw=6&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bname%5D=date&columns%5B0%5D%5Bsearchable%5D=false&columns%5B0%5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=1&columns%5B1%5D%5Bname%5D=channel&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=sfiii3n&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=2&columns%5B2%5D%5Bname%5D=quark&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=false&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=3&columns%5B3%5D%5Bname%5D=p1_country&columns%5B3%5D%5Bsearchable%5D=false&columns%5B3%5D%5Borderable%5D=false&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=4&columns%5B4%5D%5Bname%5D=player1&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=5&columns%5B5%5D%5Bname%5D=p2_country&columns%5B5%5D%5Bsearchable%5D=false&columns%5B5%5D%5Borderable%5D=false&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=6&columns%5B6%5D%5Bname%5D=player2&columns%5B6%5D%5Bsearchable%5D=true&columns%5B6%5D%5Borderable%5D=true&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=7&columns%5B7%5D%5Bname%5D=duration&columns%5B7%5D%5Bsearchable%5D=false&columns%5B7%5D%5Borderable%5D=true&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=8&columns%5B8%5D%5Bname%5D=realtime_views&columns%5B8%5D%5Bsearchable%5D=false&columns%5B8%5D%5Borderable%5D=true&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=9&columns%5B9%5D%5Bname%5D=saved_views&columns%5B9%5D%5Bsearchable%5D=false&columns%5B9%5D%5Borderable%5D=true&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=10&columns%5B10%5D%5Bname%5D=id&columns%5B10%5D%5Bsearchable%5D=false&columns%5B10%5D%5Borderable%5D=true&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&order%5B0%5D%5Bcolumn%5D=10&order%5B0%5D%5Bdir%5D=desc&start={page}&length=10&search%5Bvalue%5D={profile}&search%5Bregex%5D=false&_={ms_time}"
        logging.info(f"Getting page {page} results")
        try:
            r = get_data(url)
            for replay in r.json()['data']:
                replays.append(replay)
        except Exception as e:
            logging.error("Failed after 3 attempts or unknown error, continuing",)
            logging.error(f"{str(e)}")
            continue

    # Connect to sqlite3
    sql_conn = sqlite3.connect(f"{config['fcreplay_dir']}/{config['sqlite_db']}")
    c = sql_conn.cursor()

    # Check if table is created
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='replays'")
    if c.fetchone()[0] == 0:
        # Create table
        c.execute("CREATE TABLE replays (ID TEXT PRIMARY KEY, \
        p1_loc TEXT NOT NULL, \
        p2_loc TEXT NOT NULL, \
        p1 TEXT NOT NULL, \
        p2 TEXT NOT NULL, \
        date_formatted TEXT NOT NULL, \
        date_org TEXT NOT NULL, \
        length INT, \
        created TEXT NOT NULL, \
        failed TEXT NOT NULL, \
        status TEXT NOT NULL, \
        date_added TEXT NOT NULL, \
        player_requested TEXT NOT NULL);")
        sql_conn.commit()
        sql_conn.close()

    if len(replays) == 0:
        logging.error('No replays returned')
        raise LookupError

    replay_added = False
    for row in replays:
        # Only sfiii3n
        if 'sfiii3n' in row[1]:
            if 'live' not in row[7]:
                addreplay(row)
                replay_added = True

    if replay_added == False:
        logging.info('No replays added, but I did find some, sleeping for 1 minute')
        time.sleep(60)


def console():
    get_replays(sys.argv[1])

if __name__ == "__main__":
    console()