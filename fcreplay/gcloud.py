import json
import logging
import os
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
        'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience='
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