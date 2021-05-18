#!/usr/bin/env python
import datetime
import i3ipc
import logging
import os
import subprocess
import threading
import time
import collections

from fcreplay.config import Config
from fcreplay.overlay_detection import OverlayDetection

if 'DISPLAY' in os.environ:
    import pyautogui

log = logging.getLogger('fcreplay')


class Record:
    def __init__(self):
        self.config = Config().config

    def start_fcadefbneo(self, fcadefbneo_path=None, fc_challenge_id=None, game_name=None):
        log.info(f"/usr/bin/wine {fcadefbneo_path}/fcadefbneo.exe quark:stream,{game_name},{fc_challenge_id}.2,7100 -q")
        running_env = os.environ.copy()
        running_env['WINEDLLOVERRIDES'] = "avifil32=n,b"
        subprocess.run(
            [
                '/usr/bin/wine',
                f'{fcadefbneo_path}/fcadefbneo.exe',
                f'quark:stream,{game_name},{fc_challenge_id}.2,7100',
                'lua\\framecount.lua',
                '-q'
            ],
            env=running_env
        )

    def cleanup_tasks(self):
        # Need to kill a bunch of processes and restart pulseaudio
        log.info("Killing fcadefbneo, wine, system32 and pulseaudio")
        subprocess.run(['pkill', '-9', 'fcadefbneo'])
        subprocess.run(['pkill', '-9', 'wine'])
        subprocess.run(['pkill', '-9', '-f', 'system32'])
        subprocess.run(['/usr/bin/pulseaudio', '-k'])
        log.info("Tasks killed")

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

    def get_running_time(self, fcadefbneo_path):
        retry = 5
        while retry >= 1:
            with open(f"{fcadefbneo_path}/lua/framecount.txt", 'r') as f:
                running_time = f.readline().strip()

            try:
                running_time = int(running_time)
                break
            except Exception as e:
                retry -= 1
                if retry <= 0:
                    log.error(f"Running time is not an integer. Running time: {running_time}, exception: {e}")
                    raise TypeError
                time.sleep(0.1)
                continue

        return running_time

    def main(self, fc_challange_id=None, fc_time=None, kill_time=None, fcadefbneo_path=None, game_name=None):
        log.info('Starting pulseaudio')
        subprocess.Popen(
            ['pulseaudio', '-v', '--exit-idle-time=-1'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Get start time
        self.begin_time = datetime.datetime.now()

        # Make sure 'started.inf' is missing
        if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
            os.remove(f"{fcadefbneo_path}/fightcade/started.inf")

        # Start ggpofbneo
        log.info("Starting fcadefbneo thread")
        log.debug(f"Arguments: {fcadefbneo_path}, {fc_challange_id}, {game_name}")

        ggpo_thread = threading.Thread(target=self.start_fcadefbneo, args=[
                                       fcadefbneo_path, fc_challange_id, game_name])
        ggpo_thread.start()
        log.info("Started ggpofbneo")

        # This requires the 'fightcade' directory exists inside the fbneo directory
        # if it doesn't exists, then this will fail
        overlay_detection = OverlayDetection()
        overlay_detection.start()

        # Check to see if fcadefbneo has started playing
        log.info('Checking to see if replay has started')
        while True:
            running_time = (datetime.datetime.now() - self.begin_time).seconds

            if os.path.exists(f"{fcadefbneo_path}/fightcade/started.inf"):
                log.info('First frame displayed. Looking for recording dialog')
                if self.find_record_dialog():
                    break

            # Timeout reached, exiting
            if running_time > kill_time:
                log.info('Match never started, exiting')
                self.cleanup_tasks()
                return "FailTimeout"
            time.sleep(0.1)

        self.begin_time = datetime.datetime.now()
        minute_count = -1

        # Initalise the framecount. Do this by setting up a 'queue' with a
        # maximum length of 10. Then append each time to it. The 'last'
        # element of the queue is the current time.
        running_time = collections.deque(maxlen=10)

        # Append two elements so that the queue isn't empty
        running_time.append(-1)
        running_time.append(0)

        while True:
            # Add the current running time to the queue
            running_time.append(self.get_running_time(fcadefbneo_path))

            # Log what minute we are on
            if (running_time[-1] % 60) == 0 and int(running_time[-1] / 60) != minute_count:
                log.info(f'Minute: {int(running_time[-1]/60)} of {int(fc_time/60)}')
                minute_count = int(running_time[-1] / 60)

            # Finished recording video if all elements of the queue are the same
            if len(set(running_time)) == 1:
                overlay_detection.stop()

                log.info("Stopping recording")

                # We need to manually stop the recording. Move the mouse into the
                # fcadefbneo window, press alt, then down*7, then enter/return.
                pyautogui.moveTo(700, 384)
                time.sleep(0.05)
                pyautogui.press('alt')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.press('down')
                time.sleep(0.05)
                pyautogui.keyDown('enter')
                time.sleep(0.05)
                pyautogui.keyUp('enter')

                # Sleep for 2 seconds here in case there is some sort of delay writing file
                time.sleep(2)
                self.cleanup_tasks()

                log.info("Recording stopped")
                return "Pass"

            # Kill Timeout reached
            if running_time[-1] > (running_time[-1] + kill_time):
                return "FailTimeout"
            time.sleep(0.2)
