from feedgen.feed import FeedGenerator
from fcreplay.database import Database
import json
import pkg_resources


class Feed:
    def __init__(self):
        self.fg = FeedGenerator()
        self.fg.id('https://fightcadevids.com/feeds')
        self.fg.title('FightcadeVids')
        self.fg.author({'name': 'Gino Lisignoli', 'email': 'glisignoli@gmail.com'})
        self.fg.link(href='https://fightcadevids.com') # rel='alternate')
        self.fg.logo('https://fightcadevids.com/assets/img/fightcade_logo')
        self.fg.subtitle('Fightcade Videos')
        self.fg.language('en')

        self.atomfeed = self.fg.atom_str(pretty=True)
        self.rssfeed = self.fg.rss_str(pretty=True)

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            self.supported_games = json.load(f)

        self.db = Database()

    def generate_feed(self):
        # Read lates videos from database
        replays = self.db.get_all_finished_replays(limit=25)

        dates = []

        for r in replays:
            if r.video_youtube_uploaded:
                link = f'https://www.youtube.com/watch?v={r.video_youtube_id}'
            else:
                link = f'http://archive.org/details/{r.id.replace("@", "-")}'

            description = f"{self.supported_games[r.game]['game_name']} - ({r.p1_loc}) {r.p1} vs {r.p2_loc}) {r.p2}"

            fe = self.fg.add_entry()
            fe.title(description)
            fe.link(href=link, rel='alternate')
            fe.id('https://fightcadevids.com/video/' + r.id)
            fe.description(description)
            fe.content(description)
            fe.pubDate(r.date_added.strftime('%a, %e %b %Y %H:%M:%S UTC'))
            fe.updated(r.date_added.strftime('%a, %e %b %Y %H:%M:%S UTC'))

            dates.append(r.date_added)

        # Get newest date from list
        newest_date = max(dates)

        self.fg.updated(newest_date.strftime('%a, %e %b %Y %H:%M:%S UTC'))

    def render_atom(self):
        self.generate_feed()
        atom = self.fg.atom_str(pretty=True)
        return atom

    def render_rss(self):
        self.generate_feed()
        rss = self.fg.rss_str(pretty=True)
        return rss
