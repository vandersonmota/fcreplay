from sqlalchemy import create_engine, func
import os
import logging
import json

from fcreplay.models import Base
from fcreplay.models import Job, Replays, Character_detect, Descriptions, Youtube_day_log
from sqlalchemy.orm import sessionmaker
from os import environ


class Database:
    def __init__(self):
        with open("config.json", 'r') as json_data_file:
            config = json.load(json_data_file)

        logging.basicConfig(
            format='%(asctime)s %(levelname)s: %(message)s',
            filename=config['logfile'],
            level=config['loglevel'],
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Create Engine
        try:
            self.engine = create_engine(config['sql_baseurl'], echo=True)
            Base.metadata.create_all(self.engine)
        except Exception as e:
            logging.error(f"Unable to connect to {config['sql_baseurl']}: {e}")

        self.Session = sessionmaker(bind=self.engine)

    def add_replay(self, **kwargs):
        session = self.Session()
        session.add(Replays(
            id=kwargs['challenge_id'],
            p1_loc=kwargs['p1_loc'],
            p2_loc=kwargs['p2_loc'],
            p1=kwargs['p1'],
            p2=kwargs['p2'],
            date_replay=kwargs['date_replay'],
            length=kwargs['length'],
            created=kwargs['created'],
            failed=kwargs['failed'],
            status=kwargs['status'],
            date_added=kwargs['date_added'],
            player_requested=kwargs['player_requested']
        ))
        session.commit()
        session.close()

    def get_single_replay(self, **kwargs):
        session = self.Session()
        replay = session.query(Replays).filter_by(
            id=kwargs['challenge_id']
        ).first()
        session.close()

        return(replay)

    def update_player_requested(self, **kwargs):
        session = self.Session()
        session.query(Replays).filter_by(
            id=kwargs['challenge_id'],
        ).update(
            {'player_requested': True}
        )
        session.commit()
        session.close()

    def add_detected_characters(self, **kwargs):
        session = self.Session()
        session.add(Character_detect(
            challenge_id=kwargs['challenge_id'],
            p1_char=kwargs['p1_char'],
            p2_char=kwargs['p2_char'],
            vid_time=kwargs['vid_time']
        ))
        session.commit()
        session.close()

    def add_current_job(self, **kwargs):
        session = self.Session()
        session.add(Job(
            challenge_id=kwargs['challenge_id'],
            start_time=kwargs['start_time'],
            length=kwargs['length']
        ))
        session.commit()
        session.close()

    def update_status(self, **kwargs):
        session = self.Session()
        session.query(Replays).filter_by(
            id=kwargs['challenge_id'],
        ).update(
            {'status': kwargs['status']}
        )
        session.commit()
        session.close()

    def add_description(self, **kwargs):
        session = self.Session()
        session.add(Descriptions(
            id=kwargs['challenge_id'],
            description=kwargs['description']
        ))
        session.commit()
        session.close()

    def update_youtube_day_log_count(self, **kwargs):
        session = self.Session()
        session.query(Youtube_day_log).filter_by(
            id='count'
        ).update(
            {
                'count': kwargs['count'],
                'date': kwargs['date']
            }
        )
        session.commit()
        session.close()

    def get_youtube_day_log(self):
        session = self.Session()
        day_log = session.query(
            Youtube_day_log
        ).filter_by(
            id='count'
        ).first()
        session.close()

        return(day_log)

    def get_oldest_player_replay(self):
        session = self.Session()
        replay = session.query(
            Replays
        ).filter_by(
            player_requested=True
        ).filter_by(
            created=False
        ).filter_by(
            failed=False
        ).order_by(
            Replays.date_added.desc()
        ).first()

        return(replay)

    def get_random_replay(self):
        session = self.Session()
        replay = session.query(
            Replays
        ).filter_by(
            failed=False
        ).filter_by(
            created=False
        ).order_by(
            func.random()
        ).first()

        return(replay)

    def get_oldest_replay(self):
        session = self.Session()
        replay = session.query(
            Replays
        ).filter_by(
            failed=False
        ).filter_by(
            created=False
        ).order_by(
            Replays.date_added.desc()
        ).first()

        return(replay)

    def update_failed_replay(self, **kwargs):
        session = self.Session()
        session.query(Replays).filter_by(
            id=kwargs['challenge_id']
        ).update(
            {
                'failed': True
            }
        )
        session.commit()
        session.close()

    def update_created_replay(self, **kwargs):
        session = self.Session()
        session.query(Replays).filter_by(
            id=kwargs['challenge_id']
        ).update(
            {
                'created': True
            }
        )
        session.commit()
        session.close()

    def get_current_job(self):
        session = self.Session()
        job = session.query(
            Job
        ).order_by(
            Job.id.desc()
        ).first()
        session.close()
        return(job)

    def get_all_queued_player_replays(self):
        session = self.Session()
        replays = session.query(
            Replays
        ).filter_by(
            player_requested = True
        ).filter_by(
            failed = False
        ).filter_by(
            created = False
        ).order_by(
            Replays.date_added.asc()
        ).all()
        session.close()
        return(replays)
