"""getreplay.

Usage:
  fcreplayget game <gameid>
  fcreplayget ranked <gameid> [--playerid=<playerid>] [--pages=<pages>] 
  fcreplayget profile <playerid> <url> [--playerrequested]
  fcreplayget (-h | --help)

Options:
  -h --help         Show this screen.
"""
from fcreplay.database import Database
from retrying import retry
import datetime
import json
import logging
import os
import re
import requests
from docopt import docopt

if 'REMOTE_DEBUG' in os.environ:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    debugpy.wait_for_client()

with open("config.json", "r") as json_data_file:
    config = json.load(json_data_file)

db = Database()

# Setup Log
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    filename=config['logfile'],
    level=config['loglevel'],
    datefmt='%Y-%m-%d %H:%M:%S'
)


@retry(wait_random_min=5000, wait_random_max=10000, stop_max_attempt_number=3)
def get_data(query, profile=None):
    r = requests.post(
        "https://www.fightcade.com/api/",
        json=query
     )
    if "user not found" in r.text:
        logging.error(f"Unable to find profile: {profile}")
        raise LookupError
    if r.status_code == 500:
        logging.error("500 Code, trying up to 3 times")
        raise IOError("Unable to get data")
    else:
        return r


def add_replay(replay, emulator, game, player_replay=True):
    challenge_id = replay['quarkid']
    p1_loc = replay['players'][0]['country']
    p2_loc = replay['players'][1]['country']
    p1 = replay['players'][0]['name']
    p2 = replay['players'][1]['name']
    date_replay = datetime.datetime.fromtimestamp(replay['date']//1000)
    length = replay['duration']
    created = False
    failed = False
    status = 'ADDED'
    date_added = datetime.datetime.utcnow()
    player_requested = player_replay

    # Insert into database
    logging.info(f"Looking for {challenge_id}")

    # Check if replay exists
    data = db.get_single_replay(challenge_id=challenge_id)
    if data is None:
        # Limit the lenfth of videos
        if length > int(config['min_replay_length']) and length < int(config['max_replay_length']):
            logging.info(f"Adding {challenge_id} to queue")
            db.add_replay(
                challenge_id=challenge_id,
                p1_loc=p1_loc,
                p2_loc=p2_loc,
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
            logging.info(f"{challenge_id} is only {length} not adding")
            if player_replay:
                return('TOO_SHORT')

    else:
        logging.info(f"{challenge_id} already exists")
        if player_replay:
            # Check if the returned replay is a player replay
            if data.player_requested:
                return('ALREADY_EXISTS')
            else:
                # Update DB to mark returned replay as player replay
                db.update_player_requested(challenge_id=challenge_id)
                return('MARKED_PLAYER')
        return('ALREADY_EXISTS')


def get_game_replays(game):
    """Get game replays

    Args:
        game (String): Gameid
    """
    if game not in config['supported_games']:
        return('UNSUPPORTED_GAME')

    query = {'req': 'searchquarks', 'gameid': game}

    r = get_replay(query)

    for i in r.json()['results']['results']:
        if i['emulator'] == 'fbneo' and i['live'] is False:
            status = add_replay(
                replay=i,
                emaultor=i['emaultor'],
                game=game,
                player_replay=False
            )
            if status != 'ADDED':
                logging.info(f'Not adding game, Status: {status}')

    return("ADDED")


def get_ranked_replays(game, username=None, pages=1):
    """Get ranked replays

    Args:
        game (String): Gameid
        username (String, optional): Player profile name. Defaults to None.
    """
    if game not in config['supported_games']:
        return('UNSUPPORTED_GAME')

    query = {"req": "searchquarks", "best": True, "gameid": game}

    if username is not None:
        query['username'] = username

    replays = []
    if pages == 1:
        query['offset'] = 0
        r = get_data(query)
        replays += r.json()['results']['results']
    else:
        for page in range(0, pages):
            query['offset'] = page
            r = get_data(query)
            replays += r.json()['results']['results']

    for i in replays:
        if i['emulator'] == 'fbneo' and i['live'] is False:
            status = add_replay(
                replay=i,
                emulator=i['emulator'],
                game=game,
                player_replay=False
            )
            if status != 'ADDED':
                logging.info(f'Not adding game, Status: {status}')

    return("ADDED")


def get_replay(profile, url, player_requested=False):
    """Get a single replay from a players profile

    Args:
        profile (String): Players profile name
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
    logging.debug(f"Parsed url: emulator: {emulator}, game: {game}, challenge_id: {challenge_id}")

    if game not in config['supported_games']:
        return('UNSUPPORTED_GAME')

    # Get play replays
    query = {
        "req": "searchquarks",
        "offset": 0,
        "limit": 15,
        "username": profile
    }
    r = get_data(query, profile)

    # Look for replay in results:
    for i in r.json()['results']['results']:
        if challenge_id == i['quarkid']:
            return add_replay(
                replay=i,
                emulator=emulator,
                game=game,
                player_replay=player_requested
            )
    return False


def console():
    arguments = docopt(__doc__, version='fcreplayget')
    if arguments['game'] is True:
        get_game_replays(game=arguments['<gameid>'])
    if arguments['ranked'] is True:
        get_ranked_replays(game=arguments['<gameid>'], username=arguments['--playerid'], pages=arguments['--pages'])
    if arguments['profile'] is True:
        get_replay(profile=arguments['<playerid>'], url=arguments['<url>'], player_requested=arguments['--playerrequested'])


if __name__ == "__main__":
    console()
