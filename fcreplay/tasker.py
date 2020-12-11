#!/usr/bin/env python3
from fcreplay.database import Database
import docker
import os
import time
import uuid


class Tasker:
    def __init__(self):
        self.db = Database()

    def check_for_replay(self):
        print("Looking for replay")
        player_replay = self.db.get_oldest_player_replay()
        if player_replay is not None:
            print("Found player replay")
            self.launch_fcreplay()

        replay = self.db.get_oldest_replay()
        if replay is not None:
            print("Found replay")
            self.launch_fcreplay()

        print("No replays")

    def number_of_instances(self):
        d_client = docker.from_env()
        containers = d_client.containers.list()

        instance_count = 0
        for container in containers:
            if 'fcreplay-instance-' in container.name:
                instance_count += 1

        return instance_count

    def launch_fcreplay(self):
        d_client = docker.from_env()
        d_client.containers.run(
            'fcreplay/image:latest',
            command='record',
            cpu_count=os.environ['CPUS'],
            detach=True,
            mem_limit=os.environ['MEMORY'],
            remove=True,
            name=f"fcreplay-instance-{str(uuid.uuid4().hex)}",
            volumes={
                os.environ['CLIENT_SECRETS']: {'bind': '/root/.client_secrets', 'mode': 'ro'},
                os.environ['CONFIG']: {'bind': '/root/config.json', 'mode': 'ro'},
                os.environ['DESCRIPTION_APPEND']: {'bind': '/root/description_append.txt', 'mode': 'ro'},
                os.environ['IA']: {'bind': '/root/.ia', 'mode': 'ro'},
                os.environ['ROMS']: {'bind': '/root/Fightcade/emulator/fbneo/ROMs', 'mode': 'ro'},
                os.environ['YOUTUBE_UPLOAD_CREDENTIALS']: {'bind': '/root/.youtube-upload-credentials.json', 'mode': 'ro'}
            }
        )

    def main(self):
        if self.number_of_instances < int(os.environ['MAX_INSTANCES']):
            self.check_for_replay()
        else:
            print(f"Maximum number of instances ({os.environ['MAX_INSTANCES']}) reached")
        time.sleep(120)


def console():
    Tasker().main()


if __name__ == '__main__':
    console()
