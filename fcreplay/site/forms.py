from fcreplay.config import Config
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
import json
import pkg_resources

config = Config().config

with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
    supported_games = json.load(f)


class AdvancedSearchForm(FlaskForm):
    characters = [
        ('Any', 'Any'),
    ]

    orderby_list = [
        ('date_added', 'Date Added'),
        ('date_replay', 'Replay Date'),
        ('length', 'Length')
    ]

    rank_list = [
        ('any', 'Any'),
        ('0', '?'),
        ('1', 'E'),
        ('2', 'D'),
        ('3', 'C'),
        ('4', 'B'),
        ('5', 'A'),
        ('6', 'S')
    ]

    # Generate supported games
    game_list = []
    game_list.append(
        ('Any', 'Any')
    )

    for game in sorted(supported_games.items(), key=lambda item: item[1]['game_name']):
        game_list.append(
            (game[0], game[1]['game_name'])
        )

    search = StringField()
    game = SelectField('Game', choices=game_list,
                       render_kw={'class': 'fixed', 'onChange': 'gameSelect(this)', 'id': 'game'})
    p1_name = StringField(render_kw={'class': 'advancedAutoComplete', 'autocomplete': 'off'})
    p2_name = StringField(render_kw={'class': 'advancedAutoComplete', 'autocomplete': 'off'})
    p1_rank = SelectField('P1 Rank', choices=rank_list,
                          render_kw={'class': 'fixed', 'style': 'width:75px'})
    p2_rank = SelectField('P2 Rank', choices=rank_list,
                          render_kw={'class': 'fixed', 'style': 'width:75px'})
    char1 = SelectField('Character1', choices=characters,
                        render_kw={'class': 'fixed', 'style': 'width:75px'})
    char2 = SelectField('Character2', choices=characters,
                        render_kw={'class': 'fixed', 'style': 'width:75px'})
    order_by = SelectField('Order by', choices=orderby_list,
                           render_kw={'class': 'fixed'})
    submit = SubmitField('Search')


class SearchForm(FlaskForm):
    orderby_list = [
        ('date_replay', 'Replay Date'),
        ('date_added', 'Date Added'),
        ('length', 'Length')
    ]

    # Generate supported games
    game_list = []
    game_list.append(
        ('Any', 'Any')
    )
    for game in sorted(supported_games.items(), key=lambda item: item[1]['game_name']):
        game_list.append(
            (game[0], game[1]['game_name'])
        )

    search = StringField()
    game = SelectField('Game', choices=game_list,
                       render_kw={'class': 'fixed'})
    order_by = SelectField('Order by', choices=orderby_list,
                           render_kw={'class': 'fixed'})
    submit = SubmitField('Search')


class SubmitForm(FlaskForm):
    challenge_url = StringField()
    submit = SubmitField()
