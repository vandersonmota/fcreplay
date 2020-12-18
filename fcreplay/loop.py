import argparse
import glob
import os
import sys
import time

from fcreplay.config import Config
from fcreplay.logging import Logging
from fcreplay.replay import Replay


class Loop:
    def __init__(self):
        self.config = Config().config
        self.debug = False
        self.onetime = False

        if 'REMOTE_DEBUG' in os.environ:
            import debugpy
            self.debug = True
            debugpy.listen(("0.0.0.0", 5678))
            debugpy.wait_for_client()

    def clean(self):
        """Cleans directories before running
        """
        dirs = [
            f"{self.config['fcreplay_dir']}/tmp/*",
            f"{self.config['fcadefbneo_path']}/avi/*"
        ]

        for dir in dirs:
            files = glob.glob(dir)
            for f in files:
                os.remove(f)

    def create_dirs(self):
        # Create directories if they don't exist
        if not os.path.exists(f"{self.config['fcreplay_dir']}/tmp"):
            Logging().info('Created tmp dir')
            os.mkdir(f"{self.config['fcreplay_dir']}/tmp")

    def main(self):
        """The main loop for processing one or more replays
        """
        self.create_dirs()
        self.clean()

        if self.debug:
            Logging().debug(self.config)

        replay = Replay()
        if replay.replay is not None:
            replay.add_job()
            replay.record()
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
            Logging().info("No more replays. Waiting for replay submission")
            time.sleep(5)

        sys.exit(0)


def console():
    """Invoked from command line
    """
    parser = argparse.ArgumentParser(description='fcreplay - Video Catpure')
    parser.add_argument('--debug', action='store_true', help='Turns on debugging. Requires port 5678/tcp')
    args = parser.parse_args()

    c = Loop()

    c.debug = args.debug
    c.main()
