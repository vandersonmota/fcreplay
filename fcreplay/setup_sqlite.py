import logging
import sqlite3
import json


with open("config.json") as json_data_file:
    config = json.load(json_data_file)

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    filename=config['logfile'],
                    level=config['loglevel'],
                    datefmt='%Y-%m-%d %H:%M:%S')

sql_conn = sqlite3.connect(config['sqlite_db'])
c = sql_conn.cursor()


def setup_jobs_sql():
    # Create jobs table
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='job'")
    if c.fetchone()[0] == 0:
        # Create table, ID auto increments
        c.execute("CREATE TABLE job ( \
            ID INTEGER PRIMARY KEY, \
            challenge_id TEXT NOT NULL, \
            start_time INTEGER, \
            length INTEGER);")
        sql_conn.commit()


def setup_descriptions_sql():
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='descriptions'")
    if c.fetchone()[0] == 0:
        # Create table
        c.execute("CREATE TABLE descriptions ( \
            ID TEXT PRIMARY KEY, \
            DESCRIPTION TEXT NOT NULL);")
        sql_conn.commit()


def setup_replays_sql():
    # Check if table is created
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='replays'")
    if c.fetchone()[0] == 0:
        # Create table
        c.execute("CREATE TABLE replays ( \
        ID TEXT PRIMARY KEY, \
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


def setup_daily_uploads_sql():
        # Create table if it doesn't exist
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='day_log'")
        if c.fetchone()[0] == 0:
            logging.info("Creating table day_log")
            c.execute("CREATE TABLE day_log ( \
                ID TEXT PRIMARY KEY, \
                date TEXT NOT NULL)")
            sql_conn.commit()


def setup_character_times_sql():
        # Create table if it doesn't exist
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='character_detect'")
        if c.fetchone()[0] == 0:
            logging.info("Creating table character_detect")
            c.execute("CREATE TABLE character_detect ( \
                ID INTEGER PRIMARY KEY, \
                challenge TEXT NOT NULL, \
                p1_char TEXT NOT NULL, \
                p2_char TEXT NOT NULL, \
                vid_time TEXT NOT NULL)")
            sql_conn.commit()


def main():
    setup_daily_uploads_sql()
    setup_descriptions_sql()
    setup_replays_sql()
    setup_jobs_sql()
    setup_character_times_sql()


if __name__ == '__main__':
    main()