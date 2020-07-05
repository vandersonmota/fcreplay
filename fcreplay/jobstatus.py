import sqlite3
import logging
import datetime
import json

from fcreplay.database import Database

with open("config.json", "r") as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

def get_current_job_id():
    db = Database()
    job = db.get_current_job()
    logging.info(f"Current job ID is: {job.challenge_id}")
    return(job.challenge_id)


def get_replay_status(challenge_id):
    db = Database()
    replay = db.get_single_replay(challenge_id=challenge_id)
    logging.info(f"Current job STATUS is: {replay.status}")
    return(replay.status)


def get_current_job_remaining():
    # Returns the time left to complete current job
    db = Database()
    challenge_id = get_current_job_id()

    job = db.get_current_job()
    current_time = datetime.datetime.utcnow()
    start_time = job.start_time
    length = job.length


    # TODO Need to fix time check
    running_time = current_time - start_time
    time_left = length - running_time

    logging.info(f"Current job status: running_time: {running_time}, time_left: {time_left}")
    
    if time_left <= 0:
        # Time left is less than 0, probably uploading or doing something
        return 0
    else:
        return time_left
        

def get_current_job_details():
    challenge_id = get_current_job_id()
    db = Database()
    replay = db.get_single_replay(challenge_id=challenge_id)
    logging.info(f"Current job rowdata is: {replay}")
    return(replay)


def challenge_exists(challenge_id):
    # Checks to see if current challenge exists
    db = Database()
    replay = db.get_single_replay(challenge_id=challenge_id)
    if replay == None:
        return False
    else:
        return True

def player_replay(challenge_id):
    # Check to see if replay is a player requested one
    db = Database()
    replay = db.get_single_replay(challenge_id=challenge_id)
    if replay.player_requested:
        return True
    else:
        return False

def check_if_finished(challenge_id):
    if challenge_exists(challenge_id):
        # Checks to see if challenge is already finished
        db = Database()
        replay = db.get_single_replay(challenge_id=challenge_id)
        if replay.status == 'FINISHED':
            return('FINISHED')
        else:
            return('NOT_FINISHED')
    else:
        return("NO_DATA")


def get_queue_position(challenge_id):
    # Returns the 'queue position' for a requested replay
    if challenge_exists(challenge_id):
        if get_current_job_id() == challenge_id:
            return(0)
        if player_replay(challenge_id):
            # Get all player replays, then find my position in replays:
            # Get all unfinished player replays, sorted by date added
            db = Database()
            
            replays = db.get_all_queued_player_replays()
            position = 0
            logging.debug(f"Looking for player replay {challenge_id}")
            for replay in replays:
                logging.debug(f"Row id: {replay.id}")
                position += 1
                if replay.id == challenge_id:
                    return position
            # This shouldn't happen, ID was already verified. Maybe database modified while in use?
            raise IndexError
        else:
            # Not a player replay
            return("NOT_PLAYER_REPLAY")
    else:
        return("NO_DATA")