import pickle
import datetime


class CharacterDetection:
    def __init__(self):
        self.pickle_path = '/Fightcade/emulator/fbneo/avi/overlay.pickle'
        self.video_start_time = None

    def _load_overlay_pickle(self) -> dict:
        """Returns a dict containing overlay data
        """
        with open(self.pickle_path, 'rb') as f:
            overlay_data = pickle.load(f)
            self.video_start_time = overlay_data.pop(0)['start_time']

        return overlay_data

    def _characters_exist(self) -> bool:
        """Check to se if p1character or p2character exists in overlay data

        Returns:
            bool
        """
        for event in self.overlay_data:
            if any(event['overlay_type'] in i for i in ['p1character', 'p2character']):
                return True

        return False

    def _get_video_time(self, detection_time) -> str:
        """Returns the video time return as a string

        Args:
            detection_time (Datetime): Datetime of when a detection event happened

        Returns:
            str: String format of video time h:mm:ss
        """
        time_seconds = (detection_time - self.video_start_time).total_seconds()
        return str(datetime.timedelta(seconds=int(time_seconds)))

    def _create_timeline(self) -> list:
        """Creates a timeline of character changes

        Returns:
            list: [[str: p1character, str: p2character, str: time]...]
        """
        p1character = None
        p2character = None
        overlay_time = None
        timeline = []

        for event in self.overlay_data:
            set_characters = [p1character, p2character]

            if 'p1character' == event['overlay_type']:
                p1character = event['overlay_data']
                overlay_time = event['date']

            elif 'p2character' == event['overlay_type']:
                p2character = event['overlay_data']
                overlay_time = event['date']

            if (None not in [p1character, p2character, overlay_time]) and [p1character, p2character] != set_characters:
                timeline.append([p1character, p2character, self._get_video_time(overlay_time)])

        return timeline

    def get_characters(self):
        self.overlay_data = self._load_overlay_pickle()

        if self._characters_exist():
            return self._create_timeline()

        else:
            return []
