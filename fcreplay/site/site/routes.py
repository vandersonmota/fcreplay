from fcreplay.site.site.forms import AdvancedSearchForm, SearchForm, SubmitForm
from flask import abort, jsonify, render_template, request, session, redirect, send_from_directory, url_for

import datetime
import pytz

def index():
    searchForm = SearchForm()
    page = request.args.get('page', 1, type=int)
    pagination = Replays.query.filter(
        Replays.created == 'yes'
    ).filter(
        Replays.failed == 'no'
    ).filter(
        Replays.video_processed == True
    ).order_by(Replays.date_added.desc()).paginate(page, per_page=9)
    replays = pagination.items

    return render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm, games=config['supported_games'])


def videolinks():
    if 'ids' not in request.json:
        abort(404)

    replays = Replays.query.filter(
        Replays.created == True,
        Replays.failed == False,
        Replays.video_processed == True,
        Replays.id.in_(request.json['ids'])
    ).all()

    replay_data = {}
    for i in replays:
        replay_data[i.id] = f"https://fightcadevids.com/video/{i.id}"

    return jsonify(replay_data)


def supportedgames():
    return jsonify(config['supported_games'])


def submit():
    searchForm = SearchForm()
    submitForm = SubmitForm()
    return render_template('submit.j2.html', form=searchForm, submitForm=submitForm, submit_active=True)


def submitResult():
    logging.debug(f"Session: {session}")
    # I feel like there should be a better way to do this
    if request.method == 'POST':
        result = SubmitForm(request.form)

        challenge_id = result.challenge_url.data
        session['challenge_url'] = result.challenge_url.data

        from fcreplay.getreplay import Getreplay
        replay_result = Getreplay().get_replay(challenge_id, player_requested=True)

        session['replay_result'] = replay_result
        logging.info(f"Submit replay: {challenge_id} status is: {replay_result}")

        # Add replay and get status here
        return redirect(url_for('submitResult'))
    else:
        searchForm = SearchForm()
        if 'replay_result' not in session:
            return index()
        result = session['replay_result']
        return render_template('submitResult.j2.html', form=searchForm, result=result, submt_active=True)


def send_js(path):
    return send_from_directory('templates/assets', path)


def about():
    searchForm = SearchForm()

    sortedGames = sorted(config['supported_games'])
    supportedGames = {}
    for game in sortedGames:
        supportedGames[game] = config['supported_games'][game]
        supportedGames[game]['count'] = db.session.execute(f"select count(id) from replays where created = true and game = '{game}'").first()[0]

    numberOfReplays = db.session.execute('select count(id) from replays where created = true').first()[0]

    toProcess = db.session.execute('select count(id) from replays where created = false and failed = false').first()[0]

    return render_template('about.j2.html', about_active=True, form=searchForm, supportedGames=supportedGames, numberOfReplays=numberOfReplays, toProcess=toProcess)


def advancedSearch():
    searchForm = SearchForm()
    advancedSearchForm = AdvancedSearchForm()
    return render_template('advancedSearch.j2.html', advancedsearch_active=True, form=searchForm, advancedSearchForm=advancedSearchForm)


