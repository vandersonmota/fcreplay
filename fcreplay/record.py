#!/usr/bin/env python
import argparse
import datetime
import threading
import subprocess
import time
import logging
import os
import json

from fcreplay.config import Config

config = Config().config

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    filename=config['logfile'],
                    level=config['loglevel'],
                    datefmt='%Y-%m-%d %H:%M:%S')


def start_fcadefbneo(fcadefbneo_path=None, fc_challenge_id=None, game_name=None):
    logging.info(f"/usr/bin/wine {fcadefbneo_path}/fcadefbneo.exe quark:stream,{game_name},{fc_challenge_id}.2,7100 -w")
    fbneo_rc = subprocess.run(
        [
            '/usr/bin/wine',
            f'{fcadefbneo_path}/fcadefbneo.exe',
            f'quark:stream,{game_name},{fc_challenge_id}.2,7100',
            '-w'
        ]
    )


def start_obs():
    obs_rc = subprocess.run(
        [
            '/usr/bin/obs',
            '--minimize-to-tray',
            '--startrecording'
        ]
    )


def cleanup_tasks():
    # Need to kill a bunch of processes and restart pulseaudio
    subprocess.run(['pkill', '-9', 'fcadefbneo'])
    subprocess.run(['pkill', '-9', 'wine'])
    subprocess.run(['pkill', '-9', 'obs'])
    subprocess.run(['pkill', '-9', '-f', 'system32'])
    subprocess.run(['/usr/bin/pulseaudio', '-k'])


def main(fc_challange_id=None, fc_time=None, kill_time=None, fcadefbneo_path=None, fcreplay_path=None, game_name=None):
    logging.info('Starting pulseaudio')
    subprocess.run(['pulseaudio', '--daemon'])

    # Get start time
    begin_time = datetime.datetime.now()

    # Make sure 'started.inf' is missing
    if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
        os.remove(f"{fcadefbneo_path}/fightcade/started.inf")

    # Start ggpofbneo
    logging.info("Starting fcadefbneo thread")
    logging.debug(f"Arguments: {fcadefbneo_path}, {fc_challange_id}, {game_name}")

    ggpo_thread = threading.Thread(target=start_fcadefbneo, args=[
                                   fcadefbneo_path, fc_challange_id, game_name])
    ggpo_thread.start()
    logging.info("Started ggpofbneo")

    # Check to see if fcadefbneo has started playing
    logging.info('Checking to see if replay has started')
    while True:
        running_time = (datetime.datetime.now() - begin_time).seconds

        if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
            logging.info('First frame displayed. Starting OBS')
            break

        # Check if file exiss
        if running_time > kill_time:
            logging.info('Match never started, exiting')
            cleanup_tasks()
            return "FailTimeout"

    logging.info("Starting obs")
    obs_thread = threading.Thread(target=start_obs)
    obs_thread.start()
    logging.info("Started obs")

    begin_time = datetime.datetime.now()
    while True:
        running_time = (datetime.datetime.now() - begin_time).seconds
        obs_running = '/usr/bin/obs' in str(subprocess.run(
            ['ps', '-ef'], stdout=subprocess.PIPE, stderr=subprocess.PIPE))

        if (running_time % 60) == 0:
            logging.info(
                f'Minute: {int(running_time/60)} of {int(fc_time/60)}')

        if running_time > fc_time:
            # We have reached the end of the video. Killing processes
            if obs_running:
                cleanup_tasks()
                return "Pass"
            else:
                logging.error(
                    "Timeout reached but obs isn't running. Something was broken")
                cleanup_tasks()
                return "FailNoOBS"
        if running_time > kill_time:
            # Check if OBS is running, if it isn't then we are broken :(
            if not obs_running:
                logging.error("Kill timeout reached killing processes")
                cleanup_tasks()
                return "FailTimeout"
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record fightcade replays")
    parser.add_argument('fc_challenge_id', help="Fightcade challenge id")
    parser.add_argument('fc_time', help="Length of time in seconds to record")
    parser.add_argument(
        'kill_timeout', help="How long to wait before killing processing")
    parser.add_argument('fcadefbneo_path', help='Path to ggpo')
    parser.add_argument('fcreplay_path', help='Path to fcreplay')
    parser.add_argument('game_name', help='Game name (Eg: sfiii3nr1)')
    args = parser.parse_args()
    main(
        fc_challange_id=args.fc_challenge_id,
        fc_time=int(args.fc_time),
        kill_time=int(args.kill_timeout),
        fcadefbneo_path=args.fcadefbneo_path,
        fcreplay_path=args.fcreplay_path,
        game_name=args.game_name)
