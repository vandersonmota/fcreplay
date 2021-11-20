import glob
import logging
import os
import sys
import time

from fcreplay.config import Config
from fcreplay.replay import Replay

log = logging.getLogger('fcreplay')


class Instance:
    def __init__(self):
        self.config = Config()

    def clean(self):
        """Cleans directories before running
        """
        dirs = [
            f"{self.config.fcreplay_dir}/tmp/*",
            f"{self.config.fcadefbneo_path}/avi/*"
        ]

        for dir in dirs:
            files = glob.glob(dir)
            for f in files:
                os.remove(f)

    def create_dirs(self):
        # Create directories if they don't exist
        if not os.path.exists(f"{self.config.fcreplay_dir}/tmp"):
            log.info('Created tmp dir')
            os.mkdir(f"{self.config.fcreplay_dir}/tmp")

    def main(self):
        """The main loop for processing one or more replays
        """
        self.create_dirs()
        self.clean()

        replay = Replay()
        if replay.replay is not None:
            replay.add_job()
            replay.record()
            replay.get_characters()
            replay.encode()
            if self.config.remove_old_avi_files:
                replay.remove_old_avi_files()
            replay.create_thumbnail()
            replay.update_thumbnail()
            replay.set_description()
            if self.config.upload_to_ia:
                replay.upload_to_ia()
            if self.config.upload_to_yt:
                replay.upload_to_yt()
            replay.remove_job()
            replay.db.update_created_replay(challenge_id=replay.replay.id)
            replay.set_created()

        else:
            log.info("No more replays. Waiting for replay submission")
            time.sleep(5)

        sys.exit(0)
