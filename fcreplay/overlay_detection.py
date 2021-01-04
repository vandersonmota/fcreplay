from fcreplay.config import Config
import logging
import datetime
import os
import pickle
import threading
import glob
import time

log = logging.getLogger('fcreplay')


class OverlayDetection:
    def __init__(self):
        log.debug('Creating character detection instance')
        self.config = Config().config
        self.events = [{'start_time': datetime.datetime.now()}]
        self.finished = False
        self.overlay_pickle_path = f"{self.config['fcadefbneo_path']}/avi/overlay.pickle"

    def start(self):
        log.info('Starting character detection')
        self.overlay_thread = threading.Thread(target=self.watch_files)
        self.overlay_thread.start()

    def stop(self):
        log.info('Stopping character detection')
        self.finished = True
        self.overlay_thread.join()

        with open(self.overlay_pickle_path, 'wb') as f:
            pickle.dump(self.events, f, pickle.HIGHEST_PROTOCOL)

    def watch_files(self):
        monitor = {}

        log.info("Starting to watch files in fightacde directory")
        while True:
            if self.finished:
                break

            for file_path in glob.glob(f"{self.config['fcadefbneo_path']}/fightcade/*"):
                base_name = os.path.basename(file_path)
                overlay_type = os.path.splitext(base_name)[0]

                if overlay_type in ['p1country', 'p2country']:
                    continue

                overlay_data = self.get_file_data(file_path)

                if overlay_type not in monitor:
                    monitor[overlay_type] = overlay_data
                    self.add_event(overlay_type, overlay_data)
                else:
                    if monitor[overlay_type] != overlay_data:
                        monitor[overlay_type] = overlay_data
                        self.add_event(overlay_type, overlay_data)

            time.sleep(0.5)

    def get_file_data(self, file_path: str):
        with open(file_path, 'rb') as f:
            return f.read().decode('ascii').strip()

    def add_event(self, overlay_type: str, overlay_data: str):
        log.info(f"Adding overlay event '{overlay_type}': '{overlay_data}'")
        self.events.append(
            {
                'date': datetime.datetime.now(),
                'overlay_type': overlay_type,
                'overlay_data': overlay_data
            }
        )
