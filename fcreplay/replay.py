import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback

from internetarchive import get_item
from retrying import retry

from fcreplay import record as fc_record
from fcreplay.config import Config
from fcreplay.database import Database
from fcreplay.gcloud import destroy_fcreplay


class Replay:
    """ Class for FightCade replays
    """

    def __init__(self):
        self.config = Config().config

        self.db = Database()
        self.replay = self.get_replay()
        self.description_text = ""

        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s',
            filename=self.config['logfile'],
            level=self.config['loglevel'],
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def handle_fail(func):
        """Handle Failure decorator
        """
        def failed(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                trace_back = sys.exc_info()[2]
                line = trace_back.tb_lineno
                logging.error(traceback.print_tb(trace_back))
                logging.error(f"Excption: {e} on line: {line},  shutting down")
                logging.info(f"Setting {self.replay.id} to failed")
                self.db.update_failed_replay(challenge_id=self.replay.id)
                self.update_status("FAILED")

                if self.config['gcloud_destroy_on_fail']:
                    destroy_fcreplay()
                sys.exit(1)

        return failed

    @handle_fail
    def get_replay(self):
        """Get a replay from the database
        """
        logging.info('Getting replay from database')
        if self.config['player_replay']:
            replay = self.db.get_oldest_player_replay()
            if replay is not None:
                logging.info('Found player replay to encode')
                return replay
            else:
                logging.info('No more player replays')

        if self.config['random_replay']:
            logging.info('Getting random replay')
            replay = self.db.get_random_replay()
            return replay
        else:
            logging.info('Getting oldest replay')
            replay = self.db.get_oldest_replay()

        return replay

    @handle_fail
    def add_job(self):
        """Update jobs database table with the current replay
        """
        start_time = datetime.datetime.utcnow()
        self.update_status("JOB_ADDED")
        self.db.add_job(
            challenge_id=self.replay.id,
            start_time=start_time,
            length=self.replay.length
        )

    @handle_fail
    def remove_job(self):
        """Remove job from database
        """
        self.db.remove_job(challenge_id=self.replay.id)
        self.update_status("FINISHED")

    @handle_fail
    def update_status(self, status):
        """Update the replay status
        """
        logging.info(f"Set status to {status}")
        self.db.update_status(
            challenge_id=self.replay.id,
            status=status
        )

    @handle_fail
    def record(self):
        """Start recording a replay
        """
        logging.info(
            f"Starting capture with {self.replay.id} and {self.replay.length}")
        time_min = int(self.replay.length/60)
        logging.info(f"Capture will take {time_min} minutes")

        self.update_status('RECORDING')

        # Star a recording store recording status
        logging.debug(
            f"""Starting record.main with argumens:
            fc_challange_id={self.replay.id},
            fc_time={self.replay.length},
            kill_time={self.config['record_timeout']},
            fcadefbneo_path={self.config['fcadefbneo_path']},
            fcreplay_path={self.config['fcreplay_dir']},
            game_name={self.replay.game}""")
        record_status = fc_record.main(fc_challange_id=self.replay.id,
                                       fc_time=self.replay.length,
                                       kill_time=self.config['record_timeout'],
                                       fcadefbneo_path=self.config['fcadefbneo_path'],
                                       fcreplay_path=self.config['fcreplay_dir'],
                                       game_name=self.replay.game
                                       )

        # Check recording status
        if not record_status == "Pass":
            logging.error(f"Recording failed on {self.replay.id},"
                          "Status: \"{record_status}\", exiting.")

            if record_status == "FailTimeout":
                raise TimeoutError
            else:
                logging.error(f"Unknown error: ${record_status}, exiting")
                raise ValueError

        logging.info("Capture finished")
        self.update_status('RECORDED')

        return True

    @handle_fail
    def move(self):
        """Move files to finished area
        """
        avi_files_list = os.listdir(f"{self.config['fcadefbneo_path']}/avi")
        for f in avi_files_list:
            shutil.move(f"{self.config['fcadefbneo_path']}/avi/{f}",
                        f"{self.config['fcreplay_dir']}/finished/{f}")

        self.update_status('MOVED')

    @handle_fail
    def broken_fix(self):
        """Fix broken video

        When fcadefbneo recording is terminated, it potentially leaves the video in
        a broken state. To fix this ffmpeg is used to fix any errors in the video.
        """
        logging.info("Running ffmpeg to fix dirty video")

        avi_files_list = os.listdir(f"{self.config['fcreplay_dir']}/finished")
        avi_files_list.sort()

        brokenfix_rc = subprocess.run(
            [
                "ffmpeg", "-err_detect", "ignore_err",
                "-i", f"{self.config['fcreplay_dir']}/finished/{avi_files_list[-1]}",
                "-c", "copy",
                f"{self.config['fcreplay_dir']}/finished/{avi_files_list[-1]}.fixed.avi"
            ]
        )

        logging.info("Removing dirty file")
        os.remove(f"{self.config['fcreplay_dir']}/finished/{avi_files_list[-1]}")
        os.rename(f"{self.config['fcreplay_dir']}/finished/{avi_files_list[-1]}.fixed.avi",
                  f"{self.config['fcreplay_dir']}/finished/{avi_files_list[-1]}")

        self.update_status('BROKEN_CHECK')
        logging.info("Removed dirty file and fixed file")

    @handle_fail
    def encode(self):
        logging.info("Encoding file")
        avi_files_list = os.listdir(f"{self.config['fcreplay_dir']}/finished")
        avi_files_list.sort()
        avi_files = [f"{self.config['fcreplay_dir']}/finished/" + i for i in avi_files_list]

        logging.info("Running mencoder with:" + " ".join([
            'mencoder',
            '-oac', 'mp3lame', '-lameopts', 'abr:br=128',
            '-ovc', 'x264', '-x264encopts', 'preset=fast:crf=23:subq=1:threads=8', '-vf', 'flip,scale=800:600',
            *avi_files,
            '-o', f"{self.config['fcreplay_dir']}/finished/{self.replay.id}.mkv"]))

        mencoder_rc = subprocess.run([
            'mencoder',
            '-oac', 'mp3lame', '-lameopts', 'abr:br=128',
            '-ovc', 'x264', '-x264encopts', 'preset=fast:crf=23:subq=1:threads=8', '-vf', 'flip,scale=800:600',
            *avi_files,
            '-o', f"{self.config['fcreplay_dir']}/finished/{self.replay.id}.mkv"])

        try:
            mencoder_rc.check_returncode()
        except subprocess.CalledProcessError as e:
            logging.error(f"Unable to process avi files. Return code: {e.returncode}, Output: {e.output}")
            raise e

    @handle_fail
    def set_description(self):
        """Set the description of the video

        Returns:
            Boolean: Success or failure
        """
        logging.info("Creating description")

        self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} vs " \
                                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}" \
                                f"\nFightcade replay id: {self.replay.id}"

        # Read the append file:
        if self.config['description_append_file'][0] is True:
            # Check if file exists:
            if not os.path.exists(self.config['description_append_file'][1]):
                logging.error(
                    f"Description append file {self.config['description_append_file'][1]} doesn't exist")
                return False
            else:
                with open(self.config['description_append_file'][1]) as description_append:
                    self.description_text += description_append.read()

        self.update_status('DESCRIPTION_CREATED')
        logging.info("Finished creating description")

        # Add description to database
        logging.info('Adding description to database')
        self.db.add_description(
            challenge_id=self.replay.id, description=self.description_text)

        logging.debug(
            f"Description Text is: {self.description_text.encode('unicode-escape')}")
        return True

    @handle_fail
    def create_thumbnail(self):
        """Create thumbnail from video
        """
        logging.info("Making thumbnail")
        filename = f"{self.replay.id}.mkv"
        subprocess.run([
            "ffmpeg",
            "-ss", "20",
            "-i", f"{self.config['fcreplay_dir']}/finished/{filename}",
            "-vframes:v", "1",
            f"{self.config['fcreplay_dir']}/tmp/thumbnail.jpg"])

        self.update_status('THUMBNAIL_CREATED')
        logging.info("Finished making thumbnail")

    @handle_fail
    @retry(wait_random_min=30000, wait_random_max=60000, stop_max_attempt_number=3)
    def upload_to_ia(self):
        """Upload to internet archive

        Sometimes it will return a 403, even though the file doesn't already
        exist. So we decorate the function with the @retry decorator to try
        again in a little bit. Max of 3 tries
        """
        title = f"{self.config['supported_games'][self.replay.game]['game_name']}: ({self.replay.p1_loc}) {self.replay.p1} vs" \
                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}"
        filename = f"{self.replay.id}.mkv"
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

        logging.info("Starting upload to archive.org")
        fc_video.upload(f"{self.config['fcreplay_dir']}/finished/{filename}",
                        metadata=metadata, verbose=True)

        self.update_status('UPLOADED_TO_IA')
        logging.info("Finished upload to archive.org")

    @handle_fail
    def upload_to_yt(self):
        """Upload video to youtube
        """
        title = f"{self.config['supported_games'][self.replay.game]['game_name']}: ({self.replay.p1_loc}) {self.replay.p1} vs "\
                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}"
        filename = f"{self.replay.id}.mkv"
        import_format = '%Y-%m-%d %H:%M:%S'
        date_raw = datetime.datetime.strptime(
            str(self.replay.date_replay), import_format)

        # YYYY-MM-DDThh:mm:ss.sZ
        youtube_date = date_raw.strftime('%Y-%m-%dT%H:%M:%S.0Z')

        # Check if youtube-upload is installed
        if shutil.which('youtube-upload') is not None:
            # Check if credentials file exists
            if not os.path.exists(self.config['youtube_credentials']):
                logging.error("Youtube credentials don't exist exist")
                return False

            if not os.path.exists(self.config['youtube_secrets']):
                logging.error("Youtube secrets don't exist")
                return False

            # Check min and max length:
            if (int(self.replay.length)/60) < int(self.config['yt_min_length']):
                logging.info("Replay is too short. Not uploading to youtube")
                return False
            if (int(self.replay.length)/60) > int(self.config['yt_max_length']):
                logging.info("Replay is too long. Not uploading to youtube")
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
                    logging.info("Maximum uploads reached for today")
                    return False
            else:
                # It's a new day, update the counter
                logging.info("New day for youtube uploads")
                self.db.update_youtube_day_log_count(count=1, date=today)

            # Create description file
            with open(f"{self.config['fcreplay_dir']}/tmp/description.txt", 'w') as description_file:
                description_file.write(self.description_text)

            # Do upload
            logging.info("Uploading to youtube")
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
                    '--thumbnail', f"{self.config['fcreplay_dir']}/tmp/thumbnail.jpg",
                    f"{self.config['fcreplay_dir']}/finished/{filename}",
                ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            logging.info(yt_rc.stdout.decode())
            logging.info(yt_rc.stderr.decode())

            if not self.replay.player_requested:
                logging.info('Updating day_log')
                logging.info("Updating counter")
                self.db.update_youtube_day_log_count(
                    count=day_log.count+1, date=today)

            # Remove description file
            os.remove(f"{self.config['fcreplay_dir']}/tmp/description.txt")

            self.update_status('UPLOADED_TO_YOUTUBE')
            logging.info('Finished uploading to Youtube')
        else:
            raise ModuleNotFoundError

    @handle_fail
    def remove_generated_files(self):
        """Remove generated files

        Generated files are thumbnail and videofile
        """
        logging.info("Removing old files")
        filename = f"{self.replay.id}.mkv"
        os.remove(f"{self.config['fcreplay_dir']}/finished/{filename}")
        os.remove(f"{self.config['fcreplay_dir']}/tmp/thumbnail.jpg")

        self.update_status("REMOVED_GENERATED_FILES")
        logging.info("Finished removing files")

    @handle_fail
    def set_created(self):
        self.db.update_created_replay(challenge_id=self.replay.id)
