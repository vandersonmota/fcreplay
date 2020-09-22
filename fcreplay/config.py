from cerberus import Validator
import json
import os


class Config:
    def __init__(self):
        if 'FCREPLAY_CONFIG' in os.environ:
            with open(os.environ['FCREPLAY_CONFIG'], 'r') as json_data_file:
                self.config = json.load(json_data_file)
        else:
            with open("config.json", 'r') as json_data_file:
                self.config = json.load(json_data_file)

        self.schema = {
            "auto_add_more": {"type": "boolean"},
            "auto_add_search_string": {"type": "string"},
            "channel": {"type": "string"},
            "description_append_file": {"type": "list"},
            "fcadefbneo_path": {"type": "string"},
            "fcreplay_dir": {"type": "string"},
            "gcloud_compute_service_account": {"type": "string"},
            "gcloud_destroy_on_fail": {"type": "boolean"},
            "gcloud_destroy_when_stopped": {"type": "boolean"},
            "gcloud_instance_max": {"type": "integer"},
            "gcloud_project": {"type": "string"},
            "gcloud_region": {"type": "string"},
            "gcloud_zone": {"type": "string"},
            "ia_settings": {"type": "dict"},
            "logfile": {"type": "string"},
            "loglevel": {"type": "string"},
            "max_replay_length": {"type": "integer"},
            "min_replay_length": {"type": "integer"},
            "password": {"type": "string"},
            "player_replay": {"type": "integer"},
            "random_replay": {"type": "integer"},
            "record_timeout": {"type": "integer"},
            "remove_generated_files": {"type": "boolean"},
            "replay_pages": {"type": "string"},
            "secret_key": {"type": "string"},
            "sql_baseurl": {"type": "string"},
            "supported_games": {"type": "dict"},
            "upload_to_ia": {"type": "boolean"},
            "upload_to_yt": {"type": "boolean"},
            "username": {"type": "string"},
            "youtube_credentials": {"type": "string"},
            "youtube_max_daily_uploads": {"type": "integer"},
            "youtube_secrets": {"type": "string"},
            "yt_max_length": {"type": "integer"},
            "yt_min_length": {"type": "integer"}
        }
        v = Validator()
        if v.validate(self.config, self.schema) is False:
            print(v.errors)
            raise Exception
