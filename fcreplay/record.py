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
from fcreplay.logging import Logging


class Record:
    def __init__(self):
        self.config = Config().config

    def start_fcadefbneo(self, fcadefbneo_path=None, fc_challenge_id=None, game_name=None):
        Logging().info(f"/usr/bin/wine {fcadefbneo_path}/fcadefbneo.exe quark:stream,{game_name},{fc_challenge_id}.2,7100 -q")
        fbneo_rc = subprocess.run(
            [
                '/usr/bin/wine',
                f'{fcadefbneo_path}/fcadefbneo.exe',
                f'quark:stream,{game_name},{fc_challenge_id}.2,7100',
                '-q'
            ]
        )

    def cleanup_tasks(self):
        # Need to kill a bunch of processes and restart pulseaudio
        subprocess.run(['pkill', '-9', 'fcadefbneo'])
        subprocess.run(['pkill', '-9', 'wine'])
        subprocess.run(['pkill', '-9', '-f', 'system32'])
        subprocess.run(['/usr/bin/pulseaudio', '-k'])

    def find_record_dialog(self):
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

    def main(self, fc_challange_id=None, fc_time=None, kill_time=None, fcadefbneo_path=None, fcreplay_path=None, game_name=None):
        Logging().info('Starting pulseaudio')
        subprocess.run(['pulseaudio', '--daemon'])

        # Get start time
        begin_time = datetime.datetime.now()

        # Make sure 'started.inf' is missing
        if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
            os.remove(f"{fcadefbneo_path}/fightcade/started.inf")

        # Start ggpofbneo
        Logging().info("Starting fcadefbneo thread")
        Logging().debug(f"Arguments: {fcadefbneo_path}, {fc_challange_id}, {game_name}")

        ggpo_thread = threading.Thread(target=self.start_fcadefbneo, args=[
                                       fcadefbneo_path, fc_challange_id, game_name])
        ggpo_thread.start()
        Logging().info("Started ggpofbneo")

        # Check to see if fcadefbneo has started playing
        Logging().info('Checking to see if replay has started')
        while True:
            running_time = (datetime.datetime.now() - begin_time).seconds

            if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
                Logging().info('First frame displayed. Looking for recording dialog')
                if self.find_record_dialog():
                    break

            # Timeout reached, exiting
            if running_time > kill_time:
                Logging().info('Match never started, exiting')
                self.cleanup_tasks()
                return "FailTimeout"
            time.sleep(0.1)

        begin_time = datetime.datetime.now()
        minute_count = -1

        while True:
            running_time = (datetime.datetime.now() - begin_time).seconds

            # Log what minute we are on
            if (running_time % 60) == 0 and int(running_time / 60) != minute_count:
                Logging().info(f'Minute: {int(running_time/60)} of {int(fc_time/60)}')
                minute_count = int(running_time / 60)

            # Finished recording video
            if running_time > fc_time:
                # We need to manually stop the recording. Move the mouse into the
                # fcadefbneo window, press alt, then down*7, then enter/return.
                # I'm not sure why, but the 'duration' time being reported is
                # actually too short. So we extend it by 4 seconds.
                pyautogui.moveTo(700, 384)
                time.sleep(0.1)
                pyautogui.press('alt')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('down')

                # Since the duration is too short, we extend it by 4 seconds here
                time.sleep(4)
                pyautogui.keyDown('enter')
                time.sleep(0.1)
                pyautogui.keyUp('enter')

                # Sleep for 2 seconds here in case there is some sort of delay writing file
                time.sleep(2)
                self.cleanup_tasks()
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
    Record.main(
        fc_challange_id=args.fc_challenge_id,
        fc_time=int(args.fc_time),
        kill_time=int(args.kill_timeout),
        fcadefbneo_path=args.fcadefbneo_path,
        fcreplay_path=args.fcreplay_path,
        game_name=args.game_name)
