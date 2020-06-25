#!/usr/bin/env python3
import sqlite3
import subprocess
import shutil
import os
import logging
import json
import sys
import time
from fcreplay import character_detect
from fcreplay import record as fc_record
from fcreplay import get as fc_get
import argparse
import datetime
from soundmeter import meter as sm
from internetarchive import get_item
from retrying import retry

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

sql_conn = sqlite3.connect(config['sqlite_db'])
c = sql_conn.cursor()

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

DEBUG=False

# Create directories if they don't exist
if not os.path.exists(f"{config['fcreplay_dir']}/tmp"):
    os.mkdir(f"{config['fcreplay_dir']}/tmp")
if not os.path.exists(f"{config['fcreplay_dir']}/videos"):
    os.mkdir(f"{config['fcreplay_dir']}/videos")
if not os.path.exists(f"{config['fcreplay_dir']}/finished"):
    os.mkdir(f"{config['fcreplay_dir']}/finished")


def setupjobssql():
    # Create jobs table
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='job'")
    if c.fetchone()[0] == 0:
        # Create table, ID auto increments
        c.execute("CREATE TABLE job (ID INTEGER PRIMARY KEY, \
            challenge_id TEXT NOT NULL, \
            start_time INTEGER, \
            length INTEGER);")
        sql_conn.commit()


def setcurrentjob(row):
    # Insert current job, with start_time and length
    current_time = str(time.time())
    c.execute("INSERT INTO job VALUES (null, ?, ?, ?);",(row[0], current_time, row[7],))
    sql_conn.commit()

def update_status(row, status):
    # Update the replay table status of the current job
    c.execute("UPDATE replays SET status = ? WHERE ID = ?", (status, row[0],))
    logging.info(f"Set status to {status}")
    sql_conn.commit()

def record(row):
    logging.info(f"Running capture with {row[0]} and {row[7]}")
    time_min = int(row[7]/60)
    logging.info(f"Capture will take {time_min} minutes")

    update_status(row, 'RECORDING')
    
    record_status = fc_record.main(fc_challange=row[0], fc_time=row[7], kill_time=config['record_timeout'], ggpo_path=config['pyqtggpo_dir'], fcreplay_path=config['fcreplay_dir'])
    if not record_status == "Pass":
        logging.error(f"Recording failed on {row[0]}, Status: \"{record_status}\", exiting.")
        # Depending on the exit status, do different things:
        if record_status == "FailTimeout":
            # Just do a new recording and mark the current one as failed
            logging.error(f"Setting {row[0]} to failed and continuing")
            set_failed(row)
            return False
        else:
            logging.error("Exiting")
            sys.exit(1)
            return False
    logging.info("Capture finished")
    update_status(row, 'RECORDED')
    return True


def move(row):
    filename = f"{row[0]}.mkv"
    shutil.move(f"{config['fcreplay_dir']}/videos/{config['obs_video_filename']}",
                f"{config['fcreplay_dir']}/finished/dirty_{filename}")

    update_status(row, 'MOVED')


def description(row, detected_chars=None):
    # Create description
    logging.info("Creating description")
    if detected_chars is not None:
        description_text = f"""({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}
Fightcade replay id: {row[0]}"""
        for match in detected_chars:
            description_text += f"""
{row[3]}: {match[0]}, {row[4]}: {match[1]}  - {match[2]}
{match[0]} vs {match[1]}
"""
    else:
        description_text = f"""({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}
Fightcade replay id: {row[0]}"""

    # Read the append file:
    if config['description_append_file'][0] is True:
        # Check if file exists:
        if not os.path.exists(config['description_append_file'][1]):
            logging.error(f"Description append file {config['description_append_file'][0]} doesn't exist")
            return False
        else:
            with open(config['description_append_file'][1]) as description_append:
                description_text += description_append.read()

    update_status(row, 'DESCRIPTION_CREATED')
    logging.info("Finished creating description")

    if DEBUG:
        print(f'Description Text is: {description_text}')
    return description_text


def broken_fix(row):
    # Fix broken videos:
    filename = f"{row[0]}.mkv"
    logging.info("Running ffmpeg to fix dirty video")
    dirty_rc = subprocess.run([
        "ffmpeg", "-err_detect", "ignore_err",
        "-i", f"{config['fcreplay_dir']}/finished/dirty_{filename}",
        "-c", "copy",
        f"{config['fcreplay_dir']}/finished/{filename}"])
    logging.info("Removing dirty file")
    os.remove(f"{config['fcreplay_dir']}/finished/dirty_{filename}")
    update_status(row,'BROKEN_CHECK')
    logging.info("Removed dirty file")
    logging.info("Fixed file")


