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
from fcreplay import logging
import requests
import socket

config = Config().config

REGION = config['gcloud_region']
PROJECT_ID = config['gcloud_project']


def destroy_fcreplay(failed=False):
    """This function will destroy the current google cloud instance
    """
    logging.info("Starting destroy_fcreplay")
    RECEIVING_FUNCTION = 'destroy_fcreplay_instance'
    HOSTNAME = socket.gethostname()

    if 'fcreplay-image-' not in HOSTNAME:
        logging.info(f"Not destroying {HOSTNAME}")
        return(False)

    # Only retry if failed is false, by default this is false, but sometimes recording
    # fails. So we don't want to try and re-record them until we work out why they
    # have failed.
    if not failed:
        try:
            with open('/tmp/fcreplay_status', 'r') as f:
                line = f.readline()
                local_replay_id = line.split()[0].strip()
                local_replay_status = line.split()[1].strip()

            if local_replay_status in ['UPLOADING_TO_IA', 'UPLOADING_TO_YOUTUBE', 'UPLOADED_TO_IA', 'UPLOADED_TO_YOUTUBE']:
                logging.error(f"Not able to safely recover replay {local_replay_id}")
            elif local_replay_status not in ['FINISHED', 'REMOVED_GENERATED_FILES']:
                # Replay was in the middle of processing, going to set replay to be re-recorded
                db = Database()
                db.rerecord_replay(challenge_id=local_replay_id)
        except FileNotFoundError:
            logging.error('/tmp/fcreplay_status not found')

    function_url = f'https://{REGION}-{PROJECT_ID}.cloudfunctions.net/{RECEIVING_FUNCTION}'
    metadata_server_url = \
        f"http://metadata/computeMetadata/v1/instance/service-accounts/{config['gcloud_compute_service_account']}/identity?audience="
    token_full_url = metadata_server_url + function_url
    token_headers = {'Metadata-Flavor': 'Google'}

    # Fetch the token
    token_response = requests.get(token_full_url, headers=token_headers)
    jwt = token_response.text

    # Provide the token in the request to the receiving function
    function_headers = {'Authorization': f'bearer {jwt}'}
    function_response = requests.post(function_url, headers=function_headers, json={'instance_name': HOSTNAME})

    logging.info(f"destroy_fcreplay retruned: {function_response.status_code}")
    status = function_response.status_code
    return(status)


def console():
    arguments = docopt(__doc__, version='fcreplaydestroy')

    if arguments['destroy'] is True:
        destroy_fcreplay()


if __name__ == "__main__":
    console()
