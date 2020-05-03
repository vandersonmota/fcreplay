#!/usr/bin/env python
import argparse
import datetime
import threading
import subprocess
import sys
import time
from soundmeter import meter as soundmeter

def start_ggpo(ggpo_path=None, fc_challenge=None):
    challenge_id, game_name = fc_challenge.split('@')
    ggpofba_rc = subprocess.run(
        [
            '/usr/bin/wine',
            f'{ggpo_path}/ggpofba-ng.exe',
            f'quark:stream,{game_name},{challenge_id},7001',
            '-w'
        ]
    )

def cleanup_tasks():
    # Need to kill a bunch of processes and restart pulseaudio
    subprocess.run(['pkill', '-9', 'ggpo'])
    subprocess.run(['pkill', '-9', 'wine'])
    subprocess.run(['pkill', '-9', 'obs'])
    subprocess.run(['pkill', '-9', '-f', 'system32'])
    subprocess.run(['/usr/bin/pulseaudio', '-k'])


def main(fc_challange=None, fc_time=None, kill_time=None, ggpo_path=None, fcreplay_path=None):
    # Start pulseaudio
    subprocess.run(['pulseaudio', '--daemon'])
    # Create soundmeter
    sm = soundmeter.Meter(threshold='+1000', num=1, action="exec-stop", script=f"{fcreplay_path}/obs.sh")

    # Create thread for sound meter
    obs_sm_thread = threading.Thread(target=sm.start)
    obs_sm_thread.start()
    
    # Get start time
    begin_time = datetime.datetime.now()
    
    # Start ggpofba
    print("Starting ggpofba")
    ggpo_thread = threading.Thread(target=start_ggpo, args=[ggpo_path, fc_challange])
    ggpo_thread.start()
    print("Started ggpofba")
    
    # Check for sound
    while True:
        time.sleep(1)
        running_time = (datetime.datetime.now() - begin_time).seconds
        print(f'{running_time} of {fc_time}')
        obs_running = '/usr/bin/obs' in str(subprocess.run(['ps', '-ef'], stdout=subprocess.PIPE, stderr=subprocess.PIPE))

        if  obs_sm_thread.is_alive():
            print('Soundmeter Running')
        if running_time > fc_time:
            # We have reached the end of the video. Killing processes
            if obs_running:
                cleanup_tasks()
                return True
            else:
                print("Timeout reached but obs isn't running. Something was broken")
                cleanup_tasks()
                return False
        if running_time > kill_time:
            # Check if OBS is running, if it isn't then we are broken :(
            if not obs_running:
                print("Kill timeout reached killing processes")
                cleanup_tasks()
                return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record fightcade replays")
    parser.add_argument('challenge_id', help="Fightcade challenge id")
    parser.add_argument('fc_time', help="Length of time in seconds to record")
    parser.add_argument('kill_timeout', help="How long to wait before killing processing")
    parser.add_argument('ggpo_path', help='Path to ggpo')
    parser.add_argument('fcreplay_path', help='Path to fcreplay')
    args = parser.parse_args()
    main(
        fc_challange=args.challenge_id,
        fc_time=int(args.fc_time),
        kill_time=int(args.kill_timeout),
        ggpo_path=args.ggpo_path,
        fcreplay_path=args.fcreplay_path)