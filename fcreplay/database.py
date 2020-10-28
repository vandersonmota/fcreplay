from sqlalchemy import create_engine, func
import datetime

from fcreplay.logging import Logging
from fcreplay.models import Base
from fcreplay.models import Job, Replays, Character_detect, Descriptions, Youtube_day_log
from fcreplay.config import Config
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self):
        config = Config().config

        if 'DEBUG' in config['loglevel']:
            sql_echo = True
        else:
            sql_echo = False

        # Create Engine
        try:
            self.engine = create_engine(config['sql_baseurl'], echo=sql_echo)
            Base.metadata.create_all(self.engine)
        except Exception as e:
            Logging().error(f"Unable to connect to {config['sql_baseurl']}: {e}")
            raise e

        self.Session = sessionmaker(bind=self.engine)

    def add_replay(self, **kwargs):
        session = self.Session()
        session.add(Replays(
            id=kwargs['challenge_id'],
            p1_loc=kwargs['p1_loc'],
            p2_loc=kwargs['p2_loc'],
            p1_rank=kwargs['p1_rank'],
            p2_rank=kwargs['p2_rank'],
            p1=kwargs['p1'],
            p2=kwargs['p2'],
            date_replay=kwargs['date_replay'],
            length=kwargs['length'],
            created=kwargs['created'],
            failed=kwargs['failed'],
            status=kwargs['status'],
            date_added=kwargs['date_added'],
            player_requested=kwargs['player_requested'],
            game=kwargs['game'],
            emulator=kwargs['emulator'],
            video_processed=kwargs['video_processed']
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

    def add_job(self, **kwargs):
        session = self.Session()
        session.add(Job(
            id=kwargs['challenge_id'],
            start_time=kwargs['start_time'],
            instance=kwargs['length']
        ))
        session.commit()
        session.close()

    def remove_job(self, **kwargs):
        session = self.Session()
        session.query(Job).filter_by(
            id=kwargs['challenge_id']
        ).delete()
        session.commit()
        session.close()

    def get_job(self, challenge_id):
        session = self.Session()
        job = session.query(
            Job
        ).filter_by(
            id=challenge_id
        ).first()
        session.close()
        return job

    def get_job_count(self):
        session = self.Session()
        count = session.execute('select count(id) from job').first()[0]
        return count

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

        return day_log

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
        ).filter_by(
            status='ADDED'
        ).order_by(
            Replays.date_added.desc()
        ).first()
        session.close()
        return replay

    def get_random_replay(self):
        session = self.Session()
        replay = session.query(
            Replays
        ).filter_by(
            failed=False
        ).filter_by(
            created=False
        ).filter_by(
            status='ADDED'
        ).order_by(
            func.random()
        ).first()
        session.close()

        return replay

    def get_oldest_replay(self):
        session = self.Session()
        replay = session.query(
            Replays
        ).filter_by(
            failed=False
        ).filter_by(
            created=False
        ).filter_by(
            status='ADDED'
        ).order_by(
            Replays.date_added.desc()
        ).first()
        session.close()

        return replay

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

    def get_all_queued_player_replays(self):
        session = self.Session()
        replays = session.query(
            Replays
        ).filter_by(
            player_requested=True
        ).filter_by(
            failed=False
        ).filter_by(
            created=False
        ).order_by(
            Replays.date_added.asc()
        ).all()
        session.close()
        return replays

    def get_unprocessed_replays(self):
        session = self.Session()
        replays = session.query(
            Replays
        ).filter_by(
            failed=False
        ).filter_by(
            created=True
        ).filter_by(
            video_processed=False
        ).all()
        return replays

    def set_replay_processed(self, **kwargs):
        session = self.Session()
        session.query(Replays).filter_by(
            id=kwargs['challenge_id']
        ).update(
            {'video_processed': True, "date_added": datetime.datetime.now()}
        )
        session.commit()
        session.close()

    def rerecord_replay(self, **kwargs):
        """Sets replay to be rerecorded
        """
        session = self.Session()
        # Set replay to original status
        session.query(Replays).filter_by(
            id=kwargs['challenge_id']
        ).update(
            {'failed': False, 'created': False, 'status': 'ADDED'}
        )
        session.commit()

        # Remove description if it exists
        session.query(Descriptions).filter_by(
            id=kwargs['challenge_id']
        ).delete()
        session.commit()

        # Remove job if it exists
        session.query(Job).filter_by(
            id=kwargs['challenge_id']
        ).delete()
        session.commit()

        # Remove character detection if it exists
        session.query(Character_detect).filter_by(
            challenge_id=kwargs['challenge_id']
        ).delete()
        session.commit()

        session.close()
