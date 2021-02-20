from fcreplay.config import Config
from fcreplay.models import Base
from fcreplay.models import Job, Replays, Character_detect, Descriptions, Youtube_day_log
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import datetime
import logging

log = logging.getLogger('fcreplay')


class Database:
    def __init__(self):
        config = Config().config

        if 'DEBUG' in config['loglevel']:
            sql_echo = True
        else:
            logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
            sql_echo = False

        # Create Engine
        try:
            log.debug(f"Creating DB Instance with: {config['sql_baseurl']}")
            self.engine = create_engine(config['sql_baseurl'], echo=sql_echo, pool_pre_ping=True)
            Base.metadata.create_all(self.engine)
        except Exception as e:
            log.error(f"Unable to connect to {config['sql_baseurl']}: {e}")
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

    def get_single_replay(self, challenge_id):
        session = self.Session()
        replay = session.query(Replays).filter_by(
            id=challenge_id
        ).first()
        session.close()

        return(replay)

    def update_player_requested(self, challenge_id):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id,
        ).update(
            {'player_requested': True}
        )
        session.commit()
        session.close()

    def add_detected_characters(self, challenge_id, p1_char, p2_char, vid_time, game):
        session = self.Session()
        session.add(Character_detect(
            challenge_id=challenge_id,
            p1_char=p1_char,
            p2_char=p2_char,
            vid_time=vid_time,
            game=game
        ))
        session.commit()
        session.close()

    def add_job(self, challenge_id, start_time, length):
        session = self.Session()
        session.add(Job(
            id=challenge_id,
            start_time=start_time,
            instance=length
        ))
        session.commit()
        session.close()

    def remove_job(self, challenge_id):
        session = self.Session()
        session.query(Job).filter_by(
            id=challenge_id
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

    def get_all_count(self):
        session = self.Session()
        count = session.execute('select count(id) from replays').first()[0]
        return count

    def get_failed_count(self):
        session = self.Session()
        count = session.execute('select count(id) from replays where failed = true').first()[0]
        return count

    def get_pending_count(self):
        session = self.Session()
        count = session.execute("select count(id) from replays where created = false and failed = false").first()[0]
        return count

    def get_finished_count(self):
        session = self.Session()
        count = session.execute("select count(id) from replays where created = true and failed = false").first()[0]
        return count

    def update_status(self, challenge_id, status):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id,
        ).update(
            {'status': status}
        )
        session.commit()
        session.close()

    def add_description(self, challenge_id, description):
        session = self.Session()
        session.add(Descriptions(
            id=challenge_id,
            description=description
        ))
        session.commit()
        session.close()

    def update_youtube_day_log_count(self, count, date):
        session = self.Session()
        session.query(Youtube_day_log).filter_by(
            id='count'
        ).update(
            {
                'count': count,
                'date': date
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
            player_requested=True,
            created=False,
            failed=False,
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
            failed=False,
            created=False,
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
            failed=False,
            created=False,
            status='ADDED'
        ).order_by(
            Replays.date_added.desc()
        ).first()
        session.close()

        return replay

    def update_failed_replay(self, challenge_id):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id
        ).update(
            {
                'failed': True
            }
        )
        session.commit()
        session.close()

    def update_created_replay(self, challenge_id):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id
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
            player_requested=True,
            failed=False,
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
            failed=False,
            created=True,
            video_processed=False
        ).all()
        return replays

    def set_replay_processed(self, challenge_id):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id
        ).update(
            {'video_processed': True, "date_added": datetime.datetime.now()}
        )
        session.commit()
        session.close()

    def set_youtube_uploaded(self, challenge_id, yt_bool):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id
        ).update(
            {'video_youtube_uploaded': yt_bool}
        )
        session.commit()
        session.close()

    def set_youtube_id(self, challenge_id, yt_id):
        session = self.Session()
        session.query(Replays).filter_by(
            id=challenge_id
        ).update(
            {'video_youtube_id': yt_id}
        )
        session.commit()
        session.close()

    def rerecord_replay(self, challenge_id):
        """Sets replay to be rerecorded
        """
        session = self.Session()
        # Set replay to original status
        session.query(Replays).filter_by(
            id=challenge_id
        ).update(
            {'failed': False, 'created': False, 'status': 'ADDED'}
        )
        session.commit()

        # Remove description if it exists
        session.query(Descriptions).filter_by(
            id=challenge_id
        ).delete()
        session.commit()

        # Remove job if it exists
        session.query(Job).filter_by(
            id=challenge_id
        ).delete()
        session.commit()

        # Remove character detection if it exists
        session.query(Character_detect).filter_by(
            challenge_id=challenge_id
        ).delete()
        session.commit()
        session.close()

    def delete_replay(self, challenge_id):
        session = self.Session()
        # Remove replay if it exists
        session.query(Replays).filter_by(
            id=challenge_id,
        ).delete()
        session.commit()

        # Remove description if it exists
        session.query(Descriptions).filter_by(
            id=challenge_id
        ).delete()
        session.commit()

        # Remove job if it exists
        session.query(Job).filter_by(
            id=challenge_id
        ).delete()
        session.commit()

        # Remove character detection if it exists
        session.query(Character_detect).filter_by(
            challenge_id=challenge_id
        ).delete()
        session.commit()

    def get_all_failed_replays(self, limit=10):
        session = self.Session()
        failed_replays = session.query(Replays).filter_by(
            failed=True,
        ).limit(limit).all()
        return failed_replays

    def get_all_finished_replays(self, limit=10):
        session = self.Session()
        replays = session.query(Replays).filter_by(
            failed=False,
            created=True
        ).limit(limit).all()
        return replays

    def get_all_queued_replays(self, limit=10):
        session = self.Session()
        replays = session.query(Replays).filter_by(
            failed=False,
            created=False
        ).limit(limit).all()
        return replays
