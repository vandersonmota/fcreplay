#!/usr/bin/env python3
"""Sort games.

Usage:
  sort_games.py <supported_games_file>

Options:
  -h --help      Show this screen
  --version      Show version
"""

from docopt import docopt
import json
import sys


class SortGames:
    """Class to check game files exist."""

    def __init__(self, supported_games_file: str):
        """Initalisation."""
        with open(supported_games_file) as f:
            self.supported_games = json.load(f)

    def sort_games(self):
        """Sort games."""
        keys = sorted(list(self.supported_games.keys()))

        sorted_supported_games = {}
        for k in keys:
            sorted_supported_games[k] = self.supported_games[k]

        print(json.dumps(sorted_supported_games))


def main():
    """Main Function."""
    args = docopt(__doc__, version='0.0.1')
    supported_games = args['<supported_games_file>']

    s = SortGames(supported_games)

    s.sort_games()

    sys.exit(0)


if __name__ == '__main__':
    main()
