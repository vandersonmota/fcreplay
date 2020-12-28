# This file needs to be in the root of the repository for google cloud
# functions to use the main.py file and be able to import the fcreplay files
import json
import os
import time
import requests

from fcreplay.logging import Logging
from fcreplay.getreplay import Getreplay
from fcreplay.database import Database
from fcreplay.config import Config

config = Config().config
db = Database()


def video_status(request):
    Logging().info("Check status for completed videos")

    # Get all replays that are completed, where video_processed is false
    to_check = db.get_unprocessed_replays()

    for replay in to_check:
        # Check if replay has embeded video link. Easy way to do this is to check
        # if a thumbnail is created
        Logging().info(f"Checking: {replay.id}")
        r = requests.get(f"https://archive.org/download/{replay.id.replace('@', '-')}/__ia_thumb.jpg")

        Logging().info(f"ID: {replay.id}, Status: {r.status_code}")
        if r.status_code == 200:
            db.set_replay_processed(challenge_id=replay.id)

    return json.dumps({"status": True})


def wait_for_operation(compute, project, zone, operation):
    Logging().info('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            Logging().info("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        time.sleep(1)


def check_environment(request):
    Logging().info(os.environ)


def get_top_weekly(request):
    Logging().info(Getreplay().get_top_weekly())
