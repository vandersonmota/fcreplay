#!/usr/bin/env python3
import subprocess
import shutil
import os
import logging
import json
import sys
import time
from fcreplay.database import Database
from fcreplay import character_detect
from fcreplay import record as fc_record
from fcreplay import get as fc_get
from fcreplay.gcloud import upload_video, download_video, destroy_fcreplay_postprocessing, destroy_fcreplay
import argparse
import datetime
from internetarchive import get_item
from retrying import retry

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

db = Database()

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


def add_detected_characters(replay, detected_chars):
    logging.info("Adding detected characters to DB")
    logging.info(f"Data is: {detected_chars}")
    for i in detected_chars:
        db.add_detected_characters(
            challenge_id=replay.id,p1_char=i[0],p2_char=i[1],vid_time=i[2]
        )


def add_current_job(replay):
    # Insert current job, with start_time and length
    start_time = datetime.datetime.utcnow()
    db.add_current_job(
        challenge_id=replay.id,start_time=start_time,length=replay.length
    )


def update_status(replay, status):
    # Update the replay table status of the current job
    logging.info(f"Set status to {status}")
    db.update_status(
        challenge_id=replay.id,status=status
    )

def record(replay):
    logging.info(f"Running capture with {replay.id} and {replay.length}")
    time_min = int(replay.length/60)
    logging.info(f"Capture will take {time_min} minutes")

    update_status(replay, 'RECORDING')

    record_status = fc_record.main(fc_challange=replay.id, fc_time=replay.length, kill_time=config['record_timeout'], ggpo_path=config['pyqtggpo_dir'], fcreplay_path=config['fcreplay_dir'])
    if not record_status == "Pass":
        logging.error(f"Recording failed on {replay.id}, Status: \"{record_status}\", exiting.")
        # Depending on the exit status, do different things:
        if record_status == "FailTimeout":
            # Just do a new recording and mark the current one as failed
            logging.error(f"Setting {replay.id} to failed and continuing")
            set_failed(replay)
            return False
        else:
            logging.error("Exiting")
            sys.exit(1)
            return False
    logging.info("Capture finished")
    update_status(replay, 'RECORDED')
    return True


def move(replay):
    filename = f"{replay.id}.mkv"
    shutil.move(f"{config['fcreplay_dir']}/videos/{config['obs_video_filename']}",
                f"{config['fcreplay_dir']}/finished/dirty_{filename}")

    update_status(replay, 'MOVED')


def description(replay, detected_chars=None):
    replay_date = replay.date_replay
    # Create description
    logging.info("Creating description")
    if detected_chars is not None:
        description_text = f"""({replay.p1_loc}) {replay.p1} vs ({replay.p2_loc}) {replay.p2} - {replay_date}
Fightcade replay id: {replay.id}"""
        for match in detected_chars:
            description_text += f"""
{replay.p1}: {match[0]}, {replay.p2}: {match[1]}  - {match[2]}
{match[0]} vs {match[1]}
"""
    else:
        description_text = f"""({replay.p1_loc}) {replay.p1} vs ({replay.p2_loc}) {replay.p2} - {replay_date}
Fightcade replay id: {replay.id}"""

    # Read the append file:
    if config['description_append_file'][0] is True:
        # Check if file exists:
        if not os.path.exists(config['description_append_file'][1]):
            logging.error(f"Description append file {config['description_append_file'][0]} doesn't exist")
            return False
        else:
            with open(config['description_append_file'][1]) as description_append:
                description_text += description_append.read()

    update_status(replay, 'DESCRIPTION_CREATED')
    logging.info("Finished creating description")

    # Add description to database
    logging.info('Adding description to database')
    db.add_description(challenge_id=replay.id,description=description_text)

    if DEBUG:
        print(f'Description Text is: {description_text}')
    return description_text


def broken_fix(replay):
    # Fix broken videos:
    filename = f"{replay.id}.mkv"
    logging.info("Running ffmpeg to fix dirty video")
    subprocess.run([
        "ffmpeg", "-err_detect", "ignore_err",
        "-i", f"{config['fcreplay_dir']}/finished/dirty_{filename}",
        "-c", "copy",
        f"{config['fcreplay_dir']}/finished/{filename}"])
    logging.info("Removing dirty file")
    os.remove(f"{config['fcreplay_dir']}/finished/dirty_{filename}")
    update_status(replay,'BROKEN_CHECK')
    logging.info("Removed dirty file")
    logging.info("Fixed file")


