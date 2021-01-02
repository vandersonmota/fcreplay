from unittest.mock import patch
from fcreplay.tasker import Tasker


class TestTasker:
    @patch('fcreplay.tasker.Database')
    def tasker(self, database):
        t = Tasker()
        return t

    def test_check_for_replay(self, capsys):
        tasker = self.tasker()
        tasker.max_instances = 1

        with patch.object(Tasker, 'number_of_instances', return_value=1), capsys.disabled():
            assert tasker.check_for_replay() is False, 'Should return false when max_number_of_instances reached'

        with patch.object(Tasker, 'number_of_instances', return_value=0):
            with patch.object(Tasker, 'launch_fcreplay') as launch_fcreplay:
                tasker.db.get_oldest_player_replay.return_value = True
                assert tasker.check_for_replay() is True, 'Should return true'
                capture = capsys.readouterr()
                assert 'Found player replay' in capture.out, 'Should find player replay'
                assert launch_fcreplay.assert_called, 'Should launch fcreplay'

                tasker.db.get_oldest_player_replay.return_value = None
                tasker.db.get_oldest_replay.return_value = True
                assert tasker.check_for_replay() is True, 'Should return true'
                capture = capsys.readouterr()
                assert 'Found replay' in capture.out, 'Should find player replay'
                assert launch_fcreplay.assert_called, 'Should launch fcreplay'

                tasker.db.get_oldest_player_replay.return_value = None
                tasker.db.get_oldest_replay.return_value = None
                assert tasker.check_for_replay() is False, 'Should return false'
