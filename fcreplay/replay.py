from fcreplay.config import Config
from fcreplay.record import Record
from fcreplay.thumbnail import Thumbnail
from fcreplay.updatethumbnail import UpdateThumbnail

import datetime
import glob
import json
import logging
import os
import pkg_resources
import re
import subprocess
import time
import sys
from dataclasses import dataclass
from getreplay import Getreplay


log = logging.getLogger('fcreplay')

class Replay:
    """Class for FightCade replays."""

    def __init__(self, url):
        """Initaliser for Replay class."""
        self.config = Config()
        self.replay = Getreplay().get_replay(url)
        self.description_text = ""
        self.detected_characters = []

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            self.supported_games = json.load(f)

        # On replay start create a status file in /tmp - Legacy?
        with open('/tmp/fcreplay_status', 'w') as f:
            f.write(f"{self.replay.id} STARTED")

    def handle_fail(self, e: Exception):
        """Handle failures."""
        log.exception(e)

        # Hacky as hell, but ensures everything gets killed
        if self.config.kill_all:
            subprocess.run(['pkill', '-9', 'fcadefbneo'])
            subprocess.run(['pkill', '-9', 'wine'])
            subprocess.run(['pkill', '-9', '-f', 'system32'])
            subprocess.run(['/usr/bin/pulseaudio', '-k'])
            subprocess.run(['pkill', '-9', 'tail'])
            subprocess.run(['killall5'])
            subprocess.run(['pkill', '-9', 'sh'])
        time.sleep(5)
        with open('/tmp/fcreplay_failed', 'w') as f:
            f.write("FAILED")

        sys.exit(1)

    def record(self):
        """Start recording a replay."""
        log.info(
            f"Starting capture with {self.replay.id} and {self.replay.length}")
        time_min = int(self.replay.length / 60)
        log.info(f"Capture will take {time_min} minutes")

        # Star a recording store recording status
        log.debug(
            f"""Starting record.main with argumens:
            fc_challenge_id={self.replay.id},
            fc_time={self.replay.length},
            kill_time={self.config.record_timeout},
            fcadefbneo_path={self.config.fcadefbneo_path},
            game_name={self.replay.game}""")

        Record().main(
            challenge_id=self.replay.id,
            replay_length_seconds=self.replay.length,
            kill_time=self.config.record_timeout,
            game_id=self.replay.game
        )

        log.info("Capture finished")

        return True

    def sort_files(self, avi_files_list: list):
        """Sort files.

        This sorts the avi files FBNeo generates. FBneo generates files that
        have a hexadecimal suffix added to them (08, 09, 0A, 0B...).

        Args:
            avi_files_list (list): List of avi files to sort

        Returns:
            list: Returns a sorted list of avi files
        """
        log.info("Sorting files")

        if len(avi_files_list) > 1:
            avi_dict = {}
            for i in avi_files_list:
                m = re.search('(.*)_([0-9a-fA-F]+).avi', i)
                avi_dict[i] = int(m.group(2), 16)
            sorted_avi_files_list = []
            for i in sorted(avi_dict.items(), key=lambda x: x[1]):
                sorted_avi_files_list.append(i[0])
            avi_files = [f"{self.config.fcadefbneo_path}/avi/" + i for i in sorted_avi_files_list]
        else:
            avi_files = [
                f"{self.config.fcadefbneo_path}/avi/" + avi_files_list[0]]

        return avi_files

    def get_resolution(self, aspect_ratio: list, video_resolution: list) -> list:
        """Return the correct resoltion for memcoder.

        Args:
            aspect_ratio (list): Supplied aspect ratio as list, eg: [4, 3]
            video_resolution (list): Supplied video resolution as list, eg: [1280, 720]

        Returns:
            list: Returns list containing the encoding resultion for memcoder, eg: [960, 720, 1280, 720]
        """
        # Find resolution
        multiplier = aspect_ratio[0] / aspect_ratio[1]
        desired_resolution = []

        # If the resolution is horozontal, use a horizontal HD resolution, otherwise use a vertical
        # resolution video
        if aspect_ratio[0] >= aspect_ratio[1]:
            desired_resolution = [video_resolution[1] * multiplier, video_resolution[1]]

            # Super wide games need to be done differently, looking at you darius...
            if desired_resolution[0] > video_resolution[0]:
                desired_resolution = [video_resolution[0],
                                      video_resolution[0] / multiplier]

        else:
            # Swap the resolutions, make the video verticle
            video_resolution = [video_resolution[1], video_resolution[0]]
            desired_resolution = [video_resolution[0] * multiplier, video_resolution[1]]

        desired_resolution.append(video_resolution[0])
        desired_resolution.append(video_resolution[1])

        desired_resolution = [int(a) for a in desired_resolution]
        return desired_resolution

    def encode(self):
        """Encode avi files.

        Raises:
            e: subprocess.CalledProcessError
        """
        log.info("Encoding lossless file")

        avi_files_list_glob = glob.glob(
            f"{self.config.fcadefbneo_path}/avi/*.avi")
        avi_files_list = []

        for f in avi_files_list_glob:
            avi_files_list.append(os.path.basename(f))

        log.info(f"List of files is: {avi_files_list}")

        # Sort files
        avi_files = self.sort_files(avi_files_list)

        # Get the correct screen resolution settings
        resolution = self.config.resolution
        aspect_ratio = self.supported_games[self.replay.game]['aspect_ratio']
        dsize = '/'.join(str(x) for x in aspect_ratio)

        r = self.get_resolution(aspect_ratio, resolution)

        # I can't stress enough how much you should not try and mess with the encoding settings!
        # 1. ffmpeg will not handle files generated by fbneo
        # 2. The files that fbneo generates need to be transcoded before they are encoded to h264 (h265 doesn't work well with archive.org)
        mencoder_options = [
            '/opt/mplayer/bin/mencoder', '-oac', 'mp3lame', '-lameopts', 'vbr=3',
            '-ovc', 'x264', '-x264encopts', 'preset=slow:threads=auto',
            '-vf', f"flip,scale={r[0]}:{r[1]},dsize={dsize},expand={r[2]}:{r[3]}::::", '-sws', '4',
            *avi_files,
            '-of', 'lavf',
            '-o', f"{self.config.fcadefbneo_path}/avi/{self.replay.id}.mp4"
        ]

        log.info(f"Running mencoder with: {' '.join(mencoder_options)}")

        mencoder_rc = subprocess.run(
            mencoder_options,
            capture_output=True
        )

        try:
            mencoder_rc.check_returncode()
        except subprocess.CalledProcessError as e:
            log.error(
                f"Unable to process avi files. Return code: {e.returncode}, stdout: {mencoder_rc.stdout}, stderr: {mencoder_rc.stderr}")
            raise e

    def remove_old_avi_files(self):
        """Remove old avi files."""
        log.info('Removing old avi files')
        old_files = glob.glob(f"{self.config.fcadefbneo_path}/avi/*.avi")

        for f in old_files:
            log.info(f"Removing {f}")
            os.unlink(f)

    def get_rank_letter(self, rank: int) -> str:
        """Return the rank letter.

        Args:
            rank (int): Rank number

        Returns:
            str: Rank letter
        """
        ranks = {
            '0': '?',
            '1': 'E',
            '2': 'D',
            '3': 'C',
            '4': 'B',
            '5': 'A',
            '6': 'S',
        }

        return ranks[str(rank)]

    def get_description(self):
        """Get the description of the video.

        Returns:
            str: Description texts
        """
        log.info("Creating description")
        ranks = [
            self.get_rank_letter(self.replay.p1_rank),
            self.get_rank_letter(self.replay.p2_rank)
        ]
        tags = []

        if len(self.detected_characters) > 0:
            self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} (Rank {ranks[0]}) vs "\
                f"({self.replay.p2_loc}) {self.replay.p2} {ranks[1]} - {self.replay.date_replay} "\
                f"\nFightcade replay id: {self.replay.id}"

            first_chapter = True
            for match in self.detected_characters:
                # Add characters to tags
                tags.append(match[1])
                tags.append(match[2])

                # Remove leading 0: from replays
                detect_time = re.sub('^0:', '', match[2])
                if first_chapter:
                    self.description_text += f"\n0:00 {match[0]} vs {match[1]}"
                    first_chapter = False
                else:
                    self.description_text += f"\n{detect_time} {match[0]} vs {match[1]}"

        else:
            self.description_text = f"({self.replay.p1_loc}) {self.replay.p1} vs " \
                                    f"({self.replay.p2_loc}) {self.replay.p2} - {self.replay.date_replay}" \
                                    f"\nFightcade replay id: {self.replay.id}"

        # Add tags to the description text
        tags.append(self.replay.p1)
        tags.append(self.replay.p2)

        self.description_text += f"\n#fightcade\n#{self.replay.game}\n#" + '\n#'.join(
            set(tags)).replace(' ', '')

        # Read the append file:
        if self.config.description_append_file[0] is True:
            # Check if file exists:
            if not os.path.exists(self.config.description_append_file[1]):
                log.error(
                    f"Description append file {self.config.description_append_file[1]} doesn't exist")
                return False
            else:
                with open(self.config.description_append_file[1], 'r') as description_append:
                    self.description_text += "\n" + description_append.read()

        log.info("Finished creating description")


        log.debug(
            f"Description Text is: {self.description_text.encode('unicode-escape')}")
        return self.description_text

    def check_bad_words(self):
        """Check if the description contains bad words.

        Returns:
            boolean: Success or failure
        """
        log.info("Checking bad words")
        with open(self.config.bad_words_file, 'r') as bad_words_file:
            bad_words = bad_words_file.read().splitlines()
        bad_words = [x.lower() for x in bad_words]

        for word in bad_words:
            for player in [self.replay.p1, self.replay.p2]:
                if word in player.lower():
                    log.error(f"Bad word: {word} detected in player: {player}")
                    log.info("Finished checking bad words")
                    return False

        log.info("Finished checking bad words")
        return True

    def create_thumbnail(self):
        """Create thumbnail from video."""
        log.info("Making thumbnail")

        self.thumbnail = Thumbnail().get_thumbnail(self.replay)

        log.info("Finished making thumbnail")

    def update_thumbnail(self):
        """Add text, country and ranks to thumbnail."""
        log.info("Updating thumbnail")

        UpdateThumbnail().update_thumbnail(self.replay, self.thumbnail)
challenge_id = url.split('/')[5]