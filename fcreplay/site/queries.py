from fcreplay.site.models import Replays, Descriptions, Character_detect

import json
import pkg_resources


def _order(order_string):
    if order_string == 'date_replay':
        return Replays.date_replay.desc()
    elif order_string == 'date_added':
        return Replays.date_added.desc()
    elif order_string == 'length':
        return Replays.length.desc()
    else:
        raise LookupError


def all_replays():
    return Replays.query.filter(
        Replays.created == True,
        Replays.failed == False,
        Replays.video_processed == True
    ).order_by(Replays.date_added.desc())


def multiple_replays(challenge_ids):
    return Replays.query.filter(
        Replays.created == True,
        Replays.failed == False,
        Replays.video_processed == True,
        Replays.id.in_(challenge_ids)
    ).all()


def single_replay(challenge_id):
    return Replays.query.filter(
        Replays.id == challenge_id
    ).first()


def character_detect(challenge_id):
    return Character_detect.query.filter(
        Character_detect.challenge_id == challenge_id
    ).all()


def basic_search(game_id, search_query, order_string):
    return Replays.query.filter(
        Replays.created == True,
        Replays.failed == False,
        Replays.game.ilike(f'{game_id}'),
        Replays.id.in_(
            Descriptions.query.with_entities(Descriptions.id).filter(
                Descriptions.description.ilike(f'%{search_query}%')
            )
        ),
        Replays.video_processed == True
    ).order_by(_order(order_string))


def advanced_search(game_id, p1_rank, p2_rank, search_query, order_by, char1='Any', char2='Any'):
    if char1 == 'Any':
        char1 = '%'
    if char2 == 'Any':
        char2 = '%'

    if game_id == 'Any':
        game_id = '%'

    if p1_rank == 'any':
        p1_rank = '%'
    if p2_rank == 'any':
        p2_rank = '%'

    with open(pkg_resources.resource_filename('fcreplay', 'data/character_detect.json')) as json_data_file:
        character_dict = json.load(json_data_file)

    query = [
        Replays.created == True,
        Replays.failed == False,
        Replays.game.ilike(f'{game_id}'),
        Replays.p1_rank.ilike(f'{p1_rank}'),
        Replays.p2_rank.ilike(f'{p2_rank}'),
        Replays.id.in_(
            Descriptions.query.with_entities(Descriptions.id).filter(
                Descriptions.description.ilike(f'%{search_query}%')
            )
        ),
        Replays.video_processed == True
    ]

    if game_id in character_dict:
        query.append(
            Replays.id.in_(
                Character_detect.query.with_entities(Character_detect.challenge_id).filter(
                    Character_detect.p1_char.ilike(
                        f'{char1}') & Character_detect.p2_char.ilike(f'{char2}')
                ).union(
                    Character_detect.query.with_entities(Character_detect.challenge_id).filter(
                        Character_detect.p1_char.ilike(
                            f'{char2}') & Character_detect.p2_char.ilike(f'{char1}')
                    )
                )
            )
        )

    return Replays.query.filter(*query).order_by(_order(order_by))