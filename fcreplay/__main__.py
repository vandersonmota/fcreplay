"""fcreplay.

Usage:
  fcreplay tasker [--instances=<instances>]
  fcreplay config validate <config.json>
  fcreplay config generate
  fcreplay get game <gameid>
  fcreplay get ranked <gameid> [--playerid=<playerid>] [--pages=<pages>]
  fcreplay get replay <url> [--playerrequested]
  fcreplay get weekly
  fcreplay get update_video_status
  fcreplay instance [--debug]
  fcreplay (-h | --help)
  fcreplay --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from fcreplay.tasker import Tasker
from docopt import docopt
from fcreplay import fclogging
from fcreplay.config import Config
from fcreplay.getreplay import Getreplay
from fcreplay.instance import Instance
import os


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

    if args['tasker']:
        if '--instances' in args:
            Tasker().main(instances=args['--instances'])
        else:
            Tasker().main()

    elif args['config']:
        if args['validate']:
            Config().validate_config_file(args['<config.json>'])
        if args['generate']:
            Config().generate_config()

    elif args['get']:
        if args['game']:
            Getreplay().get_game_replays(game=args['<gameid'])
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

        if args['weekly']:
            Getreplay().get_top_weekly()

        if args['update_video_status']:
            Getreplay().update_video_status()

    elif args['instance']:
        i = Instance()
        i.debug = args['--debug']
        i.main()


if __name__ == "__main__":
    main()