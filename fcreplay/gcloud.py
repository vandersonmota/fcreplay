#!/usr/bin/env python
"""fcreplaydestroy.

Usage:
  fcreplaydestory destroy
  fcreplaydestroy (-h | --help)

Options:
  -h --help         Show this screen.
"""
from docopt import docopt
import json
import logging
import requests

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

# Setup Log
logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        filename=config['logfile'],
        level=config['loglevel'],
        datefmt='%Y-%m-%d %H:%M:%S'
)

REGION = config['gcloud_region']
PROJECT_ID = config['gcloud_project']


def destroy_fcreplay():
    logging.info("Starting destroy_fcreplay")
    RECEIVING_FUNCTION = 'destroy_fcreplay'

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
    function_response = requests.get(function_url, headers=function_headers)

    logging.info(f"destroy_fcreplay retruned: {function_response.status_code}")
    status = function_response.status_code
    return(status)


def console():
    arguments = docopt(__doc__, version='fcreplaydestroy')

    if arguments['destroy'] is True:
        destroy_fcreplay()


if __name__ == "__main__":
    console()
