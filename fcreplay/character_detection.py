"""Character Detection.

This class is used to take the overlay data from a pickle file
and generate a list of times characters were detected
"""

import pickle
import datetime


class CharacterDetection:
    """Character detection class from pickle file."""

    def __init__(self):
        """Initiliser."""
        self.pickle_path = '/Fightcade/emulator/fbneo/avi/overlay.pickle'
        self.video_start_time = None
        self.timeline = []

    def _load_overlay_pickle(self) -> dict:
        """Return a dict containing overlay data."""
        with open(self.pickle_path, 'rb') as f:
            overlay_data = pickle.load(f)
            self.video_start_time = overlay_data.pop(0)['start_time']

        return overlay_data

    def _characters_exist(self) -> bool:
        """Check to see if p1character or p2character exists in overlay data.

        Returns:
            bool
        """
        for event in self.overlay_data:
            if any(event['overlay_type'] in i for i in ['p1character', 'p2character']):
                return True

        return False

    def _get_video_time(self, detection_time: datetime.datetime) -> str:
        """Return the video time return as a string.

        Args:
            detection_time (Datetime): Datetime of when a detection event happened

        Returns:
            str: String format of video time h:mm:ss
        """
        time_seconds = int((detection_time - self.video_start_time).total_seconds())
        formatted_time = str(datetime.timedelta(seconds=time_seconds))
        if self._time_too_soon(time_seconds):
            del self.timeline[-1]
            return formatted_time
        else:
            return formatted_time

    def _time_too_soon(self, new_time: int) -> bool:
        """Check time against previous time, if it's within a 5 seconds, then return true else return false.

        Args:
            new_time (int): <seconds>
        """
        if len(self.timeline) == 0:
            return False

        pt_list = self.timeline[-1][2].split(':')
        pt_list = list(map(int, pt_list))

        pt_seconds = (((pt_list[0] * 60) + pt_list[1]) * 60) + pt_list[2]

        if (new_time - pt_seconds) < 5:
            return True
        else:
            return False

    def _create_timeline(self) -> list:
        """Create a timeline of character changes.

        Returns:
            list: [[str: p1character, str: p2character, str: time]...]
        """
        p1character = None
        p2character = None
        overlay_time = None

        for event in self.overlay_data:
            set_characters = [p1character, p2character]

            if 'p1character' == event['overlay_type']:
                p1character = event['overlay_data']
                overlay_time = event['date']

            elif 'p2character' == event['overlay_type']:
                p2character = event['overlay_data']
                overlay_time = event['date']

            if (None not in [p1character, p2character, overlay_time]) and [p1character, p2character] != set_characters:
                self.timeline.append([p1character, p2character, self._get_video_time(overlay_time)])

        return self.timeline

    def get_characters(self):
        """Get characters.

        Returns:
            list: Returns a nested list of characters and the time they were discovered,
                  eg: [['p1char', 'p2char', '0:01']]
        """
        self.overlay_data = self._load_overlay_pickle()

        if self._characters_exist():
            return self._create_timeline()

        else:
            return []
