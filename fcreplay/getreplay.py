from fcreplay.config import Config
from fcreplay.status import status
from retrying import retry
import json
import logging
import pkg_resources
import re
import requests
from replaydata import ReplayData

log = logging.getLogger('fcreplay')


class Getreplay:
    """Classmethod to getreplay."""

    def __init__(self):
        """Initialize the Getreplay class."""
        self.config = Config()

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            self.supported_games = json.load(f)

    @retry(wait_random_min=5000, wait_random_max=10000, stop_max_attempt_number=3)
    def get_data(self, query):
        """Get data from fightcade api.

        Args:
            query (dict): Query to pass to fightcade API

        Raises:
            IOError: Rase error when unable to get data or status code == 500

        Returns:
            dict: Returns dict containting the request
        """
        r = requests.post(
            "https://www.fightcade.com/api/",
            json=query
        )
        if r.status_code == 500:
            log.error("500 Code, trying up to 3 times")
            raise IOError("Unable to get data")
        else:
            return r.json()


    def get_replay(self, url):
        """Get a replay by url.

        Args:
            url (str): Url to retrieve the replay from
            player_requested (bool, optional): Is this a player requested replay. Defaults to False.

        Returns:
            str: Returns the string status of the request
        """
        # Validate url, this could probably be done better
        pattern = re.compile('^https://replay\.fightcade\.com/fbneo/.*/[0-9]*-[0-9]*$')
        if not pattern.match(url):
            return(status.INVALID_URL)

        # Parse url
        emulator = url.split('/')[3]
        game = url.split('/')[4]
        challenge_id = url.split('/')[5]
        log.debug(f"Parsed url: emulator: {emulator}, game: {game}, challenge_id: {challenge_id}")

        if game not in self.supported_games:
            return(status.UNSUPPORTED_GAME)

        # Get play replays
        query = {
            "req": "searchquarks",
            "quarkid": challenge_id
        }
        r = self.get_data(query)

        # Look for replay in results:
        for i in r['results']['results']:
            if challenge_id == i['quarkid']:
                return ReplayData(id=challenge_id, emulator=emulator, game=game)
