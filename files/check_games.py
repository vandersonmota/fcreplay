#!/usr/bin/env python3
"""Check Games.

Usage:
  check_games.py check <path_to_roms> <supported_games_file>

Options:
  -h --help      Show this screen
  --version      Show version
"""

from docopt import docopt
import glob
import json
import os
import sys


class CheckGames:
    """Class to check game files exist."""

    def __init__(self, rom_path: str, supported_games_file: str):
        """Initalisation."""
        self.all_games = [os.path.basename(x) for x in glob.glob(f"{rom_path}/*.zip")]

        with open(supported_games_file) as f:
            self.supported_games = json.load(f)

    def check_single_game(self, gameid: str) -> bool:
        """Check a single game.

        Check to see if a single game is present in the ROMs directory

        Args:
            gameid (str): gameid (without .zip extension)

        Returns:
            boolean: Returns True if game is present
        """
        if gameid not in self.supported_games:
            return False

        # Check for nes games
        if gameid.startswith("nes_"):
            if f"{gameid.lstrip('nes_')}.zip" not in self.all_games:
                print(f"NES gameid: {gameid}, not found!")
                return False
            return True

        if gameid.startswith("pce_"):
            if f"{gameid.lstrip('pce_')}.zip" not in self.all_games:
                print(f"PCE gameid: {gameid}, not found!")
                return False
            return True

        # Check aracde games
        if f"{gameid}.zip" not in self.all_games:
            print(f"Arcade gameid: {gameid}, not found!")
            return False
        return True

    def check_all_games(self) -> bool:
        """Check all games.

        Returns:
            boolean: Returns true if all games are present
                     Returns false if a single game is missing
        """
        for gameid in self.supported_games:
            if not self.check_single_game(gameid):
                return False

        return True


def main():
    args = docopt(__doc__, version='0.0.1')
    if args['check']:
        rom_path = args['<path_to_roms>']
        supported_games = args['<supported_games_file>']

    c = CheckGames(rom_path, supported_games)

    if not c.check_all_games():
        sys.exit(1)

    print("All games found!")
    sys.exit(0)


if __name__ == '__main__':
    main()
