from fcreplay.database import Database
from fcreplay.getreplay import Getreplay
import cmd2
import pprint


class Cli(cmd2.Cmd):
    def __init__(self):
        super().__init__()

        # Show this as the prompt when asking for input
        self.prompt = 'fcreplay> '

        # Used as prompt for multiline commands after the first line
        self.continuation_prompt = '... '

        self.db = Database()

    add_replay_parser = cmd2.Cmd2ArgumentParser(description='Add a new replay')
    add_replay_parser.add_argument('replay_url', help='Replay url of replay')

    delete_failed_parser = cmd2.Cmd2ArgumentParser(description='Delete a failed replay')
    delete_failed_parser.add_argument('challenge_id', help='Challenge id of replay')

    delete_all_failed_parser = cmd2.Cmd2ArgumentParser(description='Delete all failed replays')
    delete_all_failed_parser.add_argument('-y', '--yes', action='store_true',
                                          help='Force yes')

    delete_pending_parser = cmd2.Cmd2ArgumentParser(description='Delete a pending replay')
    delete_pending_parser.add_argument('challenge_id', help='Challenge id of the replay')

    delete_all_pending_parser = cmd2.Cmd2ArgumentParser(description='Delete all pending replays')
    delete_all_pending_parser.add_argument('-y', '--yes', action='store_true',
                                           help='Force yes')

    retry_replay_parser = cmd2.Cmd2ArgumentParser(description='Mark a replay to be re-encoded')
    retry_replay_parser.add_argument('challenge_id', help='Challenge id of replay')

    retry_all_failed_replays_parser = cmd2.Cmd2ArgumentParser(description='Mark all failed replays to be re-encoded')
    retry_all_failed_replays_parser.add_argument('-y', '--yes', action='store_true',
                                                 help='Force yes')

    list_replays_parser = cmd2.Cmd2ArgumentParser(description='List replays')
    list_replays_parser.add_argument('type',
                                     type=str,
                                     nargs=1,
                                     choices=['failed', 'finished', 'pending'],
                                     help='Type of replays to return')
    list_replays_parser.add_argument('-l', '--limit', default=10, type=int, help='Limit number of results')

    count_parser = cmd2.Cmd2ArgumentParser(description='List replays')
    count_parser.add_argument('type',
                              type=str,
                              nargs=1,
                              choices=['failed', 'finished', 'pending', 'all'],
                              help='Type of replays to count')

    def yes_or_no(self, question):
        while "the answer is invalid":
            reply = str(input(question + ' continue? (y/n): ')).lower().strip()
            if reply[:1] == 'y':
                return True
            if reply[:1] == 'n':
                return False

    @cmd2.with_argparser(add_replay_parser)
    def do_add_replay(self, args):
        Getreplay().get_replay(args.replay_url)
        return

    @cmd2.with_argparser(delete_failed_parser)
    def do_delete_failed(self, args):
        if self.yes_or_no(f"This will delete failed replay: {args.challenge_id},"):
            replay = self.db.get_single_replay(args.challenge_id)

            if replay is not None:
                if replay.failed is True:
                    self.db.delete_replay(args.challenge_id)
                    print(f"Deleated replay {args.challenge_id}")
                else:
                    print(f"Replay {args.challenge_id} isn't a faild replay")
                    return
            else:
                print(f"Replay {args.challenge_id} doesn't exist")
                return

    @cmd2.with_argparser(delete_all_failed_parser)
    def do_delete_all_failed(self, args):
        if not args.yes:
            if not self.yes_or_no("This will delete all failed replays,"):
                return

        failed_replays = self.db.get_all_failed_replays(limit=9999)

        if failed_replays is not None:
            for r in failed_replays:
                self.db.delete_replay(r.id)
                print(f"Removed replay: {r.id}")
        else:
            print("No failed replays")
            return

    @cmd2.with_argparser(delete_pending_parser)
    def do_delete_pending(self, args):
        if self.yes_or_no(f"This will delete the pending replay: {args.challenge_id},"):
            replay = self.db.get_single_replay(args.challenge_id)

            if replay is not None:
                if replay.failed is not True and replay.finished is not True:
                    self.db.delete_replay(replay.id)
                else:
                    print("Replay isn't a pending replay")
                    return
            else:
                print("No replay found")
                return

    @cmd2.with_argparser(delete_all_pending_parser)
    def do_delete_all_pending(self, args):
        if not args.yes:
            if not self.yes_or_no("This will delete all pending replays,"):
                return

        pending_replays = self.db.get_all_queued_replays(limit=9999)

        if pending_replays is not None:
            for r in pending_replays:
                self.db.delete_replay(r.id)
                print(f"Removed replay: {r.id}")
        else:
            print("No pending replays")
            return

    @cmd2.with_argparser(retry_replay_parser)
    def do_retry_replay(self, args):
        replay = self.db.get_single_replay(args.challenge_id)

        if replay is not None:
            self.db.rerecord_replay(args.challenge_id)
            print(f"Marked replay {args.challenge_id} to be re-encoded")
        else:
            print(f"Replay {args.challenge_id} doesn't exist")

    @cmd2.with_argparser(retry_all_failed_replays_parser)
    def do_retry_all_failed_replays(self, args):
        if not args.yes:
            if not self.yes_or_no("This will retry all failed replays,"):
                return

        failed_replays = self.db.get_all_failed_replays()
        if failed_replays is None:
            print("No failed replays to retry")
        else:
            for r in failed_replays:
                self.db.rerecord_replay(r.id)
                print(f"Marked failed replay {r.id} to be re-encoded")

    @cmd2.with_argparser(list_replays_parser)
    def do_ls(self, args):
        replays = None

        if 'failed' in args.type:
            replays = self.db.get_all_failed_replays(limit=args.limit)
        elif 'finished' in args.type:
            replays = self.db.get_all_finished_replays(limit=args.limit)
        elif 'pending' in args.type:
            replays = self.db.get_all_queued_replays(limit=args.limit)
        else:
            return

        if replays is not None:
            pp = pprint.PrettyPrinter()
            for r in replays:
                pp.pprint(r.__dict__)
        else:
            print(f"No replays found for query: {args}")

    @cmd2.with_argparser(count_parser)
    def do_count(self, args):
        replay_count = None

        if 'failed' in args.type:
            replay_count = self.db.get_failed_count()
        elif 'finished' in args.type:
            replay_count = self.db.get_finished_count()
        elif 'pending' in args.type:
            replay_count = self.db.get_pending_count()
        elif 'all' in args.type:
            replay_count = self.db.get_all_count()

        if replay_count is None:
            print("0")
        else:
            print(replay_count)
