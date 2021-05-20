import json
import pkg_resources


class TestSupprtedGames:
    def test_supported_games(self):
        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            supported_games = json.load(f)

        for gameid in supported_games:
            if 'game_name' not in supported_games[gameid]:
                assert False, f"Game name not present for {gameid}"

            if 'aspect_ratio' not in supported_games[gameid]:
                assert False, f"Aspect ratio not present for {gameid}"

            for ar in supported_games[gameid]['aspect_ratio']:
                if not isinstance(ar, int):
                    assert False, f"Aspect ratio for {gameid} is not int"

    def test_duplicated_games(self):
        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            supported_games = json.load(f)

        game_names = []
        for gameid in supported_games:
            if supported_games[gameid]['game_name'] in game_names:
                raise ValueError(f"Duplicate game name '{gameid}': '{supported_games[gameid]['game_name']}'")

            game_names.append(supported_games[gameid]['game_name'])
