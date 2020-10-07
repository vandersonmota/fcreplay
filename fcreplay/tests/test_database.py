import pytest
import sys
from unittest.mock import patch, MagicMock

sys.modules['pyautogui'] = MagicMock()
from fcreplay.database import Database


class TestDatabase:
    @patch('fcreplay.logging.Config')
    @patch('fcreplay.database.create_engine')
    @patch('fcreplay.database.func')
    @patch('fcreplay.database.Config')
    def setUp(self, mock_config, mock_func, mock_create_engine, mock_logging_config):
        db = Database()
        assert mock_create_engine.called, 'Database should call create_engine'

        mock_create_engine.side_effect = Exception
        with pytest.raises(Exception) as e:
            db = Database()
            assert e is Exception, 'Database should raise exception when __init__ fails'

        return db

    @patch('fcreplay.database.sessionmaker')
    def test_db_session(self, mock_session):
        db = self.setUp()
        db.add_replay(
            challenge_id=MagicMock(),
            p1_loc=MagicMock(),
            p2_loc=MagicMock(),
            p1_rank=MagicMock(),
            p2_rank=MagicMock(),
            p1=MagicMock(),
            p2=MagicMock(),
            date_replay=MagicMock(),
            length=MagicMock(),
            created=MagicMock(),
            failed=MagicMock(),
            status=MagicMock(),
            date_added=MagicMock(),
            player_requested=MagicMock(),
            game=MagicMock(),
            emulator=MagicMock(),
            video_processed=MagicMock()
        )

        db.get_single_replay(challenge_id=MagicMock())
        db.update_player_requested(challenge_id=MagicMock())
        db.add_detected_characters(
            challenge_id=MagicMock(),
            p1_char=MagicMock(),
            p2_char=MagicMock(),
            vid_time=MagicMock()
        )
        db.add_job(
            challenge_id=MagicMock(),
            start_time=MagicMock(),
            length=MagicMock()
        )
        db.remove_job(challenge_id=MagicMock())
        db.get_job(challenge_id=MagicMock())
        db.get_job_count()
        db.update_status(
            challenge_id=MagicMock(),
            status=MagicMock(),
        )
        db.add_description(
            challenge_id=MagicMock(),
            description=MagicMock()
        )
        db.update_youtube_day_log_count(
            count=MagicMock(),
            date=MagicMock()
        )
        db.get_youtube_day_log()
        db.get_oldest_player_replay()
        db.get_random_replay()
        db.get_oldest_replay()
        db.update_failed_replay(
            challenge_id=MagicMock()
        )
        db.update_created_replay(
            challenge_id=MagicMock()
        )
        db.get_all_queued_player_replays()
        db.get_unprocessed_replays()
        db.set_replay_processed(challenge_id=MagicMock())
        db.rerecord_replay(challenge_id=MagicMock())

        assert mock_session.called, 'Database functions should complete'
