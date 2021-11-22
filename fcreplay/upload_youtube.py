from fcreplay.config import Config
from fcreplay.database import Database

import datetime
import logging
import os

from types import SimpleNamespace
from youtube_upload import main as youtube_upload

log = logging.getLogger('fcreplay')

class UploadYouTube:
    def __init__(self, title, description, tags, video_path, recording_date, playlist=False, thumbnail=False, player_requested=False):
        self.config = Config()
        self.db = Database()
        self.day_log = self.db.get_youtube_day_log()
        self.today = datetime.date.today()
        self.player_requested = player_requested

        self.options = SimpleNamespace(
            client_secrets=self.config.youtube_secrets,
            credentials=self.config.youtube_credentials,
            auth_browser=False,
            title=title,
            description=description,
            tags=tags,
            title_template="",
            category='Gaming',
            default_language="en",
            default_audio_language="en",
            embeddable=True,
            publish_at=None,
            privacy="public",
            license="youtube",
            location=None,
            recording_date=recording_date,
            open_link=False,
            thumb=thumbnail,
            playlist=playlist,
            chunksize=1024 * 1024 * 8,
        )
        self.video_path = video_path

    def _check_credentials(self):
        # Check if credentials file exists
        if not os.path.exists(self.config.youtube_credentials):
            log.error("Youtube credentials don't exist exist")
            return False

        if not os.path.exists(self.config.youtube_secrets):
            log.error("Youtube secrets don't exist")
            return False

    def _get_auth(self):
        return youtube_upload.auth.get_resource(self.options.client_secrets, self.options.credentials, None)

    def _check_day_log(self):

        # Check max uploads
        # Get todays date, dd-mm-yyyy

        # Check the log is for today
        if self.day_log.date.date() == self.today:
            # Check number of uploads
            if self.day_log.count >= int(self.config.youtube_max_daily_uploads):
                log.info("Maximum uploads reached for today")
                return False
        else:
            # It's a new day, update the counter
            log.info("New day for youtube uploads")
            self.db.update_youtube_day_log_count(count=1, date=self.today)

        return True

    def _update_day_log(self):
        # Update the day log
        if not self.player_requested:
            log.info('Updating day_log')
            log.info("Updating counter")
            self.db.update_youtube_day_log_count(count=self.day_log.count + 1, date=self.today)

    def upload(self):
        # Check if we can upload
        if not self._check_day_log():
            return False

        youtube = self._get_auth()

        try:
            if youtube:
                youtube_id = youtube_upload.upload_youtube_video(youtube=youtube, options=self.options, video_path=self.video_path, total_videos=1, index=0)
                if self.options.thumb:
                    youtube.thumbnails().set(videoId=youtube_id, media_body=self.options.thumb).execute()
                if self.options.playlist:
                    youtube_upload.playlists.add_video_to_playlist(youtube, youtube_id, title=youtube_upload.lib.to_utf8(self.options.playlist), privacy=self.options.privacy)
        except Exception as e:
            log.error(f"Unable to upload to youtube: {e}")
            return False

        self._update_day_log()

        return youtube_id
