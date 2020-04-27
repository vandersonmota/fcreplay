#!/usr/bin/env python3
import sqlite3
import subprocess
import shutil
import os
import logging
import json
from internetarchive import get_item

with open("config.json") as json_data_file:
    config = json.load(json_data_file)

# Setup Sql
sql_conn = sqlite3.connect(config['sqlite_db'])
c = sql_conn.cursor()

# Setup Log
logging.basicConfig(filename=config['logfile'])
loglevel = logging.getLogger('logging')
level = logging.getLevelName(config.['loglevel'])
loglevel.setLevel(level)

# Create directories if they don't exist
if not os.path.exits(f"{config['fcreplay_dir']}/tmp"):
    os.mkdir(f"{config['fcreplay_dir']}/tmp")
if not os.path.exits(f"{config['fcreplay_dir']}/videos"):
    os.mkdir(f"{config['fcreplay_dir']}/videos")
if not os.path.exits(f"{config['fcreplay_dir']}/finished"):
    os.mkdir(f"{config['fcreplay_dir']}/finished")

# Loop and choose a random replay every time
while True:
    if config['random_replay']:
        c.execute("SELECT * FROM replays WHERE created = 'no' ORDER BY RANDOM() LIMIT 1")
    else:
        c.execute("SELECT * FROM replays WHERE created = 'no' LIMIT 1")
    row = c.fetchone()

    if row is not None:
        # Do record here
        logging.info(f"INFO: Running capture with {str(row[0])} and {str(row[7])}")
        time_min = int(row[7]/60)
        logging.info(f"INFO: Capture will take {str(time_min)} minutes")
        capture_rc = subprocess.call([f"{config['fcreplay_dir']}/capture.sh", str(row[0]), str(row[7])])
        # Check if failed
        status = open(f"{config['fcreplay_dir']}/tmp/status", 'r')
        if "failed" in status.readline():
            logging.error(f"ERROR: Status file is failed. Unable to record {str(row[0])}")
            continue
        logging.info("INFO: Capture finished")

        # Do move
        filename = f"{str(row[0])}.mkv"
        shutil.move(f"{config['fcreplay_dir']}/videos/{config['obs_video_filename']}",
                    f"{config['fcreplay_dir']}/finished/dirty_{filename}")

        # Create description
        logging.info("INFO: Creating description")
        description_text = f"""({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}
Fightcade replay id: {row[0]}"""
        logging.info("INFO: Finished creating description")

        # Fix broken videos:
        logging.info("INFO: Running ffmpeg to fix dirty video")
        dirty_rc = subprocess.call(["ffmpeg", "-err_detect", "ignore_err",
                                    "-i", f"{config['fcreplay_dir']}/finished/dirty_{filename}",
                                    "-c", "copy",
                                    f"{config['fcreplay_dir']}/finished/{filename}"])
        logging.info("INFO: Removing dirty file")
        os.remove(f"{config['fcreplay_dir']}/finished/dirty_{filename}")
        logging.info("INFO: Removed dirty file")
        logging.info("INFO: Fixed file")

        # Create thumbnail
        logging.info("INFO: Making thumbnail")
        thumbnail_rc = subprocess.call(["ffmpeg",
                                        "-ss", "20",
                                        "-i", f"{config['fcreplay_dir']}/finished/{filename}",
                                        "-vframes:v", "1",
                                        f"{config['fcreplay_dir']}/tmp/thumbnail.jpg"])
        logging.info("INFO: Made thumbnail")

        if config['upload_to_ia']:
            # Do Upload
            title = f"Street Fighter III: 3rd Strike: ({row[1]}) {row[3]} vs ({row[2]}) {row[4]} - {row[6]}"
            tags = "StreetFighter3rd, fightcade"
            date_mut = str(row[6])
            date_short = str(row[6])[10]
            date = date_mut.replace(" ","T") + ".0Z"

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

            logging.info("INFO: Uploading to archive.org")
            fc_video.upload(f"{config['fcreplay_dir']}/finished/{filename}", metadata=md, verbose=True)
            logging.info("INFO: Uploaded to archive.org")

        if config['remove_generated_files']:
            # Remove dirty file, description and thumbnail
            logging.info("INFO: Removing old files")
            os.remove(f"{config['fcreplay_dir']}/finished/{filename}")
            os.remove(f"{config['fcreplay_dir']}/tmp/thumbnail.jpg")
            logging.info("INFO: Removed files")

        # Update to processed
        logging.info(f"INFO: sqlite updating id {str(row[0])} created to yes")
        c2 = sql_conn.cursor()
        c2.execute("UPDATE replays SET created = 'yes' WHERE ID = ?", (row[0],))
        sql_conn.commit()
        logging.info("INFO: Updated sqlite")
        logging.info(f"INFO: Finished processing {str(row[0])}")
    else:
        break

logging.info("INFO: Finished processing queue")
