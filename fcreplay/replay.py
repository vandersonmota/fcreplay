import datetime
import os
import shutil
import subprocess
import sys
import traceback

from internetarchive import get_item
from retrying import retry

from fcreplay.record import Record
from fcreplay.status import status
from fcreplay.logging import Logging
from fcreplay.config import Config
from fcreplay.database import Database
from fcreplay.gcloud import Gcloud


class Replay:
    """ Class for FightCade replays
    """

    def __init__(self):
        self.config = Config().config
        self.db = Database()
        self.replay = self.get_replay()
        self.description_text = ""

        # On replay start create a status file in /tmp
        # This is used to determine shutdown status for a replay
        with open('/tmp/fcreplay_status', 'w') as f:
            f.write(f"{self.replay.id} STARTED")

    def handle_fail(func):
        """Handle Failure decorator
        """
        def failed(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                trace_back = sys.exc_info()[2]
                Logging().error(f"Excption: {str(traceback.format_tb(trace_back))},  shutting down")
                Logging().info(f"Setting {self.replay.id} to failed")
                self.db.update_failed_replay(challenge_id=self.replay.id)
                self.update_status(status.FAILED)

                if self.config['gcloud_destroy_on_fail']:
                    Gcloud().destroy_fcreplay(failed=True)
                sys.exit(1)

        return failed

    @handle_fail
    def get_replay(self):
        """Get a replay from the database
        """
        Logging().info('Getting replay from database')
        if self.config['player_replay_first']:
            replay = self.db.get_oldest_player_replay()
            if replay is not None:
                Logging().info('Found player replay to encode')
                return replay
            else:
                Logging().info('No more player replays')

        if self.config['random_replay']:
            Logging().info('Getting random replay')
            replay = self.db.get_random_replay()
            return replay
        else:
            Logging().info('Getting oldest replay')
            replay = self.db.get_oldest_replay()

        return replay

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
        Logging().info(f"Set status to {status}")
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
        Logging().info(
            f"Starting capture with {self.replay.id} and {self.replay.length}")
        time_min = int(self.replay.length / 60)
        Logging().info(f"Capture will take {time_min} minutes")

        self.update_status(status.RECORDING)

        # Star a recording store recording status
        Logging().debug(
            f"""Starting record.main with argumens:
            fc_challange_id={self.replay.id},
            fc_time={self.replay.length},
            kill_time={self.config['record_timeout']},
            fcadefbneo_path={self.config['fcadefbneo_path']},
            fcreplay_path={self.config['fcreplay_dir']},
            game_name={self.replay.game}""")
        record_status = Record().main(fc_challange_id=self.replay.id,
                                      fc_time=self.replay.length,
                                      kill_time=self.config['record_timeout'],
                                      fcadefbneo_path=self.config['fcadefbneo_path'],
                                      fcreplay_path=self.config['fcreplay_dir'],
                                      game_name=self.replay.game
                                      )

        # Check recording status
        if record_status != "Pass":
            Logging().error(f"Recording failed on {self.replay.id},"
                            f"Status: {record_status}, exiting.")

            if record_status == "FailTimeout":
                raise TimeoutError
            else:
                Logging().error(f"Unknown error: ${record_status}, exiting")
                raise ValueError

        Logging().info("Capture finished")
        self.update_status(status.RECORDED)

        return True

    @handle_fail
    def move(self):
        """Move files to finished area
        """
        avi_files_list = os.listdir(f"{self.config['fcadefbneo_path']}/avi")
        for f in avi_files_list:
            shutil.move(f"{self.config['fcadefbneo_path']}/avi/{f}",
                        f"{self.config['fcreplay_dir']}/finished/{f}")

        self.update_status(status.MOVED)

    @handle_fail
    def encode(self):
        Logging().info("Encoding file")
        avi_files_list = os.listdir(f"{self.config['fcreplay_dir']}/finished")
        if len(avi_files_list) > 1:
            avi_dict = {i: int(i.split('_')[1].split('.')[0], 16) for i in avi_files_list}
            sorted_avi_files_list = []
            for i in sorted(avi_dict.items(), key=lambda x: x[1]):
                sorted_avi_files_list.append(i[0])
            avi_files = [f"{self.config['fcreplay_dir']}/finished/" + i for i in sorted_avi_files_list]
        else:
            avi_files = avi_files_list

        # I can't stress enough how much you should not try and mess with the encoding settings!
        # 1. ffmpeg will not handle files generated by fbneo
        # 2. x264 for whatever reason inserts audio delay
        mencoder_options = [
            'mencoder', '-oac', 'mp3lame', '-lameopts', 'vbr=3',
            '-ovc', 'lavc', '-lavcopts', 'vcodec=mpeg4:vbitrate=4000',
            '-vf', 'flip,scale=800:600,dsize=4/3',
            *avi_files,
            '-of', 'lavf',
            '-o', f"{self.config['fcreplay_dir']}/finished/{self.replay.id}.mkv"
        ]

        Logging().info(f"Running mencoder with: {' '.join(mencoder_options)}")

        mencoder_rc = subprocess.run(
            mencoder_options,
            capture_output=True
        )

        try:
            mencoder_rc.check_returncode()
        except subprocess.CalledProcessError as e:
            Logging().error(f"Unable to process avi files. Return code: {e.returncode}, stdout: {mencoder_rc.stdout}, stderr: {mencoder_rc.stderr}")
            raise e

    @handle_fail
    def set_description(self):
        """Set the description of the video

        Returns:
            Boolean: Success or failure
        """
        Logging().info("Creating description")

        self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} vs " \
                                f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}" \
                                f"\nFightcade replay id: {self.replay.id}"

        # Read the append file:
        if self.config['description_append_file'][0] is True:
            # Check if file exists:
            if not os.path.exists(self.config['description_append_file'][1]):
                Logging().error(
                    f"Description append file {self.config['description_append_file'][1]} doesn't exist")
                return False
            else:
                with open(self.config['description_append_file'][1], 'r') as description_append:
                    self.description_text += "\n" + description_append.read()

        self.update_status(status.DESCRIPTION_CREATED)
        Logging().info("Finished creating description")

        # Add description to database
        Logging().info('Adding description to database')
        self.db.add_description(
            challenge_id=self.replay.id, description=self.description_text)

        Logging().debug(
            f"Description Text is: {self.description_text.encode('unicode-escape')}")
        return True

    @handle_fail
    def create_thumbnail(self):
        """Create thumbnail from video
        """
        Logging().info("Making thumbnail")
        filename = f"{self.replay.id}.mkv"
        subprocess.run([
            "ffmpeg",
            "-ss", "20",
            "-i", f"{self.config['fcreplay_dir']}/finished/{filename}",
            "-vframes:v", "1",
            f"{self.config['fcreplay_dir']}/tmp/thumbnail.jpg"])

        self.update_status(status.THUMBNAIL_CREATED)
        Logging().info("Finished making thumbnail")

    @handle_fail
    @retry(wait_random_min=30000, wait_random_max=60000, stop_max_attempt_number=3)
    def upload_to_ia(self):
        """Upload to internet archive

        Sometimes it will return a 403, even though the file doesn't already
        exist. So we decorate the function with the @retry decorator to try
        again in a little bit. Max of 3 tries
        """
        self.update_status(status.UPLOADING_TO_IA)
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

        Logging().info("Starting upload to archive.org")
        fc_video.upload(f"{self.config['fcreplay_dir']}/finished/{filename}",
                        metadata=metadata, verbose=True)

        self.update_status(status.UPLOADED_TO_IA)
        Logging().info("Finished upload to archive.org")

    @handle_fail
    def upload_to_yt(self):
        """Upload video to youtube
        """
        self.update_status(status.UPLOADING_TO_YOUTUBE)
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
                Logging().error("Youtube credentials don't exist exist")
                return False

            if not os.path.exists(self.config['youtube_secrets']):
                Logging().error("Youtube secrets don't exist")
                return False

            # Check min and max length:
            if (int(self.replay.length) / 60) < int(self.config['yt_min_length']):
                Logging().info("Replay is too short. Not uploading to youtube")
                return False
            if (int(self.replay.length) / 60) > int(self.config['yt_max_length']):
                Logging().info("Replay is too long. Not uploading to youtube")
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
                    Logging().info("Maximum uploads reached for today")
                    return False
            else:
                # It's a new day, update the counter
                Logging().info("New day for youtube uploads")
                self.db.update_youtube_day_log_count(count=1, date=today)

            # Create description file
            with open(f"{self.config['fcreplay_dir']}/tmp/description.txt", 'w') as description_file:
                description_file.write(self.description_text)

            # Do upload
            Logging().info("Uploading to youtube")
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

            Logging().info(yt_rc.stdout.decode())
            Logging().info(yt_rc.stderr.decode())

            if not self.replay.player_requested:
                Logging().info('Updating day_log')
                Logging().info("Updating counter")
                self.db.update_youtube_day_log_count(
                    count=day_log.count + 1, date=today)

            # Remove description file
            os.remove(f"{self.config['fcreplay_dir']}/tmp/description.txt")

            self.update_status(status.UPLOADED_TO_YOUTUBE)
            Logging().info('Finished uploading to Youtube')
        else:
            raise ModuleNotFoundError

    @handle_fail
    def remove_generated_files(self):
        """Remove generated files

        Generated files are thumbnail and videofile
        """
        Logging().info("Removing old files")
        filename = f"{self.replay.id}.mkv"
        os.remove(f"{self.config['fcreplay_dir']}/finished/{filename}")
        os.remove(f"{self.config['fcreplay_dir']}/tmp/thumbnail.jpg")

        self.update_status(status.REMOVED_GENERATED_FILES)
        Logging().info("Finished removing files")

    @handle_fail
    def set_created(self):
        self.update_status(status.FINISHED)
        self.db.update_created_replay(challenge_id=self.replay.id)
