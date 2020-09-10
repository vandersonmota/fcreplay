import argparse
import os
import sys
import time

from fcreplay.config import Config
from fcreplay.gcloud import destroy_fcreplay
from fcreplay import logging
from fcreplay.replay import Replay

if 'REMOTE_DEBUG' in os.environ:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()

config = Config().config


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
    # If this is google cloud, and the 'destroying' file exists, remove it
    if Gcloud and os.path.exist('/tmp/destroying'):
        os.remove('/tmp/destroying')

    while True:
        replay = Replay()
        if replay.replay is not None:
            replay.add_job()
            replay.record()
            replay.move()
            replay.encode()
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
            replay.set_created()

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
