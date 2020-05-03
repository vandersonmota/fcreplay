#!/usr/bin/env python
import daemon
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
    timeout = False
    
    # Start ggpofba
    print("Starting ggpofba")
    ggpo_thread = threading.Thread(target=start_ggpo, args=[ggpo_path, fc_challange])
    ggpo_thread.start()
    print("Started ggpofba")
    
    # Check for sound
    while not timeout:
        time.sleep(1)
        running_time = (datetime.datetime.now() - begin_time).seconds
        print(f'{running_time} of {fc_time}')
        check_rc = subprocess.run(['pgrep', 'obs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if  obs_sm_thread.is_alive():
            print('Soundmeter Running')
        if running_time > fc_time:
            # We have reached the end of the video. Killing processes
            if check_rc.returncode == 0:
                cleanup_tasks()
                timeout=True
                return True
            else:
                print("Timeout reached but obs isn't running. Something was broken")
                return False
        if running_time > kill_time:
            # Check if OBS is running, if it isn't then we are broken :(
            if check_rc.returncode == 0:
                print("Timeout reached killing processes")
                cleanup_tasks()
                timeout = True
                return False
            else:
                print("Timeout reached buy obs isn't running. Something is broken")
                return False


if __name__ == "__main__":
    main()