def black_check(row):
    # Use ffmpeg to check for black frames to see if something is broken
    logging.info("Checking for black frames")
    filename = f"{row[0]}.mkv"
    black_rc = subprocess.run([
        "ffmpeg",
        "-i",
        f"{config['fcreplay_dir']}/finished/{filename}",
        "-vf", "blackdetect=d=20",
        "-an", "-f", "null", "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    if "blackdetect" in str(black_rc.stderr) or "blackdetect" in str(black_rc.stdout):
        logging.error("Black frames detected, exiting")
        # If there are too many black frames, then we need to debug processing
        sys.exit(1)
    
    update_status(row, 'EMPTY_CHECK')
    logging.info("Finished checking black frames")


def create_thumbnail(row):
    # Create thumbnail
    logging.info("Making thumbnail")
    filename = f"{row[0]}.mkv"
    thumbnail_rc = subprocess.run([
        "ffmpeg",
        "-ss", "20",
        "-i", f"{config['fcreplay_dir']}/finished/{filename}",
        "-vframes:v", "1",
        f"{config['fcreplay_dir']}/tmp/thumbnail.jpg"])

    update_status(row, 'THUMBNAIL_CREATED')
    logging.info("Finished making thumbnail")


@retry(wait_random_min=30000, wait_random_max=60000, stop_max_attempt_number=3)
def upload_to_ia(row, description_text):
    # Do Upload to internet archive. Sometimes it will return a 403, even
    # though the file doesn't already exist. So we decorate the function with
    # the @retry decorator to try again in a little bit. Max of 3 tries.
    title = f"Street Fighter III: 3rd Strike: ({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}"
    filename = f"{row[0]}.mkv"
    date_short = str(row[6])[10]

    # Make identifier for Archive.org
    ident = str(row[0]).replace("@", "-")
    fc_video = get_item(ident)

    md = {'title': title,
          'mediatype': config['ia_settings']['mediatype'],
          'collection': config['ia_settings']['collection'],
          'date': date_short,
          'description': description_text,
          'subject': config['ia_settings']['subject'],
          'creator': config['ia_settings']['creator'],
          'language': config['ia_settings']['language'],
          'licenseurl': config['ia_settings']['license_url']}

    logging.info("Starting upload to archive.org")
    fc_video.upload(f"{config['fcreplay_dir']}/finished/{filename}",
                    metadata=md, verbose=True)

    update_status(row, 'UPLOADED_TO_IA')
    logging.info("Finished upload to archive.org")


def upload_to_yt(row, description_text):
    title = f"Street Fighter III: 3rd Strike: ({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}"
    filename = f"{row[0]}.mkv"
    import_format = '%Y-%m-%d %H:%M:%S'
    date_raw = datetime.datetime.strptime(str(row[6]), import_format)

    # YYYY-MM-DDThh:mm:ss.sZ
    youtube_date = date_raw.strftime('%Y-%m-%dT%H:%M:%S.0Z')

    # Check if youtube-upload is installed
    if shutil.which('youtube-upload') is not None:
        # Check if credentials file exists
        if not os.path.exists(config['youtube_credentials']):
            logging.error("Youtube credentials don't exist exist")
            return False

        if not os.path.exists(config['youtube_secrets']):
            logging.error("Youtube secrets don't exist")
            return False

        # Check min and max length:
        if (int(row[7])/60) < int(config['yt_min_length']):
            logging.info("Replay is too short. Not uploading to youtube")
            return False
        if (int(row[7])/60) > int(config['yt_max_length']):
            logging.info("Replay is too long. Not uploading to youtube")
            return False

        # Chech max daily uploads
        # Create table if it doesn't exist
        c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='day_log'")
        if c.fetchone()[0] == 0:
            logging.info("Creating table day_log")
            c.execute("CREATE TABLE day_log (ID TEXT PRIMARY KEY, date TEXT NOT NULL)")
            sql_conn.commit()

        # Find number of uploads today
        c.execute("SELECT count(date) FROM day_log WHERE date = date('now')")
        num_uploads = c.fetchone()[0]
        if num_uploads >= int(config['youtube_max_daily_uploads']):
            logging.info("Maximum uploads reached for today")
            return False
        elif num_uploads == 0:
            logging.info("Clearing table day_log as no entries found for today")
            c.execute('DELETE FROM day_log')
            sql_conn.commit()

        # Create description file
        with open(f"{config['fcreplay_dir']}/tmp/description.txt", 'w') as description_file:
            description_file.write(description_text)

        # Do upload
        logging.info("Uploading to youtube")
        yt_rc = subprocess.run(
            [
                'youtube-upload',
                '--credentials-file', config['youtube_credentials'],
                '--client-secrets', config['youtube_secrets'],
                '-t', title,
                '-c', 'Gaming',
                '--description-file', f"{config['fcreplay_dir']}/tmp/description.txt",
                '--recording-date', youtube_date,
                '--default-language', 'en',
                '--thumbnail', f"{config['fcreplay_dir']}/tmp/thumbnail.jpg",
                f"{config['fcreplay_dir']}/finished/{filename}",
                ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        logging.info(yt_rc.stdout.decode())
        logging.info(yt_rc.stderr.decode())

        # Add upload to day_log dable
        logging.info('Updating day_log')
        c.execute("INSERT INTO day_log VALUES (?, date('now'))", (row[0],))
        sql_conn.commit()

        # Remove description file
        os.remove(f"{config['fcreplay_dir']}/tmp/description.txt")

        update_status(row, 'UPLOADED_TO_YOUTUBE')
        logging.info('Finished uploading to Youtube')
    else:
        logging.error("youtube-upload is not installed")


def remove_generated_files(row):
    # Remove dirty file, description and thumbnail
    logging.info("Removing old files")
    filename = f"{row[0]}.mkv"
    try:
        os.remove(f"{config['fcreplay_dir']}/finished/{filename}")
    except:
        pass
    
    try:
        os.remove(f"{config['fcreplay_dir']}/tmp/thumbnail.jpg")
    except:
        pass

    update_status(row, "REMOVED_GENERATED_FILES")
    logging.info("Finished removing files")


def update_db(row):
    # Update to processed
    logging.info(f"sqlite updating id {row[0]} created to yes")
    c2 = sql_conn.cursor()
    c2.execute("UPDATE replays SET created = 'yes' WHERE ID = ?", (row[0],))
    sql_conn.commit()
    logging.info("Updated sqlite")

    update_status(row, "FINISHED")
    logging.info(f"Finished processing {row[0]}")


def set_failed(row):
    logging.info(f"Setting {row[0]} to failed")
    c3 = sql_conn.cursor()
    c3.execute("UPDATE replays SET failed = 'yes' WHERE ID = ?", (row[0],))
    sql_conn.commit()

    update_status(row, "FAILED")
    logging.info("Finished updating sqlite")


def get_row():
    logging.info('Getting replay from sqlite database')
    if config['player_replay']:
        c.execute("SELECT * FROM replays WHERE player_requested = 'yes' AND created = 'no' AND failed ='no' ORDER BY datetime(date_added) ASC LIMIT 1")
        row = c.fetchone()
        if row is not None:
            logging.info('Found player replay to encode')
            return row
        else:
            logging.info('No more player replays, encoding a random one')
    if config['random_replay']:
        logging.info('Getting random replay')
        c.execute("SELECT * FROM replays WHERE created = 'no' AND failed = 'no' ORDER BY RANDOM() LIMIT 1")
        return c.fetchone()
    else:
        logging.info('Getting any replay')
        c.execute("SELECT * FROM replays WHERE created = 'no' AND failed != 'yes' LIMIT 1")
        return c.fetchone()


def main(DEBUG):
    # Create jobs table if it does't exist
    setupjobssql()

    while True:
        row = get_row()
        if row is not None:
            # Update the current job
            setcurrentjob(row)
            try:
                status = record(row)
                if status is False:
                    continue
            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in capture")
                sys.exit(1)

            try:
                move(row)
            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in move")
                sys.exit(1)

            try:
                broken_fix(row)
            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in brokenfix")
                sys.exit(1)

            if config['blackdetect']:
                try:
                    black_check(row)
                except FileNotFoundError as e:
                    logging.error(e)
                    logging.error("Exiting due to error in black_check")
                    sys.exit(1)

            if config['detect_chars']:
                try:
                    logging.info("Detecting characters")
                    detected_chars = character_detect.character_detect(f"{config['fcreplay_dir']}/finished/{row[0]}.mkv")
                    description_text = description(row, detected_chars)
                    logging.info(f"Description is: {description_text}")
                except Exception as e:
                    logging.error(e)
                    logging.error("Exiting due to error in character detection")
                    sys.exit(1)
            else:
                description_text = description(row)
                logging.info(f"Description is {description_text}")

            try:
                create_thumbnail(row)

            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in create_thumbnail")
                sys.exit(1)

            if config['upload_to_ia']:
                try:
                    upload_to_ia(row, description_text)
                except:
                    set_failed(row)

            if config['upload_to_yt']:
                try:
                    upload_to_yt(row, description_text)
                except Exception as e:
                    logging.error(e)
                    set_failed(row)

            if config['remove_generated_files']:
                try:
                    remove_generated_files(row)
                except FileNotFoundError as e:
                    logging.error(e)
                    logging.error("Exiting due to error in remove_generated_files")
                    sys.exit(1)

            update_db(row)
        else:
            if config['auto_add_more']:
                logging.info('Auto adding more replays')
                fc_get.get_replays(config['auto_add_search_string'])                
            else:
                break

        if DEBUG:
            sys.exit(0)


def console():
    parser = argparse.ArgumentParser(description='FCReplay - Video Catpure')
    parser.add_argument('--debug', action='store_true', help='Exits after a single loop')
    args = parser.parse_args()
    main(args.debug)

# Loop and choose a random replay every time
if __name__ == "__main__":
    console()

logging.info("Finished processing queue")
