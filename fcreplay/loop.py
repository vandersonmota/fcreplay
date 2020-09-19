import argparse
import os
import sys
import time

from fcreplay.config import Config
from fcreplay.gcloud import Gcloud
from fcreplay.logging import Logging
from fcreplay.replay import Replay


class Loop:
    def __init__(self):
        self.config = Config().config
        self.gcloud = False
        self.debug = False
        self.log = Logging()

        if 'REMOTE_DEBUG' in os.environ:
            import debugpy
            self.debug = True
            debugpy.listen(("0.0.0.0", 5678))
            debugpy.wait_for_client()

    def create_dirs(self):
        # Create directories if they don't exist
        if not os.path.exists(f"{self.config['fcreplay_dir']}/tmp"):
            Logging().info('Created tmp dir')
            os.mkdir(f"{self.config['fcreplay_dir']}/tmp")
        if not os.path.exists(f"{self.config['fcreplay_dir']}/videos"):
            Logging().info('Created videos dir')
            os.mkdir(f"{self.config['fcreplay_dir']}/videos")
        if not os.path.exists(f"{self.config['fcreplay_dir']}/finished"):
            Logging().info('Created finished dir')
            os.mkdir(f"{self.config['fcreplay_dir']}/finished")

    def main(self):
        """The main loop for processing one or more replays

        Args:
            Debug (bool): Exit after one loop
            Gcloud (bool): Cloud shutdown after processing
        """
        # If this is google cloud, and the 'destroying' file exists, remove it
        if self.gcloud and os.path.exists('/tmp/destroying'):
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

                if self.config['upload_to_ia']:
                    replay.upload_to_ia()

                if self.config['upload_to_yt']:
                    replay.upload_to_yt()

                if self.config['remove_generated_files']:
                    replay.remove_generated_files()

                replay.remove_job()

                replay.db.update_created_replay(challenge_id=replay.replay.id)
                replay.set_created()

            else:
                logging.info("No more replays. Waiting for replay submission")
                time.sleep(5)

            if self.gcloud:
                Gcloud().destroy_fcreplay()
                sys.exit(0)

            if self.debug:
                sys.exit(0)

    def console(self):
        """Invoked from command line
        """
        parser = argparse.ArgumentParser(description='FCReplay - Video Catpure')
        parser.add_argument('--debug', action='store_true', help='Exits after a single loop')
        parser.add_argument('--gcloud', action='store_true', help='Enabled google cloud functions')
        args = parser.parse_args()

        self.debug = args.debug
        self.gcloud = args.gcloud
        self.main()


if __name__ == "__main__":
    c = Loop()
    c.console()