def advancedSearchResult():
    logging.debug(f"Session: {session}")
    # I feel like there should be a better way to do this
    if request.method == 'POST':
        result = AdvancedSearchForm(request.form)

        session['search'] = result.search.data
        session['char1'] = result.char1.data
        session['char2'] = result.char2.data
        session['p1_rank'] = result.p1_rank.data
        session['p2_rank'] = result.p1_rank.data
        session['order_by'] = result.order_by.data
        session['game'] = result.game.data

        return redirect(url_for('advancedSearchResult'))
    else:
        if 'search' not in session:
            return index()
        search_query = session['search']
        char1 = session['char1']
        char2 = session['char2']
        p1_rank = session['p1_rank']
        p2_rank = session['p2_rank']
        order_by = session['order_by']
        game = session['game']

    searchForm = SearchForm()

    page = request.args.get('page', 1, type=int)

    if order_by == 'date_replay':
        order = Replays.date_replay.desc()
    elif order_by == 'date_added':
        order = Replays.date_added.desc()
    elif order_by == 'length':
        order = Replays.length.desc()
    else:
        raise LookupError

    if char1 == 'Any':
        char1 = '%'
    if char2 == 'Any':
        char2 = '%'

    if game == 'Any':
        game = '%'

    if p1_rank == 'any':
        p1_rank = '%'
    if p2_rank == 'any':
        p2_rank = '%'

    replay_query = [
        Replays.created == True,
        Replays.failed == False,
        Replays.game.ilike(f'{game}'),
        Replays.p1_rank.ilike(f'{p1_rank}'),
        Replays.p2_rank.ilike(f'{p2_rank}'),
        Replays.id.in_(
            Descriptions.query.with_entities(Descriptions.id).filter(
                Descriptions.description.ilike(f'%{search_query}%')
            )
        ),
        Replays.video_processed == True
    ]

    if game in character_dict:
        replay_query.append(
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

    logging.debug(Replays.query.filter(*replay_query))
    pagination = Replays.query.filter(*replay_query).order_by(order).paginate(page, per_page=9)
    replays = pagination.items

    return render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm, games=config['supported_games'])


def search():
    logging.debug(f"Session: {session}")
    # I feel like there should be a better way to do this
    if request.method == 'POST':
        result = SearchForm(request.form)

        session['search'] = result.search.data
        session['order_by'] = result.order_by.data
        session['game'] = result.game.data

        return redirect(url_for('search'))
    else:
        if 'search' not in session:
            return index()
        search_query = session['search']
        order_by = session['order_by']
        game = session['game']

    searchForm = SearchForm(request.form,
                            search=search_query,
                            game=game)

    page = request.args.get('page', 1, type=int)

    if order_by == 'date_replay':
        order = Replays.date_replay.desc()
    elif order_by == 'date_added':
        order = Replays.date_added.desc()
    elif order_by == 'length':
        order = Replays.length.desc()
    else:
        raise LookupError

    if game == 'Any':
        game = '%'

    replay_query = Replays.query.filter(
        Replays.created == True
    ).filter(
        Replays.failed == False
    ).filter(
        Replays.game.ilike(f'{game}')
    ).filter(
        Replays.id.in_(
            Descriptions.query.with_entities(Descriptions.id).filter(
                Descriptions.description.ilike(f'%{search_query}%')
            )
        )
    ).filter(
        Replays.video_processed == True
    ).order_by(order)

    logging.debug(replay_query)
    pagination = replay_query.paginate(page, per_page=9)
    replays = pagination.items

    return render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm, games=config['supported_games'])


def robots():
    return send_from_directory(app.static_folder, request.path[1:])


def sitemap():
    tz = pytz.timezone("Pacific/Auckland")
    aware_dt = tz.localize(datetime.datetime.now())
    update_date = aware_dt.isoformat()
    return render_template('sitemap.j2.xml', update_date=update_date)


def videopage(challenge_id):
    searchForm = SearchForm()

    replay = Replays.query.filter(
        Replays.id == challenge_id
    ).first()
    char_detect = Character_detect.query.filter(
        Character_detect.challenge_id == challenge_id
    ).all()

    characters = []
    for c in char_detect:
        characters.append(
            {
                'p1_char': c.p1_char,
                'p2_char': c.p2_char,
                'vid_time': c.vid_time,
                'seek_time': sum(int(x) * 60 ** i for i, x in enumerate(reversed(c.vid_time.split(":"))))
            }
        )

    seek = request.args.get('seek', default=0, type=float)

    logging.debug(
        f"Video page, replay: {replay}, characters: {characters}, seek: {seek}")
    return render_template('video.j2.html', replay=replay, characters=characters, seek=seek, form=searchForm, games=config['supported_games'])