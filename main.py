# This file needs to be in the root of the repository for google cloud
# functions to use the main.py file and be able to import the fcreplay files
import googleapiclient.discovery
import json
import os
import time
import requests
import uuid

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


def check_for_replay(request):
    destroyed_instance = json.loads(destroy_stopped_instances(True))['status']

    if destroyed_instance:
        return json.dumps({'status': False})

    Logging().info("Looking for replay")
    player_replay = db.get_oldest_player_replay()
    if player_replay is not None:
        Logging().info("Found player replay")
        launch_fcreplay(None)
        return json.dumps({"status": True})

    replay = db.get_oldest_replay()
    if replay is not None:
        Logging().info("Found replay")
        launch_fcreplay(None)
        return json.dumps({"status": True})

    Logging().info("No replays")
    return json.dumps({"status": False})


def destroy_stopped_instances(request):
    Logging().info("Checking if there are instances stopped")
    instance_name = "fcreplay-image-"
    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().list(
        project=config['gcloud_project'],
        zone=config['gcloud_zone']).execute()

    # Destroy any stopped instances and exit
    for i in result['items']:
        if instance_name in i['name']:
            # Destroy stopped instances
            if i['status'] == "TERMINATED" and config['gcloud_destroy_when_stopped']:
                Logging().info(f"Destoying {i['name']}")
                destroy_fcreplay_instance(instance_name=i['name'])
                return(json.dumps({'status': True}))

    return(json.dumps({'status': False}))


def fcreplay_running(request):
    Logging().info("Checking if there are instances running")
    instance_name = "fcreplay-image-"
    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().list(
        project=config['gcloud_project'],
        zone=config['gcloud_zone']).execute()

    instance_count = 0
    for i in result['items']:
        if instance_name in i['name']:
            # Count number of running instances
            if i['status'] == "RUNNING":
                Logging().info(f"{i['name']} instance running adding to count")
                instance_count += 1

            # Count number of 'other' instances
            else:
                Logging().info(f"{instance_name} status is {i['status']}, adding to count")
                instance_count += 1

    if instance_count >= config['gcloud_instance_max']:
        Logging().info(f"There are {instance_count}/{config['gcloud_instance_max']} running")
        return(json.dumps({'status': True}))

    Logging().info(f"There are {instance_count}/{config['gcloud_instance_max']} running")
    return(json.dumps({'status': False}))


def launch_fcreplay(request):
    Logging().info("Running: launch_fcreplay")

    # Check if instance is running
    running = json.loads(fcreplay_running(None))
    if running['status']:
        return(json.dumps({"status": False}))

    # Generate instance name uuid
    instance_name = 'fcreplay-image-' + str(uuid.uuid1())

    # Starting compute engine
    compute = googleapiclient.discovery.build('compute', 'v1')

    instance_body = {
        'name': instance_name,
        'machineType': f"zones/{config['gcloud_zone']}/machineTypes/custom-4-4096",
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [
                    {
                        "type": "ONE_TO_ONE_NAT",
                        "name": "External NAT",
                        "setPublicPtr": False,
                        "networkTier": "STANDARD"
                    }
                ]
            }
        ],
        'disks': [
            {
                "boot": True,
                "initializeParams": {
                    "sourceImage": "global/images/fcreplay-image"
                },
                "autoDelete": True
            }
        ],
        'scheduling': {
            'preemptible': True
        },
        "serviceAccounts": [
            {
                "email": config['gcloud_compute_service_account'],
                "scopes": [
                    "https://www.googleapis.com/auth/cloud-platform"
                ]
            }
        ]
    }

    result = compute.instances().insert(
        project=config['gcloud_project'],
        zone=config['gcloud_zone'],
        body=instance_body).execute()

    wait_for_operation(
        compute,
        config['gcloud_project'],
        config['gcloud_zone'],
        result['name'])
    return(json.dumps({"status": True}))


def destroy_fcreplay_instance(request=None, instance_name=None):
    if request is not None:
        request_json = request.get_json(silent=True)
    else:
        request_json = None

    Logging().info(f"request_json: {request_json}")
    Logging().info(f"instance_name: {instance_name}")
    if (request_json is not None and 'instance_name' in request_json) or instance_name is not None:
        if request_json is not None:
            Logging().info("Setting instance name from json")
            instance_name = request_json['instance_name']

        if 'fcreplay-image-' not in instance_name:
            Logging().info(f"Not deleting {instance_name}")
            return json.dumps({"status": False})

        Logging().info(f"Deleting {instance_name} compute instance")

        compute = googleapiclient.discovery.build('compute', 'v1')
        result = compute.instances().stop(
            project=config['gcloud_project'],
            zone=config['gcloud_zone'],
            instance=instance_name).execute()

        wait_for_operation(
            compute,
            config['gcloud_project'],
            config['gcloud_zone'],
            result['name'])

        destroy_vm(
            compute,
            config['gcloud_project'],
            config['gcloud_zone'],
            instance_name)
        return json.dumps({"status": True})

    Logging().info('No instance_name found')
    return json.dumps({"status": False})


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


def destroy_vm(compute, project, zone, instance_name):
    Logging().info(f"Destroying: {instance_name}")
    result = compute.instances().delete(project=project, zone=zone, instance=instance_name).execute()
    wait_for_operation(compute, project, zone, result['name'])


def check_environment(request):
    Logging().info(os.environ)


def get_top_weekly(request):
    Logging().info(Getreplay().get_top_weekly())
