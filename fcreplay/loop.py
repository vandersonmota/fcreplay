import argparse
import json
import logging
import os
import sys
import time

from fcreplay.config import Config
from fcreplay.gcloud import destroy_fcreplay
from fcreplay.replay import Replay

if 'REMOTE_DEBUG' in os.environ:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()

config = Config().config

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)


# Create directories if they don't exist
if not os.path.exists(f"{config['fcreplay_dir']}/tmp"):
    os.mkdir(f"{config['fcreplay_dir']}/tmp")
if not os.path.exists(f"{config['fcreplay_dir']}/videos"):
    os.mkdir(f"{config['fcreplay_dir']}/videos")
if not os.path.exists(f"{config['fcreplay_dir']}/finished"):
    os.mkdir(f"{config['fcreplay_dir']}/finished")


def main(Debug, Gcloud):
    """The main loop for processing one or more replays

    Args:
        Debug (bool): Exit after one loop
        Gcloud (bool): Cloud shutdown after processing
    """
    ## TODO Capture kill signal and handle within 30 secods for google cloud shutdown
    while True:
        replay = Replay()
        if replay.replay is not None:
            replay.add_job()
            replay.record()
            replay.move()
            replay.broken_fix()

            if config['detect_chars'] and config['supported_games'][replay.replay.game]['character_detect']:
                replay.detect_characters()
                replay.set_detected_characters()

            replay.set_description()
            replay.create_thumbnail()

            if config['upload_to_ia']:
                replay.upload_to_ia()

            if config['upload_to_yt']:
                replay.upload_to_yt()

            if config['remove_generated_files']:
                replay.remove_generated_files()

            replay.remove_job()

            replay.db.update_created_replay(challenge_id=replay.replay.id)

        else:
            logging.info("No more replays. Waiting for replay submission")
            time.sleep(5)

        if Gcloud:
            destroy_fcreplay()
            sys.exit(0)

        if Debug:
            sys.exit(0)


def console():
    """Invoked from command line
    """
    parser = argparse.ArgumentParser(description='FCReplay - Video Catpure')
    parser.add_argument('--debug', action='store_true', help='Exits after a single loop')
    parser.add_argument('--gcloud', action='store_true', help='Enabled google cloud functions')
    args = parser.parse_args()
    main(args.debug, args.gcloud)


# Loop and choose a random replay every time
if __name__ == "__main__":
    console()

logging.info("Finished processing queue")
