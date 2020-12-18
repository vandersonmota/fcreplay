#!/usr/bin/env python
"""fcreplayconfig.

Usage:
  fcreplayconfig <config.json>
  fcreplayconfig (-h | --help)

Options:
  -h --help         Show this screen.
"""
from docopt import docopt
from cerberus import Validator
import base64
import json
import os
import sys


class Config:
    def __init__(self):
        self.schema = {
            'description_append_file': {
                'type': 'list',
                'required': True,
                'meta': {
                    'description': "Enable description to be appended from file",
                    'default': [False, '/path/to/description_file.txt'],
                }
            },
            'fcadefbneo_path': {
                'type': 'string',
                'required': True,
                'meta': {
                    'default': '/home/fcrecorder/fcreplay/Fightcade/emulator/fbneo',
                    'description': 'Path to fcadefbneo'
                },
            },
            'fcreplay_dir': {
                'type': 'string',
                'required': True,
                'meta': {
                    'default': '/home/fcrecorder/fcreplay',
                    'description': 'Path of where to run fcreplay',
                }
            },
            'gcloud_compute_service_account': {
                'type': 'string',
                'meta': {
                    'default': 'some-service-account123@project.iam.gserviceaccount.com',
                    'description': 'Google cloud service account email address'
                }
            },
            'gcloud_instance_max': {
                'type': 'number',
                'meta': {
                    'default': 5,
                    'description': 'Maximum number of cloud recording instances to run',
                }
            },
            'gcloud_project': {
                'type': 'string',
                'meta': {
                    'default': 'some-project-id-123',
                    'description': 'Google cloud project id'
                }
            },
            'gcloud_region': {
                'type': 'string',
                'meta': {
                    'default': 'some-region',
                    'description': 'Google cloud region'
                }
            },
            'gcloud_zone': {
                'type': 'string',
                'meta': {
                    'default': 'some-zone',
                    'description': 'Google cloud zone'
                }
            },
            'get_weekly_replay_pages': {
                'type': 'number',
                'meta': {
                    'default': 1,
                    'description': 'Number of replay pages to get for weekly replays'
                }
            },
            'ia_settings': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'collection': {
                        'type': 'string',
                        'required': True,
                    },
                    'creator': {
                        'type': 'string',
                        'required': True,
                    },
                    'language': {
                        'type': 'string',
                        'required': True
                    },
                    'license_url': {
                        'type': 'string',
                        'required': True,
                    },
                    'mediatype': {
                        'type': 'string',
                        'required': True,
                    },
                    'subject': {
                        'type': 'list',
                        'required': True
                    }
                },
                'meta': {
                    'default': {
                        "collection": "Collection-Name",
                        "creator": "Author",
                        "language": "Language",
                        "license_url": "http://creativecommons.org/publicdomain/zero/1.0",
                        "mediatype": "video",
                        "subject": ["video", "fightcade"]
                    },
                    'description': 'Dictionary of Internet Archive settings'
                }
            },
            'logging_loki': {
                'type': 'dict',
                'required': True,
                'meta': {
                    'default': {
                        'enabled': False,
                        'password': 'password',
                        'url': 'https://my-loki-instance:1234/loki/api/v1/push',
                        'username': 'username'
                    },
                    'description': 'Enables logging to a loki endpoint'
                }
            },
            'logfile': {
                'type': 'string',
                'meta': {
                    'default': '/home/fcrecorder/fcreplay/fcreplay.log',
                    'description': 'Path of where to write log file',
                }
            },
            'loglevel': {
                'type': 'string',
                'allowed': ['ERROR', 'INFO', 'DEBUG'],
                'required': True,
                'meta': {
                    'default': 'INFO',
                    'description': 'Log level',
                }
            },
            'max_replay_length': {
                'type': 'number',
                'required': True,
                'meta': {
                    'default': 10800,
                    'description': 'Maximum replay length to accept in seconds',
                }
            },
            'min_replay_length': {
                'type': 'number',
                'required': True,
                'meta': {
                    'default': 60,
                    'description': 'Minimum replay length to accept in seconds',
                }
            },
            'player_replay_first': {
                'type': 'boolean',
                'required': True,
                'meta': {
                    'default': True,
                    'description': 'Look for player replay to record first',
                }
            },
            'random_replay': {
                'type': 'boolean',
                'required': True,
                'meta': {
                    'default': False,
                    'description': 'Encode a random replay, otherwise encode the oldest'
                }
            },
            'record_timeout': {
                'type': 'number',
                'required': True,
                'meta': {
                    'default': 120,
                    'description': 'Time in seconds before marking a replay as failed if start not detected'
                }
            },
            'remove_generated_files': {
                'type': 'boolean',
                'required': True,
                'meta': {
                    'default': True,
                    'description': 'Delete generated files after finished recording'
                }
            },
            'secret_key': {
                'type': 'string',
                'required': True,
                'meta': {
                    'default': base64.b64encode(os.urandom(64)).decode(),
                    'description': 'Secret key used for flask/site cookies'
                }
            },
            'sql_baseurl': {
                'type': 'string',
                'required': True,
                'meta': {
                    'default': 'postgres://username:password@url.com:1234',
                    'description': 'URL of database'
                }
            },
            'supported_games': {
                'type': 'dict',
                'required': True,
                'meta': {
                    'default': {
                        "gameid": {
                            "character_detect": False,
                            "game_name": "Full Game NAme"
                        },
                    },
                }
            },
            'upload_to_ia': {
                'type': 'boolean',
                'required': True,
                'meta': {
                    'default': False,
                    'description': 'Upload replay to Internet Archive'
                }
            },
            'upload_to_yt': {
                'type': 'boolean',
                'required': True,
                'meta': {
                    'default': False,
                    'description': 'Upload replays to Youtube'
                }
            },
            'youtube_credentials': {
                'type': 'string',
                'meta': {
                    'default': '/path/to/youtube-upload-credentials.json',
                    'description': 'Path to youtube-upload-credentials.json file'
                }
            },
            'youtube_max_daily_uploads': {
                'type': 'number',
                'meta': {
                    'default': 5,
                    'description': 'Maximum number of uploads to youtube per day'
                }
            },
            'youtube_secrets': {
                'type': 'string',
                'meta': {
                    'default': '/path/to/youtube-secrets.json',
                    'description': 'Path to youtube-secrets.json file'
                }
            },
            'yt_max_length': {
                'type': 'number',
                'meta': {
                    'default': 120,
                    'description': 'Maximum replay length to upload to youtube in minutes'
                }
            },
            'yt_min_length': {
                'type': 'number',
                'meta': {
                    'default': 10,
                    'description': 'Minimum replay length to upload to youtube in minutes'
                }
            }
        }
        self.config = self.get_config()
        self.validate_config(self.config, self.schema)

    def get_config(self):
        """Returns config based on FCREPLAY_CONFIG environment variable
        If variable is unset, then look for config.json
        If file does not exist, generate default config
        """
        try:
            if 'FCREPLAY_CONFIG' in os.environ:
                with open(os.environ['FCREPLAY_CONFIG'], 'r') as json_data_file:
                    return json.load(json_data_file)
            else:
                with open("config.json", 'r') as json_data_file:
                    return json.load(json_data_file)

        except FileNotFoundError as e:
            default_json = {}
            for k in self.schema:
                print(self.schema[k])
                if 'default' in self.schema[k]['meta']:
                    default_json[k] = self.schema[k]['meta']['default']

            with open(e.filename, 'w') as f:
                json.dump(default_json, f, indent=4)

            print(f"Unable to find config, default config written to {e.filename}")
            print("Adjust default values and run again")
            sys.exit(1)

    def validate_config(self, config, schema):
        v = Validator()
        if v.validate(config, schema) is False:
            print(json.dumps(v.errors, indent=4))
            raise LookupError


def console():
    if 'REMOTE_DEBUG' in os.environ:
        print("Starting remote debugger on port 5678")
        import debugpy
        debugpy.listen(("0.0.0.0", 5678))
        print("Waiting for connection...")
        debugpy.wait_for_client()

    arguments = docopt(__doc__, version='fcreplayconfig')
    if '<config.json>' in arguments:
        os.environ['FCREPLAY_CONFIG'] = arguments['<config.json>']

        # Try to validate config file
        Config().config

        # If this works, then print success
        print("Configuration validated successfuly")


if __name__ == "__main__":
    console()
