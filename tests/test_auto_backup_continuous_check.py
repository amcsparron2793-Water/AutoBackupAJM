import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from AutoBackupAJM import BasicAutoBackupContinuousCheck, ExternalCompareContinuousCheck


@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "source.txt"
    f.write_text("initial content")
    return f


@pytest.fixture
def backup_dir(tmp_path):
    d = tmp_path / "backups"
    d.mkdir()
    return d


class TestBasicAutoBackupContinuousCheck:
    def test_init(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        assert abcc.not_due_notified is False
        assert abcc._logger.name == "BasicAutoBackupContinuousCheck"
        # Check if log_level_to_stream was set to ERROR by default in continuous check
        # Note: _setup_logger uses it, but we can't easily check the handler level without deeper inspection.
        # But we can verify it was passed to super().__init__ effectively.

    def test_log_intro_and_warnings(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        with patch.object(abcc._logger, 'info') as mock_info, \
                patch.object(abcc._logger, 'warning') as mock_warning:
            abcc._log_intro_and_warnings()
            assert mock_info.call_count == 2
            assert mock_warning.call_count == 2

    def test_monitor_loop(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        with patch.object(abcc, 'backup') as mock_backup, \
                patch.object(abcc, 'sleep') as mock_sleep:
            abcc._monitor_loop()
            mock_backup.assert_called_once()
            mock_sleep.assert_called_once_with(10)

    def test_process_no_backup_due(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        abcc.not_due_notified = False

        with patch.object(abcc, '_log_no_backup_due') as mock_log:
            abcc._process_no_backup_due()
            mock_log.assert_called_once()
            assert abcc.not_due_notified is True

            # Second call should not log again
            mock_log.reset_mock()
            abcc._process_no_backup_due()
            mock_log.assert_not_called()

    def test_attempt_backup_resets_notified(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        abcc.not_due_notified = True

        with patch('AutoBackupAJM._BaseAndMixins._BaseAutoBackup._attempt_backup') as mock_super_attempt:
            abcc._attempt_backup()
            assert abcc.not_due_notified is False
            mock_super_attempt.assert_called_once()

    def test_continuous_monitor_exit_on_interrupt(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        with patch.object(abcc, '_log_intro_and_warnings'), \
                patch.object(abcc, '_monitor_loop', side_effect=KeyboardInterrupt), \
                patch.object(abcc._logger, 'error') as mock_error:
            abcc.continuous_monitor()
            mock_error.assert_called_once_with("user interrupted backup process, exiting...")

    def test_sleep(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        with patch('AutoBackupAJM.auto_backup_continuous_check.sleep') as mock_time_sleep:
            abcc.sleep(5)
            mock_time_sleep.assert_called_once_with(5)

    def test_overrides(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        # Should not raise any error or do anything
        assert abcc._overwrite_protection_check() is None
        # Should always return True
        assert abcc._make_backup_dir_path_root_question(backup_dir) is True

    def test_process_no_backup_due_updates_date_today(self, source_file, backup_dir):
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir)
        # Set a past date
        past_date = datetime(2000, 1, 1)
        BasicAutoBackupContinuousCheck.DATE_TODAY = past_date

        abcc._process_no_backup_due()
        # Should be updated to today's date
        assert BasicAutoBackupContinuousCheck.DATE_TODAY.date() == datetime.today().date()

    def test_backup_is_due_and_becomes_due(self, source_file, backup_dir):
        # 1. Backup is due immediately (no previous backup)
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir, backup_frequency='daily')
        fixed_today = datetime(2026, 8, 24)
        BasicAutoBackupContinuousCheck.DATE_TODAY = fixed_today

        assert abcc.due_for_backup is True

        with patch.object(abcc, '_attempt_backup') as mock_attempt:
            abcc.backup()
            mock_attempt.assert_called_once()

        # 2. Backup is NOT due (backup just made today)
        # We need to ensure most_recent_backup_file reflects today
        # In a real scenario, backup() would create a file.
        # Let's actually perform a real backup for this test to be robust.
        abcc.backup()
        assert abcc.due_for_backup is False

        with patch.object(abcc, '_process_no_backup_due') as mock_no_due:
            abcc.backup()
            mock_no_due.assert_called_once()

        # 3. Backup becomes due after some time (simulated by moving DATE_TODAY forward)
        tomorrow = fixed_today + timedelta(days=1)
        BasicAutoBackupContinuousCheck.DATE_TODAY = tomorrow

        # We must also ensure source_changed_since_last_backup is True, 
        # because due_and_changed = due_for_backup AND source_changed_since_last_backup
        # In the test above, we made a backup, and source hasn't changed.
        # Let's modify the source.
        source_file.write_text("modified content")

        assert abcc.due_for_backup is True
        assert abcc.source_changed_since_last_backup is True
        
        with patch.object(abcc, '_attempt_backup') as mock_attempt_tomorrow:
            abcc.backup()
            mock_attempt_tomorrow.assert_called_once()

    def test_backup_becomes_due_without_source_change(self, source_file, backup_dir):
        # Even if source hasn't changed, if we use force_backup, it should backup.
        # But here we want to test if it DOES NOT backup if only due but NOT changed.
        abcc = BasicAutoBackupContinuousCheck(source_file, backup_dir, backup_frequency='daily')
        fixed_today = datetime(2026, 8, 24)
        BasicAutoBackupContinuousCheck.DATE_TODAY = fixed_today

        # Initial backup
        abcc.backup()
        assert abcc.due_for_backup is False

        # Move to tomorrow
        tomorrow = fixed_today + timedelta(days=1)
        BasicAutoBackupContinuousCheck.DATE_TODAY = tomorrow

        assert abcc.due_for_backup is True
        assert abcc.source_changed_since_last_backup is False

        # this is split like this since 3.8 doesn't support parenthetically split WITH expressions
        with patch.object(abcc, '_attempt_backup') as mock_attempt, \
             patch.object(abcc, '_process_no_backup_due') as mock_no_due:
            abcc.backup()
            mock_attempt.assert_not_called()
            mock_no_due.assert_called_once()


class TestExternalCompareContinuousCheck:
    def test_init(self, source_file, backup_dir):
        # We need to mock the external comparer because it might try to do real hash checks
        # or it might fail if MultiHasherMatchAJM is not properly set up in test env.
        # However, looking at auto_backup_ajm.py, it instantiates the comparer in __init__.

        with patch('AutoBackupAJM.auto_backup_ajm.ExternalCompareAutoBackup._get_comparer') as mock_get_comparer:
            mock_comparer = MagicMock()
            mock_get_comparer.return_value = mock_comparer

            eccc = ExternalCompareContinuousCheck(source_file, backup_dir)
            assert eccc._logger.name == eccc.__class__.__name__
            assert eccc.not_due_notified is False
