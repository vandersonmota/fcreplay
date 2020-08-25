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