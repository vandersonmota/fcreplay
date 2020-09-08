#!/usr/bin/env python
import argparse
import datetime
import i3ipc
import os
import pyautogui
import subprocess
import threading
import time

from fcreplay.config import Config
from fcreplay import logging

config = Config().config


def start_fcadefbneo(fcadefbneo_path=None, fc_challenge_id=None, game_name=None):
    logging.info(f"/usr/bin/wine {fcadefbneo_path}/fcadefbneo.exe quark:stream,{game_name},{fc_challenge_id}.2,7100 -q")
    fbneo_rc = subprocess.run(
        [
            '/usr/bin/wine',
            f'{fcadefbneo_path}/fcadefbneo.exe',
            f'quark:stream,{game_name},{fc_challenge_id}.2,7100',
            '-q'
        ]
    )


def cleanup_tasks():
    # Need to kill a bunch of processes and restart pulseaudio
    subprocess.run(['pkill', '-9', 'fcadefbneo'])
    subprocess.run(['pkill', '-9', 'wine'])
    subprocess.run(['pkill', '-9', '-f', 'system32'])
    subprocess.run(['/usr/bin/pulseaudio', '-k'])


def find_record_dialog():
    # Look for recording dialog
    i3 = i3ipc.Connection()
    root = i3.get_tree()
    for con in root:
        if isinstance(con.name, str):
            if 'Set video compression option' in con.name:
                # Found dialog. Click on ok
                mouse_x = con.rect.x + 300
                mouse_y = con.rect.y + 10
                pyautogui.moveTo(mouse_x, mouse_y)
                time.sleep(0.1)
                pyautogui.click()
                return True
    return False


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
            logging.info('First frame displayed. Looking for recording dialog')
            if find_record_dialog():
                break

        # Timeout reached, exiting
        if running_time > kill_time:
            logging.info('Match never started, exiting')
            cleanup_tasks()
            return "FailTimeout"
        time.sleep(0.1)

    begin_time = datetime.datetime.now()
    while True:
        running_time = (datetime.datetime.now() - begin_time).seconds

        # Log what minute we are on
        if (running_time % 60) == 0:
            logging.info(
                f'Minute: {int(running_time/60)} of {int(fc_time/60)}')

        # Finished recording video
        if running_time > fc_time:
            # We need to manually stop the recording. Move the mouse into the
            # fcadefbneo window, press alt, then down*6, then enter/return
            pyautogui.moveTo(700, 384)
            time.sleep('0.05')
            pyautogui.press('alt')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.press('down')
            time.sleep('0.05')
            pyautogui.keyDown('enter')
            time.sleep('0.05')
            pyautogui.keyUp('enter')
            time.sleep(2)
            cleanup_tasks()
            return "Pass"

        # Kill Timeout reached
        if running_time > (running_time + kill_time):
            return "FailTimeout"
        time.sleep(0.2)


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
