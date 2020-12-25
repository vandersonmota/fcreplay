#!/usr/bin/env python3
from fcreplay.database import Database
import docker
import os
import shutil
import time
import uuid


class Tasker:
    def __init__(self):
        self.started_instances = {}
        self.db = Database()

    def check_for_replay(self):
        print("Looking for replay")
        player_replay = self.db.get_oldest_player_replay()
        if player_replay is not None:
            print("Found player replay")
            self.launch_fcreplay()
            return True

        replay = self.db.get_oldest_replay()
        if replay is not None:
            print("Found replay")
            self.launch_fcreplay()
            return True

        print("No replays")
        return False

    def number_of_instances(self):
        d_client = docker.from_env()
        containers = d_client.containers.list()

        instance_count = 0
        for container in containers:
            if 'fcreplay-instance-' in container.name:
                instance_count += 1

        return instance_count

    def running_instance(self, instance_hostname):
        d_client = docker.from_env()
        for i in d_client.containers.list():
            if instance_hostname in i.attrs['Config']['Hostname']:
                return True

        return False

    def remove_temp_dirs(self):
        remove_instances = []

        for docker_hostname in self.started_instances:
            if not self.running_instance(docker_hostname):
                print(f"Removing '/avi_storage_temp/{self.started_instances[docker_hostname]}'")
                shutil.rmtree(f"/avi_storage_temp/{self.started_instances[docker_hostname]}")
                remove_instances.append(docker_hostname)

        for i in remove_instances:
            del self.started_instances[i]

    def launch_fcreplay(self):
        print("Getting docker env")
        d_client = docker.from_env()

        instance_uuid = str(uuid.uuid4().hex)

        if 'FCREPLAY_NETWORK' not in os.environ:
            os.environ['FCREPLAY_NETWORK'] = 'bridge'

        # Get fcreplay network list
        networks = os.environ['FCREPLAY_NETWORK'].split(',')

        print(f"Starting new instance with temp dir: '{os.environ['AVI_TEMP_DIR']}/{instance_uuid}'")
        c_instance = d_client.containers.run(
            'fcreplay/image:latest',
            command='fcrecord',
            cpu_count=int(os.environ['CPUS']),
            detach=True,
            mem_limit=str(os.environ['MEMORY']),
            network=networks[0],
            remove=True,
            name=f"fcreplay-instance-{instance_uuid}",
            volumes={
                str(os.environ['CLIENT_SECRETS']): {'bind': '/root/.client_secrets.json', 'mode': 'ro'},
                str(os.environ['CONFIG']): {'bind': '/root/config.json', 'mode': 'ro'},
                str(os.environ['DESCRIPTION_APPEND']): {'bind': '/root/description_append.txt', 'mode': 'ro'},
                str(os.environ['IA']): {'bind': '/root/.ia', 'mode': 'ro'},
                str(os.environ['ROMS']): {'bind': '/Fightcade/emulator/fbneo/ROMs', 'mode': 'ro'},
                str(os.environ['YOUTUBE_UPLOAD_CREDENTIALS']): {'bind': '/root/.youtube-upload-credentials.json', 'mode': 'ro'},
                f"{os.environ['AVI_TEMP_DIR']}/{instance_uuid}": {'bind': '/Fightcade/emulator/fbneo/avi', 'mode': 'rw'}
            }
        )

        if len(networks) > 1:
            for n in networks[1:]:
                print(f"Adding container to network {n}")
                d_net = d_client.networks.get(n)
                d_net.connect(c_instance)

        print("Getting instance uuid")
        self.started_instances[c_instance.attrs['Config']['Hostname']] = instance_uuid

    def main(self, instances=1):
        if 'MAX_INSTANCES' in os.environ:
            instances = int(os.environ['MAX_INSTANCES'])
        while True:
            # Prune directories
            print("Removing empty temp directories")
            self.remove_temp_dirs()

            if self.number_of_instances() < instances:
                self.check_for_replay()
            else:
                print(f"Maximum number of instances ({os.environ['MAX_INSTANCES']}) reached")

            print("Sleeping for 20 seconds")
            time.sleep(20)
