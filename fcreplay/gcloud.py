#!/usr/bin/env python
"""fcreplaydestroy.

Usage:
  fcreplaydestroy destroy
  fcreplaydestroy (-h | --help)

Options:
  -h --help         Show this screen.
"""
from docopt import docopt
from fcreplay.database import Database
from fcreplay.config import Config
from fcreplay.logging import Logging
from pathlib import Path
import requests
import socket
import subprocess
import sys


class Gcloud:
    def __init__(self):
        self.config = Config().config

        self.REGION = self.config['gcloud_region']
        self.PROJECT_ID = self.config['gcloud_project']

    def destroy_fcreplay(self, failed=False):
        """Destry the current compute engine

        Checks for the existance of /tmp/destroying. If it exists then
        don't try and destroy fcreplay

        Args:
            failed (bool, optional): Updates the replay to failed. Defaults to False.
        """
        # Create destroying file
        try:
            Path('/tmp/destroying').touch(0o644, exist_ok=False)
        except FileExistsError:
            # File already exists, not running
            sys.exit(0)

        Logging().info("Starting destroy_fcreplay")
        RECEIVING_FUNCTION = 'destroy_fcreplay_instance'
        HOSTNAME = socket.gethostname()

        if 'fcreplay-image-' not in HOSTNAME:
            Logging().info(f"Not destroying {HOSTNAME}")
            return(False)

        # Only retry if failed is false, by default this is false, but sometimes recording
        # fails. So we don't want to try and re-record them until we work out why they
        # have failed.
        if failed is False:
            try:
                with open('/tmp/fcreplay_status', 'r') as f:
                    line = f.readline()
                    local_replay_id = line.split()[0].strip()
                    local_replay_status = line.split()[1].strip()

                if local_replay_status in ['UPLOADING_TO_IA', 'UPLOADING_TO_YOUTUBE', 'UPLOADED_TO_IA', 'UPLOADED_TO_YOUTUBE']:
                    Logging().error(f"Not able to safely recover replay {local_replay_id}")
                elif local_replay_status not in ['FINISHED', 'REMOVED_GENERATED_FILES']:
                    # Replay was in the middle of processing, going to set replay to be re-recorded
                    db = Database()
                    db.rerecord_replay(challenge_id=local_replay_id)
            except FileNotFoundError:
                Logging().error('/tmp/fcreplay_status not found')

        function_url = f'https://{self.REGION}-{self.PROJECT_ID}.cloudfunctions.net/{RECEIVING_FUNCTION}'
        metadata_server_url = \
            f"http://metadata/computeMetadata/v1/instance/service-accounts/{self.config['gcloud_compute_service_account']}/identity?audience="
        token_full_url = metadata_server_url + function_url
        token_headers = {'Metadata-Flavor': 'Google'}

        # Fetch the token
        token_response = requests.get(token_full_url, headers=token_headers)
        jwt = token_response.text

        # Provide the token in the request to the receiving function
        function_headers = {'Authorization': f'bearer {jwt}'}
        function_response = requests.post(function_url, headers=function_headers, json={'instance_name': HOSTNAME})

        Logging().info(f"destroy_fcreplay retruned: {function_response.status_code}")
        status = function_response.status_code

        if self.config['gcloud_shutdown_instance']:
            subprocess.run(['shutdown', 'now', '-h'])
        return(status)


def console():
    arguments = docopt(__doc__, version='fcreplaydestroy')

    g = Gcloud()
    if arguments['destroy'] is True:
        g.destroy_fcreplay()
