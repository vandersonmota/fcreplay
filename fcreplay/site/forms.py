from fcreplay.config import Config
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField

config = Config().config


class AdvancedSearchForm(FlaskForm):
    characters = [
        ('Any', 'Any'),
        ('alex', 'alex'),
        ('akuma', 'akuma'),
        ('chunli', 'chunli'),
        ('dudley', 'dudley'),
        ('elena', 'elena'),
        ('hugo', 'hugo'),
        ('ibuki', 'ibuki'),
        ('ken', 'ken'),
        ('makoto', 'makoto'),
        ('necro', 'necro'),
        ('oro', 'oro'),
        ('q', 'q'),
        ('remy', 'remy'),
        ('ryu', 'ryu'),
        ('sean', 'sean'),
        ('twelve', 'twelve'),
        ('urien', 'urien'),
        ('yang', 'yang'),
        ('yun', 'yun')]

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

    for game in sorted(config['supported_games'].items(), key=lambda item: item[1]['game_name']):
        game_list.append(
            (game[0], game[1]['game_name'])
        )

    search = StringField()
    game = SelectField('Game', choices=game_list,
                       render_kw={'class': 'fixed', 'onChange': 'gameSelect(this)', 'id': 'game'})
    p1_rank = SelectField('P1 Rank', choices=rank_list,
                          render_kw={'class': 'fixed', 'style': 'width:75px'})
    p2_rank = SelectField('P2 Rank', choices=rank_list,
                          render_kw={'class': 'fixed', 'style': 'width:75px'})
    char1 = SelectField('Character1', choices=characters,
                        render_kw={'class': 'fixed'})
    char2 = SelectField('Character2', choices=characters,
                        render_kw={'class': 'fixed'})
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
    for game in sorted(config['supported_games'].items(), key=lambda item: item[1]['game_name']):
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