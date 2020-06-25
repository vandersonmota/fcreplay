import sqlite3
import logging
import time
import json

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

# Setup Sql
def setupsqlcon():
    sql_conn = sqlite3.connect(config['sqlite_db'])
    c = sql_conn.cursor()
    return sql_conn, c

def get_current_job():
    sql_conn, c = setupsqlcon()
    # Returns the current job ID (Challenge id)
    c.execute('SELECT challenge_id FROM job ORDER BY ID DESC LIMIT 1;')
    row = c.fetchone()
    logging.info(f"Current job ID is: {row[0]}")
    return(row[0])


def get_current_job_status():
    sql_conn, c = setupsqlcon()
    # Returns the status for the current job
    challenge_id = get_current_job()
    c.execute("SELECT status from replays WHERE ID = ?", (challenge_id,))
    row = c.fetchone()
    logging.info(f"Current job STATUS is: {row[0]}")
    return(row[0])


def get_current_job_remaining():
    sql_conn, c = setupsqlcon()
    # Returns the time left to complete current job
    challenge_id = get_current_job()
    c.execute("SELECT * FROM job ORDER BY ID DESC LIMIT 1;")
    row = c.fetchone()
    
    current_time = int(time.time())
    start_time = int(row[2])
    length = int(row[3])

    running_time = current_time - start_time
    time_left = length - running_time

    logging.info(f"Current job status: running_time: {running_time}, time_left: {time_left}")
    
    if time_left <= 0:
        # Time left is less than 0, probably uploading or doing something
        return 0
    else:
        return time_left
        

def get_current_job_details():
    sql_conn, c = setupsqlcon()
    # Returns a 'row' for the current job
    challenge_id = get_current_job()
    c.execute("SELECT * from replays WHERE ID = ?", (challenge_id,))
    row = c.fetchone()
    logging.info(f"Current job rowdata is: {row}")
    return(row)


def challenge_exists(challenge_id):
    sql_conn, c = setupsqlcon()
    # Checks to see if current challenge exists
    c.execute("SELECT ID from replays WHERE ID = ?", (challenge_id,))
    row = c.fetchone()
    if row == None:
        return False
    else:
        return True

def player_replay(challenge_id):
    sql_conn, c = setupsqlcon()
    # Check to see if replay is a player requested one
    c.execute("SELECT player_requested from replays WHERE ID = ?", (challenge_id,))
    row = c.fetchone()
    if row[0] == 'no':
        return False
    else:
        return True

def check_if_finished(challenge_id):
    sql_conn, c = setupsqlcon()
    if challenge_exists(challenge_id):
        # Checks to see if challenge is already finished
        c.execute("SELECT status from replays WHERE ID = ?", (challenge_id,))
        row = c.fetchone()
        if row[0] == 'FINISHED':
            return('FINISHED')
        else:
            return('NOT_FINISHED')
    else:
        return("NO_DATA")


def get_queue_position(challenge_id):
    sql_conn, c = setupsqlcon()
    # Returns the 'queue position' for a requested replay
    if challenge_exists(challenge_id):
        if get_current_job() == challenge_id:
            return(0)
        if player_replay(challenge_id):
            # Get all player replays, then find my position in replays:
            # Get all unfinished player replays, sorted by date added
            c.execute("SELECT ID from replays WHERE player_requested = 'yes' AND failed = 'no' AND created = 'no' ORDER BY date(date_added) ASC")
            position = 0
            logging.debug(f"Looking for player replay {challenge_id}")
            for row in c.fetchone():
                logging.debug(f"Row id: {row[0]}")
                position += 1
                if row == challenge_id:
                    return position
            # This shouldn't happen, ID was already verified. Maybe database modified while in use?
            raise IndexError
        else:
            # Not a player replay
            return("NOT_PLAYER_REPLAY")
    else:
        return("NO_DATA")