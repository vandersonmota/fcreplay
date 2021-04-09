"""fcreplay.

Usage:
  fcreplay cli
  fcreplay config generate
  fcreplay config validate <config.json>
  fcreplay get game <gameid>
  fcreplay get ranked <gameid> [--playerid=<playerid>] [--pages=<pages>]
  fcreplay get replay <url> [--playerrequested]
  fcreplay get weekly
  fcreplay instance [--debug]
  fcreplay tasker start check_top_weekly
  fcreplay tasker start check_video_status
  fcreplay tasker start retry_failed_replays
  fcreplay tasker start delete_failed_replays
  fcreplay tasker start recorder [--max_instances=<instances>]
  fcreplay (-h | --help)
  fcreplay --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from fcreplay.tasker import Tasker
from docopt import docopt
from fcreplay import fclogging
from fcreplay.cli import Cli
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

    if args['tasker']:
        if args['start']:
            if args['recorder']:
                if '--max_instances' in args:
                    Tasker().recorder(max_instances=args['--max_instances'])
                else:
                    Tasker().recorder()
            if args['check_top_weekly']:
                Tasker().check_top_weekly()
            if args['check_video_status']:
                Tasker().check_video_status()
            if args['retry_failed_replays']:
                Tasker().schedule_retry_failed_replays()
            if args['delete_failed_replays']:
                Tasker().schedule_delete_failed_replays()

    elif args['cli']:
        c = Cli()
        sys.exit(c.cmdloop())

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

        if args['weekly']:
            Getreplay().get_top_weekly()

    elif args['instance']:
        i = Instance()
        i.debug = args['--debug']
        try:
            i.main()
        except Exception as e:
            print(f"Unhandled exception: {e}")


if __name__ == "__main__":
    main()
