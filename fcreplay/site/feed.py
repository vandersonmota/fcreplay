from feedgen.feed import FeedGenerator
from fcreplay.database import Database
from fcreplay.config import Config

import json
import pkg_resources


class Feed:
    def __init__(self):
        self.config = Config().config

        self.fg = FeedGenerator()
        self.fg.id('https://fightcadevids.com/feeds')
        self.fg.title('FightcadeVids')
        self.fg.author({'name': 'Gino Lisignoli', 'email': 'glisignoli@gmail.com'})
        self.fg.link(href='https://fightcadevids.com') # rel='alternate')
        self.fg.logo('https://fightcadevids.com/assets/img/fightcade_logo')
        self.fg.subtitle('Fightcade Videos')
        self.fg.language('en')
        self.fg.updated('2019-01-01T12:00:00Z')

        self.atomfeed = self.fg.atom_str(pretty=True)
        self.rssfeed = self.fg.rss_str(pretty=True)

        with open(pkg_resources.resource_filename('fcreplay', 'data/supported_games.json')) as f:
            self.supported_games = json.load(f)

        self.db = Database()

    def generate_feed(self):
        # Read lates videos from database
        replays = self.db.get_all_finished_replays(limit=25)

        for r in replays:
            description = self.db.get_description(r.id).description

            fe = self.fg.add_entry()
            fe.title(f"{self.supported_games[r.game]} - "\
                     f"({r.p1_loc}) {r.p1} vs "\
                     f"({r.p2_loc}) {r.p2}")
            fe.link(href='https://fightcadevids.com/video/' + r.id, rel='alternate')
            fe.id('https://fightcadevids.com/video/' + r.id)
            fe.description(description)
            fe.content(description)
            fe.pubDate(r.date_added.strftime('%a, %e %b %Y %H:%M:%S UTC'))
            fe.updated(r.date_added.strftime('%a, %e %b %Y %H:%M:%S UTC'))

    def render_atom(self):
        self.generate_feed()
        atom = self.fg.atom_str(pretty=True)
        return atom

    def render_rss(self):
        self.generate_feed()
        rss = self.fg.rss_str(pretty=True)
        return rss
