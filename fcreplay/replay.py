from fcreplay.config import Config
from fcreplay.database import Database
from fcreplay.record import Record
from fcreplay.status import status
from fcreplay.thumbnail import Thumbnail
from fcreplay.updatethumbnail import UpdateThumbnail
from fcreplay.character_detection import CharacterDetection

from internetarchive import get_item
from retrying import retry

import datetime
import glob
import json
import logging
import os
import pkg_resources
import re
import shutil
import subprocess
import sys
import traceback
import time

log = logging.getLogger('fcreplay')


class Replay:
    """ Class for FightCade replays
    """

    def __init__(self):
        self.config = Config().config
        self.db = Database()
        self.replay = self.get_replay()
        self.description_text = ""
        self.detected_characters = []

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            self.supported_games = json.load(f)

        # On replay start create a status file in /tmp - Legacy?
        with open('/tmp/fcreplay_status', 'w') as f:
            f.write(f"{self.replay.id} STARTED")

    def handle_fail(func):
        """Handle Failure decorator
        """
        def failed(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception:
                trace_back = sys.exc_info()[2]
                log.error(f"Excption: {str(traceback.format_tb(trace_back))},  shutting down")
                log.info(f"Setting {self.replay.id} to failed")
                self.db.update_failed_replay(challenge_id=self.replay.id)
                self.update_status(status.FAILED)

                if self.config['kill_all']:
                    subprocess.run('killall5')

                time.sleep(5)
                sys.exit(1)

        return failed

    @handle_fail
    def get_replay(self):
        """Get a replay from the database
        """
        log.info('Getting replay from database')
        if self.config['player_replay_first']:
            replay = self.db.get_oldest_player_replay()
            if replay is not None:
                log.info('Found player replay to encode')
                return replay
            else:
                log.info('No more player replays')

        if self.config['random_replay']:
            log.info('Getting random replay')
            replay = self.db.get_random_replay()
            return replay
        else:
            log.info('Getting oldest replay')
            replay = self.db.get_oldest_replay()

        return replay

    @handle_fail
    def get_characters(self):
        """Get characters (if they exist) from pickle file
        """
        c = CharacterDetection()
        self.detected_characters = c.get_characters()

        for i in self.detected_characters:
            self.db.add_detected_characters(
                challenge_id=self.replay.id,
                p1_char=i[0],
                p2_char=i[1],
                vid_time=i[2],
                game=self.replay.game
            )

    @handle_fail
    def add_job(self):
        """Update jobs database table with the current replay
        """
        start_time = datetime.datetime.utcnow()
        self.update_status(status.JOB_ADDED)
        self.db.add_job(
            challenge_id=self.replay.id,
            start_time=start_time,
            length=self.replay.length
        )

    @handle_fail
    def remove_job(self):
        """Remove job from database
        """
        self.update_status(status.REMOVED_JOB)
        self.db.remove_job(challenge_id=self.replay.id)

    @handle_fail
    def update_status(self, status):
        """Update the replay status
        """
        log.info(f"Set status to {status}")
        # This file is legacy?
        with open('/tmp/fcreplay_status', 'w') as f:
            f.write(f"{self.replay.id} {status}")
        self.db.update_status(
            challenge_id=self.replay.id,
            status=status
        )

    @handle_fail
    def record(self):
        """Start recording a replay
        """
        log.info(
            f"Starting capture with {self.replay.id} and {self.replay.length}")
        time_min = int(self.replay.length / 60)
        log.info(f"Capture will take {time_min} minutes")

        self.update_status(status.RECORDING)

        # Star a recording store recording status
        log.debug(
            f"""Starting record.main with argumens:
            fc_challange_id={self.replay.id},
            fc_time={self.replay.length},
            kill_time={self.config['record_timeout']},
            fcadefbneo_path={self.config['fcadefbneo_path']},
            game_name={self.replay.game}""")
        record_status = Record().main(fc_challange_id=self.replay.id,
                                      fc_time=self.replay.length,
                                      kill_time=self.config['record_timeout'],
                                      fcadefbneo_path=self.config['fcadefbneo_path'],
                                      game_name=self.replay.game
                                      )

        # Check recording status
        if record_status != "Pass":
            log.error(f"Recording failed on {self.replay.id},"
                      f"Status: {record_status}, exiting.")

            if record_status == "FailTimeout":
                raise TimeoutError
            else:
                log.error(f"Unknown error: ${record_status}, exiting")
                raise ValueError

        log.info("Capture finished")
        self.update_status(status.RECORDED)

        return True

    @handle_fail
    def sort_files(self, avi_files_list):
        log.info("Sorting files")

        if len(avi_files_list) > 1:
            avi_dict = {}
            for i in avi_files_list:
                m = re.search('(.*)_([0-9a-fA-F]+).avi', i)
                avi_dict[i] = int(m.group(2), 16)
            sorted_avi_files_list = []
            for i in sorted(avi_dict.items(), key=lambda x: x[1]):
                sorted_avi_files_list.append(i[0])
            avi_files = [f"{self.config['fcadefbneo_path']}/avi/" + i for i in sorted_avi_files_list]
        else:
            avi_files = [f"{self.config['fcadefbneo_path']}/avi/" + avi_files_list[0]]

        return avi_files

    @handle_fail
    def encode(self):
        log.info("Encoding lossless file")

        avi_files_list_glob = glob.glob(f"{self.config['fcadefbneo_path']}/avi/*.avi")
        avi_files_list = []

        for f in avi_files_list_glob:
            avi_files_list.append(os.path.basename(f))

        log.info(f"List of files is: {avi_files_list}")

        # Sort files
        avi_files = self.sort_files(avi_files_list)

        # I can't stress enough how much you should not try and mess with the encoding settings!
        # 1. ffmpeg will not handle files generated by fbneo
        # 2. The files that fbneo generates need to be transcoded before they are encoded to h264 (h265 doesn't work well with archive.org)
        mencoder_options = [
            '/opt/mplayer/bin/mencoder', '-oac', 'mp3lame', '-lameopts', 'vbr=3',
            '-ovc', 'x264', '-x264encopts', 'preset=slow:threads=auto',
            '-vf', 'flip,scale=960:720,dsize=4/3,expand=1280:720:160:0::',
            *avi_files,
            '-of', 'lavf',
            '-o', f"{self.config['fcadefbneo_path']}/avi/{self.replay.id}.mp4"
        ]

        log.info(f"Running mencoder with: {' '.join(mencoder_options)}")

        mencoder_rc = subprocess.run(
            mencoder_options,
            capture_output=True
        )

        try:
            mencoder_rc.check_returncode()
        except subprocess.CalledProcessError as e:
            log.error(f"Unable to process avi files. Return code: {e.returncode}, stdout: {mencoder_rc.stdout}, stderr: {mencoder_rc.stderr}")
            raise e

    @handle_fail
    def remove_old_avi_files(self):
        log.info('Removing old avi files')
        old_files = glob.glob(f"{self.config['fcadefbneo_path']}/avi/*.avi")

        for f in old_files:
            log.info(f"Removing {f}")
            os.unlink(f)

    @handle_fail
    def set_description(self):
        """Set the description of the video

        Returns:
            Boolean: Success or failure
        """
        log.info("Creating description")

        if len(self.detected_characters) > 0:
            self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} vs "\
                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay} "\
                f"\nFightcade replay id: {self.replay.id}"

            for match in self.detected_characters:
                self.description_text += f"\n{self.replay.p1}: {match[0]}, {self.replay.p2}: {match[1]}  - {match[2]}" \
                    f"\n{match[0]} vs {match[1]}"
        else:
            self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} vs " \
                                    f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}" \
                                    f"\nFightcade replay id: {self.replay.id}"

        # Read the append file:
        if self.config['description_append_file'][0] is True:
            # Check if file exists:
            if not os.path.exists(self.config['description_append_file'][1]):
                log.error(
                    f"Description append file {self.config['description_append_file'][1]} doesn't exist")
                return False
            else:
                with open(self.config['description_append_file'][1], 'r') as description_append:
                    self.description_text += "\n" + description_append.read()

        self.update_status(status.DESCRIPTION_CREATED)
        log.info("Finished creating description")

        # Add description to database
        log.info('Adding description to database')
        self.db.add_description(
            challenge_id=self.replay.id, description=self.description_text)

        log.debug(
            f"Description Text is: {self.description_text.encode('unicode-escape')}")
        return True

    @handle_fail
    def create_thumbnail(self):
        """Create thumbnail from video
        """
        log.info("Making thumbnail")

        self.thumbnail = Thumbnail().get_thumbnail(self.replay)

        self.update_status(status.THUMBNAIL_CREATED)
        log.info("Finished making thumbnail")

    @handle_fail
    def update_thumbnail(self):
        """Add text, country and ranks to thumbnail
        """
        log.info("Updating thumbnail")

        UpdateThumbnail().update_thumbnail(self.replay, self.thumbnail)

    @handle_fail
    @retry(wait_random_min=30000, wait_random_max=60000, stop_max_attempt_number=3)
    def upload_to_ia(self):
        """Upload to internet archive

        Sometimes it will return a 403, even though the file doesn't already
        exist. So we decorate the function with the @retry decorator to try
        again in a little bit. Max of 3 tries
        """
        self.update_status(status.UPLOADING_TO_IA)
        title = f"{self.supported_games[self.replay.game]['game_name']}: ({self.replay.p1_loc}) {self.replay.p1} vs" \
                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}"
        filename = f"{self.replay.id}.mp4"
        date_short = str(self.replay.date_replay)[10]

        # Make identifier for Archive.org
        ident = str(self.replay.id).replace("@", "-")
        fc_video = get_item(ident)

        metadata = {
            'title': title,
            'mediatype': self.config['ia_settings']['mediatype'],
            'collection': self.config['ia_settings']['collection'],
            'date': date_short,
            'description': self.description_text,
            'subject': self.config['ia_settings']['subject'],
            'creator': self.config['ia_settings']['creator'],
            'language': self.config['ia_settings']['language'],
            'licenseurl': self.config['ia_settings']['license_url']}

        log.info("Starting upload to archive.org")
        fc_video.upload(f"{self.config['fcadefbneo_path']}/avi/{filename}",
                        metadata=metadata, verbose=True)

        self.update_status(status.UPLOADED_TO_IA)
        log.info("Finished upload to archive.org")

    @handle_fail
    def upload_to_yt(self):
        """Upload video to youtube
        """
        self.update_status(status.UPLOADING_TO_YOUTUBE)
        title = f"{self.supported_games[self.replay.game]['game_name']}: ({self.replay.p1_loc}) {self.replay.p1} vs "\
                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}"
        filename = f"{self.replay.id}.mp4"
        import_format = '%Y-%m-%d %H:%M:%S'
        date_raw = datetime.datetime.strptime(
            str(self.replay.date_replay), import_format)

        if len(title) > 100:
            title = title[:99]
        log.info(f"Title is: {title}")

        # YYYY-MM-DDThh:mm:ss.sZ
        youtube_date = date_raw.strftime('%Y-%m-%dT%H:%M:%S.0Z')

        # Check if youtube-upload is installed
        if shutil.which('youtube-upload') is not None:
            # Check if credentials file exists
            if not os.path.exists(self.config['youtube_credentials']):
                log.error("Youtube credentials don't exist exist")
                return False

            if not os.path.exists(self.config['youtube_secrets']):
                log.error("Youtube secrets don't exist")
                return False

            # Find number of uploads today
            day_log = self.db.get_youtube_day_log()

            # Check max uploads
            # Get todays date, dd-mm-yyyy
            today = datetime.date.today()

            # Check the log is for today
            if day_log.date.date() == today:
                # Check number of uploads
                if day_log.count >= int(self.config['youtube_max_daily_uploads']):
                    log.info("Maximum uploads reached for today")
                    return False
            else:
                # It's a new day, update the counter
                log.info("New day for youtube uploads")
                self.db.update_youtube_day_log_count(count=1, date=today)

            # Create description file
            with open(f"{self.config['fcreplay_dir']}/tmp/description.txt", 'w') as description_file:
                description_file.write(self.description_text)

            # Do upload
            log.info("Uploading to youtube")
            yt_rc = subprocess.run(
                [
                    'youtube-upload',
                    '--credentials-file', self.config['youtube_credentials'],
                    '--client-secrets', self.config['youtube_secrets'],
                    '-t', title,
                    '-c', 'Gaming',
                    '--description-file', f"{self.config['fcreplay_dir']}/tmp/description.txt",
                    '--recording-date', youtube_date,
                    '--default-language', 'en',
                    '--thumbnail', str(self.thumbnail),
                    f"{self.config['fcadefbneo_path']}/avi/{filename}",
                ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            youtube_id = yt_rc.stdout.decode().rstrip()

            log.info(f"Youtube id: {youtube_id}")
            log.info(yt_rc.stderr.decode())

            if not self.replay.player_requested:
                log.info('Updating day_log')
                log.info("Updating counter")
                self.db.update_youtube_day_log_count(
                    count=day_log.count + 1, date=today)

            # Remove description file
            os.remove(f"{self.config['fcreplay_dir']}/tmp/description.txt")
            if len(youtube_id) < 4:
                log.info('Unable to upload to youtube')
                self.db.set_youtube_uploaded(self.replay.id, False)
            else:
                self.db.set_youtube_uploaded(self.replay.id, True)
                self.db.set_youtube_id(self.replay.id, youtube_id)

            self.update_status(status.UPLOADED_TO_YOUTUBE)
            log.info('Finished uploading to Youtube')
        else:
            raise ModuleNotFoundError

    @handle_fail
    def set_created(self):
        self.update_status(status.FINISHED)
        self.db.update_created_replay(challenge_id=self.replay.id)
