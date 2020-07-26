import googleapiclient.discovery
from google.cloud import storage
import json
import time
from sqlalchemy import Column, String, Integer, DateTime, Boolean, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

Base = declarative_base()
engine = create_engine(config['sql_baseurl'], echo=False)
Session = sessionmaker(bind=engine)


class Replays(Base):
    __tablename__ = 'replays'

    id = Column(String, primary_key=True)
    p1_loc = Column(String)
    p2_loc = Column(String)
    p1 = Column(String)
    p2 = Column(String)
    date_replay = Column(DateTime)
    length = Column(Integer)
    created = Column(Boolean)
    failed = Column(Boolean)
    status = Column(String)
    date_added = Column(DateTime)
    player_requested = Column(Boolean)


def check_for_replay(request):
    print("Looking for replay")
    session = Session()
    player_replay = session.query(
        Replays
    ).filter_by(
        player_requested = True
    ).filter_by(
        failed = False
    ).filter_by(
        created = False
    ).filter_by(
        status = "ADDED"
    ).order_by(
        Replays.date_added.asc()
    ).first()

    if player_replay is not None:
        session.close()
        print("Found player replay")
        launch_fcreplay(None)
        return json.dumps({"status": True})

    replay = session.query(
        Replays
    ).filter_by(
        failed=False
    ).filter_by(
        created=False
    ).filter_by(
        status = "ADDED"
    ).order_by(
        func.random()
    ).first()

    if replay is not None:
        session.close()
        print("Found replay")
        launch_fcreplay(None)
        return json.dumps({"status": True})

    print("No replays")
    return json.dumps({"status": False})


def check_for_postprocessing(request):
    print("Check if instance is running")
    running = json.loads(fcreplay_postprocessing_running(None))

    # Post processing is running
    if running['status']:
        print("Instance is running")
        return json.dumps({'status': False})

    running = json.loads(fcreplay_running(None))
    if running['status']:
        print("Instance is running")
        return json.dumps({"status": False})


    # Look for replay to encode, either a db call, or just look for items in the bucket.
    # db call will be more accurate. But looking for items should be easier. Doing that...
    # This will totally bite me in the ass
    print("Looking for replays to process in google cloud storage")
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(config['gcloud_bucket'])
    for blob in blobs:
        print(f"found {blob.name}")
        # Since we returned something, we know we should be recording
        status = json.loads(launch_fcreplay_postprocessing(None))

        # If status is false, then something bad happened
        if not status['status']:
            print("Launch instance failed")
            return json.dumps({'status': False})
        else:
            print("Finished")
            return json.dumps({'status': True})

    # No replays to postprocess. Exiting
    print("No replays to process")
    return json.dumps({'status': True})


def fcreplay_running(request):
    print("Checking if instance running")
    instance_name = "fcreplay-image-1"
    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().list(
        project=config['gcloud_project'],
        zone=config['gcloud_zone']).execute()

    for i in result['items']:
        if instance_name in i['name']:
            print("Instance running")
            return(json.dumps({'status': True}))

    print("Instance running")
    return(json.dumps({'status': False}))


def fcreplay_postprocessing_running(request):
    print("Checking if instance running")
    instance_name = "fcreplay-postprocessing-1"

    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().list(
        project=config['gcloud_project'],
        zone=config['gcloud_zone']).execute()

    for i in result['items']:
        if instance_name in i['name']:
            print("Instance running")
            return(json.dumps({'status': True}))

    print("No instance running")
    return(json.dumps({'status': False}))


def launch_fcreplay_postprocessing(request):
    instance_name = "fcreplay-postprocessing-1"

    print("Checking if instance running")
    running = json.loads(fcreplay_postprocessing_running(None))
    if running['status']:
        return(json.dumps({"status": False}))

    running = json.loads(fcreplay_running(None))
    if running['status']:
        return(json.dumps({"status": False}))


    print("Launching fcreplay_postprocessing")
    compute = googleapiclient.discovery.build('compute', 'v1')
    instance_body = {
        'name': instance_name,
        'machineType': f"zones/{config['gcloud_zone']}/machineTypes/custom-2-2048",
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


def launch_fcreplay(request):
    print("Running: launch_fcreplay")
    instance_name = "fcreplay-image-1"

    # Check if instance is running
    running = json.loads(fcreplay_running(None))
    if running['status']:
        return(json.dumps({"status": False}))

    running = json.loads(fcreplay_postprocessing_running(None))
    if running['status']:
        return(json.dumps({"status": False}))

    # Check if there is already an item in google storage:
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(config['gcloud_bucket'])
    for blob in blobs:
        print(f"found {blob.name}, not running")
        return(json.dumps({"status": False}))
    print("No post processing videos found")

    # Starting compute engine
    compute = googleapiclient.discovery.build('compute', 'v1')

    instance_body = {
        'name': instance_name,
        'machineType': f"zones/{config['gcloud_zone']}/machineTypes/custom-6-5632",
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


def destroy_fcreplay(request):
    print("Deleting fcreaplay-image-1 compute instance")
    instance_name = "fcreplay-image-1"

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


def destroy_fcreplay_postprocessing(request):
    print("Deleting fcreplay-postprocessing-1 compute instance")
    instance_name = "fcreplay-postprocessing-1"

    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().stop(
        project=config['gcloud_project'],
        zone=config['gcloud_zone'],
        instance=instance_name).execute()

    wait_for_operation(
        compute,config['gcloud_project'],
        config['gcloud_zone'],
        result['name'])

    destroy_vm(
        compute,
        config['gcloud_project'],
        config['gcloud_zone'],
        instance_name)
    return json.dumps({"status": True})


def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        time.sleep(1)


def destroy_vm(compute, project, zone, instance_name):
    print(f"Destroying: {instance_name}")
    result = compute.instances().delete(project=project, zone=zone, instance=instance_name).execute()
    wait_for_operation(compute, project, zone, result['name'])
