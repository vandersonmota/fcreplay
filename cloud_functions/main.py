import datetime
import googleapiclient.discovery
import json
import os
import time
import requests
from sqlalchemy import Column, String, Integer, DateTime, Boolean, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

if 'FCREPLAY_CONFIG' in os.environ:
    with open(os.environ['FCREPLAY_CONFIG'], 'r') as json_data_file:
        config = json.load(json_data_file)
else:
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
    video_processed = Column(Boolean)


def video_status(request):
    print("Check status for completed videos")
    session = Session()

    # Get all replays that are completed, where video_processed is false
    to_check = session.query(
        Replays
    ).filter_by(
        failed = False
    ).filter_by(
        created = True
    ).filter_by(
        video_processed = False
    ).all()

    for replay in to_check:
        # Check if replay has embeded video link. Easy way to do this is to check
        # if a thumbnail is created
        print(f"Checking: {replay.id}")
        r = requests.get(f"https://archive.org/download/{replay.id.replace('@', '-')}/__ia_thumb.jpg")

        print(f"ID: {replay.id}, Status: {r.status_code}")
        if r.status_code == 200:
            session_loop = Session()
            session_loop.query(Replays).filter_by(id=replay.id).update({'video_processed': True, "date_added": datetime.datetime.now()})
            session_loop.commit()

    return json.dumps({"status": True})


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


def fcreplay_running(request):
    print("Checking if instance running")
    instance_name = "fcreplay-image-1"
    compute = googleapiclient.discovery.build('compute', 'v1')
    result = compute.instances().list(
        project=config['gcloud_project'],
        zone=config['gcloud_zone']).execute()

    for i in result['items']:
        if instance_name in i['name']:
            if i['status'] == "TERMINATED" and config['gcloud_destroy_when_stopped']:
                print(f"Destoying {instance_name}")
                destroy_fcreplay(True)
                return(json.dumps({'status': True}))
            elif i['status'] == "RUNNING":
                print(f"{instance_name} instance running")
                return(json.dumps({'status': True}))
            else:
                print(f"{instance_name} status is {i['status']}")
                return(json.dumps({'status': False}))

    print(f"{instance_name} instance not running")
    return(json.dumps({'status': False}))


def launch_fcreplay(request):
    print("Running: launch_fcreplay")
    instance_name = "fcreplay-image-1"

    # Check if instance is running
    running = json.loads(fcreplay_running(None))
    if running['status']:
        return(json.dumps({"status": False}))

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
