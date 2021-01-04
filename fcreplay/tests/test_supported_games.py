from cerberus import Validator
import json
import pkg_resources


class TestSupprtedGames:
    def test_supported_games(self):
        schema = {
            'game_ids': {
                'type': 'dict',
                'schema': {
                    'game_name': {
                        'type': 'string',
                        'required': True,
                    }
                }
            }
        }

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            supported_games = json.load(f)

        v = Validator(allow_unknown=True)
        assert v.validate(supported_games, schema)
