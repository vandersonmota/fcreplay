#!/usr/bin/env python3
import sqlite3
import subprocess
import shutil
import os
import logging
import json
import sys
import character_detect
import record as fc_record
import argparse
from soundmeter import meter as sm
from internetarchive import get_item
from retrying import retry

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

# Setup Sql
sql_conn = sqlite3.connect(config['sqlite_db'])
c = sql_conn.cursor()

# Setup Log
logging.basicConfig(filename=config['logfile'], level=config['loglevel'])

DEBUG=False

# Create directories if they don't exist
if not os.path.exists(f"{config['fcreplay_dir']}/tmp"):
    os.mkdir(f"{config['fcreplay_dir']}/tmp")
if not os.path.exists(f"{config['fcreplay_dir']}/videos"):
    os.mkdir(f"{config['fcreplay_dir']}/videos")
if not os.path.exists(f"{config['fcreplay_dir']}/finished"):
    os.mkdir(f"{config['fcreplay_dir']}/finished")


def record(row):
    logging.info(f"Running capture with {row[0]} and {row[7]}")
    time_min = int(row[7]/60)
    logging.info(f"Capture will take {time_min} minutes")
    
    record_pass = fc_record.main(fc_challange=row[0], fc_time=row[7], kill_time=30, ggpo_path=config['pyqtggpo_dir'], fcreplay_path=config['fcreplay_dir'])
    if not record_pass:
        logging.error(f"Recording failed on {row[0]}, exiting.")
        sys.exit(1)
    logging.info("Capture finished")


def move(row):
    filename = f"{row[0]}.mkv"
    shutil.move(f"{config['fcreplay_dir']}/videos/{config['obs_video_filename']}",
                f"{config['fcreplay_dir']}/finished/dirty_{filename}")


def description(row, detected_chars=None):
    # Create description
    logging.info("Creating description")
    if detected_chars is not None:
        description_text = f"""({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}
Fightcade replay id: {row[0]}"""
        for match in detected_chars:
            description_text += f"""
{row[3]}: {match[0]}, {row[4]}: {match[1]}  - {match[2]}
            """
    else:
        description_text = f"""({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}
Fightcade replay id: {row[0]}"""
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
    logging.info("Finished upload to archive.org")


def remove_generated_files(row):
    # Remove dirty file, description and thumbnail
    logging.info("Removing old files")
    filename = f"{row[0]}.mkv"
    os.remove(f"{config['fcreplay_dir']}/finished/{filename}")
    os.remove(f"{config['fcreplay_dir']}/tmp/thumbnail.jpg")
    logging.info("Finished removing files")


def update_db(row):
    # Update to processed
    logging.info(f"sqlite updating id {row[0]} created to yes")
    c2 = sql_conn.cursor()
    c2.execute("UPDATE replays SET created = 'yes' WHERE ID = ?", (row[0],))
    sql_conn.commit()
    logging.info("Updated sqlite")
    logging.info(f"Finished processing {row[0]}")


def set_failed(row):
    logging.info(f"Setting {row[0]} to failed")
    c3 = sql_conn.cursor()
    c3.execute("UPDATE replays SET failed = 'yes' WHERE ID = ?", (row[0],))
    sql_conn.commit()
    logging.info("Finished updating sqlite")


def main(DEBUG):
    while True:
        if config['random_replay']:
            c.execute("SELECT * FROM replays WHERE created = 'no' AND failed = 'no' ORDER BY RANDOM() LIMIT 1")
        else:
            c.execute("SELECT * FROM replays WHERE created = 'no' AND failed != 'yes' LIMIT 1")
        row = c.fetchone()

        if row is not None:
            try:
                record(row)
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

            if config['remove_generated_files']:
                try:
                    remove_generated_files(row)
                except FileNotFoundError as e:
                    logging.error(e)
                    logging.error("Exiting due to error in remove_generated_files")
                    sys.exit(1)

            update_db(row)
        else:
            break

        if DEBUG:
            sys.exit(0)


# Loop and choose a random replay every time
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FCReplay - Video Catpure')
    parser.add_argument('--debug', action='store_true', help='Exits after a single loop')
    DEBUG = argparser.parse_args(['--debug'])
    main(parser)

logging.info("Finished processing queue")
