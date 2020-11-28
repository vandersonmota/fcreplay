"""getreplay.

Usage:
  fcreplayget game <gameid>
  fcreplayget ranked <gameid> [--playerid=<playerid>] [--pages=<pages>]
  fcreplayget replay <url> [--playerrequested]
  fcreplayget (-h | --help)

Options:
  -h --help         Show this screen.
"""
from fcreplay.logging import Logging
from fcreplay.config import Config
from fcreplay.database import Database
from retrying import retry
import datetime
import os
import re
import requests
from datetime import timedelta
from docopt import docopt


class Getreplay:
    def __init__(self):
        if 'REMOTE_DEBUG' in os.environ:
            import debugpy
            debugpy.listen(("0.0.0.0", 5678))
            debugpy.wait_for_client()

        self.config = Config().config
        self.db = Database()

    @retry(wait_random_min=5000, wait_random_max=10000, stop_max_attempt_number=3)
    def get_data(self, query):
        r = requests.post(
            "https://www.fightcade.com/api/",
            json=query
        )
        if r.status_code == 500:
            Logging().error("500 Code, trying up to 3 times")
            raise IOError("Unable to get data")
        else:
            return r

    def add_replay(self, replay, emulator, game, player_replay=True):
        challenge_id = replay['quarkid']
        p1_loc = replay['players'][0]['country']
        p2_loc = replay['players'][1]['country']
        p1 = replay['players'][0]['name']
        p2 = replay['players'][1]['name']
        date_replay = datetime.datetime.fromtimestamp(replay['date'] // 1000)
        length = replay['duration']
        created = False
        failed = False
        status = 'ADDED'
        date_added = datetime.datetime.utcnow()
        player_requested = player_replay

        if 'rank' in replay['players'] or 'rank' in replay['players'][1]:
            if replay['players'][0]['rank'] is None:
                p1_rank = '0'
            else:
                p1_rank = replay['players'][0]['rank']
            if replay['players'][1]['rank'] is None:
                p2_rank = '0'
            else:
                p2_rank = replay['players'][1]['rank']
        else:
            p1_rank = '0'
            p2_rank = '0'

        # Insert into database
        Logging().info(f"Looking for {challenge_id}")

        # Check if replay exists
        data = self.db.get_single_replay(challenge_id=challenge_id)
        if data is None:
            # Limit the length of videos
            if length > int(self.config['min_replay_length']) and length < int(self.config['max_replay_length']):
                Logging().info(f"Adding {challenge_id} to queue")
                self.db.add_replay(
                    challenge_id=challenge_id,
                    p1_loc=p1_loc,
                    p2_loc=p2_loc,
                    p1_rank=p1_rank,
                    p2_rank=p2_rank,
                    p1=p1,
                    p2=p2,
                    date_replay=date_replay,
                    length=length,
                    created=created,
                    failed=failed,
                    status=status,
                    date_added=date_added,
                    player_requested=player_requested,
                    game=game,
                    emulator=emulator,
                    video_processed=False
                )
                return('ADDED')
            else:
                Logging().info(f"{challenge_id} is only {length} not adding")
                if player_replay:
                    return('TOO_SHORT')
        else:
            Logging().info(f"{challenge_id} already exists")
            if player_replay:
                # Check if the returned replay is a player replay
                if data.player_requested:
                    return('ALREADY_EXISTS')
                else:
                    # Update DB to mark returned replay as player replay
                    self.db.update_player_requested(challenge_id=challenge_id)
                    return('MARKED_PLAYER')
            return('ALREADY_EXISTS')

    def get_game_replays(self, game):
        """Get game replays

        Args:
            game (String): Gameid
        """
        if game not in self.config['supported_games']:
            return('UNSUPPORTED_GAME')

        query = {'req': 'searchquarks', 'gameid': game}

        r = self.get_data(query)

        for i in r.json()['results']['results']:
            if i['emulator'] == 'fbneo' and i['live'] is False:
                status = self.add_replay(
                    replay=i,
                    emulator=i['emulator'],
                    game=game,
                    player_replay=False
                )
                if status != 'ADDED':
                    Logging().info(f'Not adding game, Status: {status}')

        return("ADDED")

    def get_top_weekly(self):
        """Get the top weekly replays
        """
        today = datetime.datetime.today()
        start_week = today - timedelta(days=today.weekday())
        start_week_ms = int(start_week.timestamp() * 1000)
        query = {'req': 'searchquarks', 'best': True, 'since': start_week_ms}

        replays = []
        pages = self.config['get_weekly_replay_pages']
        for i in range(0, pages):
            query['offset'] = i * 15
            r = self.get_data(query)
            replays += r.json()['results']['results']

        for i in replays:
            if i['gameid'] not in self.config['supported_games']:
                Logging().info(f"Game {i['gameid']} not supported for replay {i['quarkid']}")
                continue
            status = self.add_replay(
                replay=i,
                emulator=i['emulator'],
                game=i['gameid'],
                player_replay=False
            )
            if status != 'ADDED':
                Logging().info(f"Not adding replay {i['quarkid']}, Status: {status}")

        return("ADDED")

    def get_ranked_replays(self, game, username=None, pages=None):
        """Get ranked replays

        Args:
            game (String): Gameid
            username (String, optional): Player profile name. Defaults to None.
        """
        if game not in self.config['supported_games']:
            return('UNSUPPORTED_GAME')

        query = {"req": "searchquarks", "best": True, "gameid": game}

        if username is not None:
            query['username'] = username

        replays = []
        if pages is None:
            query['offset'] = 0
            r = self.get_data(query)
            replays += r.json()['results']['results']
        else:
            for page in range(0, pages):
                query['offset'] = page
                r = self.get_data(query)
                replays += r.json()['results']['results']

        for i in replays:
            if i['emulator'] == 'fbneo' and i['live'] is False:
                status = self.add_replay(
                    replay=i,
                    emulator=i['emulator'],
                    game=game,
                    player_replay=False
                )
                if status != 'ADDED':
                    Logging().info(f'Not adding game, Status: {status}')

        return("ADDED")

    def get_replay(self, url, player_requested=False):
        """Get a single replay

        Args:
            url (String): Link to replay
        """
        # Validate url, this could probably be done better
        pattern = re.compile('^https://replay.fightcade.com/fbneo/.*/[0-9]*-[0-9]*$')
        if not pattern.match(url):
            return('INVALID_URL')

        # Parse url
        emulator = url.split('/')[3]
        game = url.split('/')[4]
        challenge_id = url.split('/')[5]
        Logging().debug(f"Parsed url: emulator: {emulator}, game: {game}, challenge_id: {challenge_id}")

        if game not in self.config['supported_games']:
            return('UNSUPPORTED_GAME')

        # Get play replays
        query = {
            "req": "searchquarks",
            "quarkid": challenge_id
        }
        r = self.get_data(query)

        # Look for replay in results:
        for i in r.json()['results']['results']:
            if challenge_id == i['quarkid']:
                return self.add_replay(
                    replay=i,
                    emulator=emulator,
                    game=game,
                    player_replay=player_requested
                )
        return False


def console():
    arguments = docopt(__doc__, version='fcreplayget')

    getreplay = Getreplay()

    if arguments['game'] is True:
        getreplay.get_game_replays(game=arguments['<gameid>'])
    if arguments['ranked'] is True:
        getreplay.get_ranked_replays(game=arguments['<gameid>'], username=arguments['--playerid'], pages=arguments['--pages'])
    if arguments['replay'] is True:
        getreplay.get_replay(url=arguments['<url>'], player_requested=arguments['--playerrequested'])