def black_check(replay):
    # Use ffmpeg to check for black frames to see if something is broken
    logging.info("Checking for black frames")
    filename = f"{replay.id}.mkv"
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

    update_status(replay, 'EMPTY_CHECK')
    logging.info("Finished checking black frames")


def create_thumbnail(replay):
    # Create thumbnail
    logging.info("Making thumbnail")
    filename = f"{replay.id}.mkv"
    subprocess.run([
        "ffmpeg",
        "-ss", "20",
        "-i", f"{config['fcreplay_dir']}/finished/{filename}",
        "-vframes:v", "1",
        f"{config['fcreplay_dir']}/tmp/thumbnail.jpg"])

    update_status(replay, 'THUMBNAIL_CREATED')
    logging.info("Finished making thumbnail")


@retry(wait_random_min=30000, wait_random_max=60000, stop_max_attempt_number=3)
def upload_to_ia(replay, description_text):
    replay_date = replay.date_replay
    # Do Upload to internet archive. Sometimes it will return a 403, even
    # though the file doesn't already exist. So we decorate the function with
    # the @retry decorator to try again in a little bit. Max of 3 tries.
    title = f"Street Fighter III: 3rd Strike: ({replay.p1_loc}) {replay.p1} vs ({replay.p2_loc}) {replay.p2} - {replay_date}"
    filename = f"{replay.id}.mkv"
    date_short = str(replay_date)[10]

    # Make identifier for Archive.org
    ident = str(replay.id).replace("@", "-")
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

    update_status(replay, 'UPLOADED_TO_IA')
    logging.info("Finished upload to archive.org")


def upload_to_yt(replay, description_text):
    replay_date = replay.date_replay
    title = f"Street Fighter III: 3rd Strike: ({replay.p1_loc}) {replay.p1} vs ({replay.p2_loc}) {replay.p2} - {replay_date}"
    filename = f"{replay.id}.mkv"
    import_format = '%Y-%m-%d %H:%M:%S'
    date_raw = datetime.datetime.strptime(str(replay_date), import_format)

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
        if (int(replay.length)/60) < int(config['yt_min_length']):
            logging.info("Replay is too short. Not uploading to youtube")
            return False
        if (int(replay.length)/60) > int(config['yt_max_length']):
            logging.info("Replay is too long. Not uploading to youtube")
            return False

        # If this isn't a player replay, then check max uploads
        if replay.player_requested == False:
            # Find number of uploads today
            day_log = db.get_youtube_day_log()

            # Check max uploads
            # Get todays date, dd-mm-yyyy
            today = datetime.datetime.utcnow().strftime("%d-%m-%Y")

            # Check the log is for today
            if day_log.date == today:
                # Check number of uploads
                if day_log.count >= int(config['youtube_max_daily_uploads']):
                    logging.info("Maximum uploads reached for today")
                    return False
            else:
                # It's a new day, update the counter
                db.update_youtube_day_log_count(count=1,date=today)


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

        if replay.player_requested == False:
            # Add upload to day_log dable
            logging.info('Updating day_log')
            # Update count for today
            logging.info("Updating counter")
            db.update_youtube_day_log_count(count=day_log.count+1,date=today)

        # Remove description file
        os.remove(f"{config['fcreplay_dir']}/tmp/description.txt")

        update_status(replay, 'UPLOADED_TO_YOUTUBE')
        logging.info('Finished uploading to Youtube')
    else:
        logging.error("youtube-upload is not installed")


def remove_generated_files(replay):
    # Remove dirty file, description and thumbnail
    logging.info("Removing old files")
    filename = f"{replay.id}.mkv"
    try:
        os.remove(f"{config['fcreplay_dir']}/finished/{filename}")
    except:
        pass

    try:
        os.remove(f"{config['fcreplay_dir']}/tmp/thumbnail.jpg")
    except:
        pass

    update_status(replay, "REMOVED_GENERATED_FILES")
    logging.info("Finished removing files")


def set_failed(replay):
    logging.info(f"Setting {replay.id} to failed")
    db.update_failed_replay(challenge_id=replay.id)

    update_status(replay, "FAILED")
    logging.info("Finished updating datebase")


