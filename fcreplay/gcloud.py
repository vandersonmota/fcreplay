import logging
import json
import requests
import os

import google.cloud.storage as storage

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
BUCKET_NAME = config['gcloud_bucket']

# This requires: export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config['gcloud_storage_creds_path']


def upload_video(source_file_name, destination_file_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_file_name)

    blob.upload_from_filename(source_file_name)


def download_video(source_file_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(source_file_name)
    blob.download_to_filename(destination_file_name)


def launch_fcreplay():
    RECEIVING_FUNCTION = 'launch_fcreplay'

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

    return(function_response.data.json())


def launch_fcreplay_postprocessing():
    RECEIVING_FUNCTION = 'launch_fcreplay_postprocessing'
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

    return(function_response.data.json())


def destroy_fcreplay_postprocessing():
    RECEIVING_FUNCTION = 'destroy_fcreplay_postprocessing'

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

    return(function_response.json())


def destroy_fcreplay():
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

    return(function_response.json())

def check_if_postprocessig_running():
    RECEIVING_FUNCTION = 'fcreplay_postprocessing_running'

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

    return(function_response.json())


def check_if_running():
    RECEIVING_FUNCTION = 'fcreplay_running'

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

    return(function_response.json())
