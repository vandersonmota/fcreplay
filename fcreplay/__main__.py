"""fcreplay.

Usage:
  fcreplay config generate
  fcreplay config validate <config.json>
  fcreplay get game <gameid>
  fcreplay (-h | --help)
  fcreplay --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt
from fcreplay import fclogging
from fcreplay.config import Config
from fcreplay.getreplay import Getreplay
from fcreplay.instance import Instance
import os
import sys


def main():
    if 'REMOTE_DEBUG' in os.environ:
        print("Starting remote debugger on port 5678")
        import debugpy
        debugpy.listen(("0.0.0.0", 5678))
        print("Waiting for connection...")
        debugpy.wait_for_client()

    args = docopt(__doc__, version='fcreplay 0.9.1')

    # Setup logging if not checking or generating config
    if not args['config']:
        fclogging.setup_logger()

    elif args['config']:
        if args['validate']:
            Config().validate_config_file(args['<config.json>'])
        if args['generate']:
            Config().generate_config()

    elif args['get']:
        if args['game']:
            Getreplay().get_game_replays(game=args['<gameid>'])
        if args['ranked']:
            Getreplay().get_ranked_replays(
                game=args['<gameid>'],
                username=args['--playerid'],
                pages=args['--pages']
            )
        if args['replay']:
            Getreplay().get_replay(
                url=args['<url>'],
                player_requested=args['--playerrequested']
            )

    elif args['instance']:
        i = Instance()
        i.debug = args['--debug']
        try:
            i.main()
        except Exception as e:
            print(f"Unhandled exception: {e}")


if __name__ == "__main__":
    main()