def get_replay():
    logging.info('Getting replay from database')
    if config['player_replay']:
        replay = db.get_oldest_player_replay()
        if replay is not None:
            logging.info('Found player replay to encode')
            return(replay)
        else:
            logging.info('No more player replays')
    if config['random_replay']:
        logging.info('Getting random replay')
        replay = db.get_random_replay()
        return(replay)
    else:
        logging.info('Getting oldest replay')
        replay = db.get_oldest_replay()
        return(replay)


def gcloud_postprocessing():
    # Get currently processing replay
    job = db.get_current_job()
    replay = db.get_single_replay(challenge_id=job.challenge_id)

    # Download replay:
    download_video(replay.id,f"{config['fcreplay_dir']}/finished/{replay.id}.mkv")

    # Do post processing
    postprocessing(replay)

    # Destroy postprocessing
    status = destroy_fcreplay_postprocessing()
    if not status['status']:
        print("Postprocessing already running. This shouldn't happen")
        sys.exit(1)

def postprocessing(replay):
    try:
        broken_fix(replay)
    except FileNotFoundError as e:
        logging.error(e)
        logging.error("Exiting due to error in brokenfix")
        sys.exit(1)

    if config['blackdetect']:
        try:
            black_check(replay)
        except FileNotFoundError as e:
            logging.error(e)
            logging.error("Exiting due to error in black_check")
            sys.exit(1)

    if config['detect_chars']:
        try:
            logging.info("Detecting characters")
            detected_chars = character_detect.character_detect(f"{config['fcreplay_dir']}/finished/{replay.id}.mkv")
            add_detected_characters(replay, detected_chars)
            description_text = description(replay, detected_chars)
            logging.info(f"Description is: {description_text}")
        except Exception as e:
            logging.error(e)
            logging.error("Exiting due to error in character detection")
            sys.exit(1)
    else:
        description_text = description(replay)
        logging.info(f"Description is {description_text}")

    try:
        create_thumbnail(replay)

    except FileNotFoundError as e:
        logging.error(e)
        logging.error("Exiting due to error in create_thumbnail")
        sys.exit(1)

    if config['upload_to_ia']:
        try:
            upload_to_ia(replay, description_text)
        except:
            set_failed(replay)

    if config['upload_to_yt']:
        try:
            upload_to_yt(replay, description_text)
        except Exception as e:
            logging.error(e)
            set_failed(replay)

    if config['remove_generated_files']:
        try:
            remove_generated_files(replay)
        except FileNotFoundError as e:
            logging.error(e)
            logging.error("Exiting due to error in remove_generated_files")
            sys.exit(1)

    db.update_created_replay(challenge_id=replay.id)


def main(DEBUG, GCLOUD):
    while True:
        replay = get_replay()
        if replay is not None:
            # Update the current job
            add_current_job(replay)
            try:
                status = record(replay)
                if status is False:
                    continue
            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in capture")
                sys.exit(1)

            try:
                move(replay)
            except FileNotFoundError as e:
                logging.error(e)
                logging.error("Exiting due to error in move")
                sys.exit(1)

            if GCLOUD:
                try:
                    upload_video(f"{config['fcreplay_dir']}/finished/dirty_{replay.id}.mkv", f"{replay.id}.mkv")
                except Exception as e:
                    logging.error(f"There was an error uploading to google storage: {e}")
                    sys.exit(1)

                try:
                    destroy_fcreplay(None)
                except Exception as e:
                    logging.error(f"There was an error destroying instance: {e}")
                    sys.exit(1)

            postprocessing(replay)

        else:
            if config['auto_add_more']:
                logging.info('Auto adding more replays')
                fc_get.get_replays(config['auto_add_search_string'])
            else:
                logging.info("No more replays. Waiting for replay submission")
                time.sleep(5)

        if DEBUG:
            sys.exit(0)

        if GCLOUD:
            from fcreplay import gcloud
            destroy_fcreplay()
            sys.exit(0)


def console():
    parser = argparse.ArgumentParser(description='FCReplay - Video Catpure')
    parser.add_argument('--debug', action='store_true', help='Exits after a single loop')
    parser.add_argument('--gcloud', action='store_true', help='Enabled google cloud functions')
    args = parser.parse_args()
    main(args.debug, args.gcloud)

# Loop and choose a random replay every time
if __name__ == "__main__":
    console()

logging.info("Finished processing queue")
