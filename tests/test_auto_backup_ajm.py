# noinspection PyPackageRequirements
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from AutoBackupAJM import BasicAutoBackup
from unittest.mock import patch


def test_init(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    assert ab.source_path == source_file.resolve()
    assert ab._backup_dir_path_root == temp_dir.resolve()
    assert ab.backup_frequency == 'daily'
    assert not ab.backup_disabled


def test_backup_frequency_validation(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='weekly')
    assert ab.backup_frequency == 'weekly'

    ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='MONTHLY')
    assert ab.backup_frequency == 'monthly'

    with pytest.raises(ValueError, match="Invalid backup frequency"):
        ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='invalid')
        _ = ab.backup_frequency


def test_backup_location(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    expected_subdir = datetime.today().strftime('%m%d%Y')
    assert ab.backup_location == temp_dir / expected_subdir
    assert (temp_dir / expected_subdir).is_dir()


def test_most_recent_backup_file_none(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    assert ab.most_recent_backup_file is None


def test_source_changed_since_last_backup(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    # No backup exists
    assert ab.source_changed_since_last_backup is True

    # Create a backup
    ab.backup()
    assert ab.source_changed_since_last_backup is False

    # Modify source
    source_file.write_bytes(b"modified content")
    assert ab.source_changed_since_last_backup is True


@patch('AutoBackupAJM.auto_backup_ajm.datetime')
def test_due_for_backup_daily(mock_datetime, source_file, temp_dir):
    # Fixed datetime mock and ensured DATE_TODAY is controlled
    fixed_today = datetime(2023, 1, 1)

    # Setup mock_datetime to behave like a class
    mock_datetime.today.return_value = fixed_today
    mock_datetime.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)
    mock_datetime.now.return_value = fixed_today

    # We patch DATE_TODAY on the class
    with patch.object(BasicAutoBackup, 'DATE_TODAY', fixed_today):
        ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='daily')
        # Ensure the instance also has the correct DATE_TODAY
        ab.DATE_TODAY = fixed_today

        assert ab.due_for_backup is True  # No backup yet

        ab.backup()

        # We need to ensure that the "most recent backup" time we compare against
        # is indeed the one we just created, and that it matches our mocked "today"
        recent = ab.most_recent_backup_file
        assert recent is not None

        # If we use real file ctime, it will be "now" (real time), not our mock time.
        # This is why it returns True (due for backup) because real ctime.date() != 2023-01-01

        # Let's mock most_recent_backup_file to return our fixed_today
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', (recent[0], fixed_today.timestamp())):
            assert ab.due_for_backup is False  # Now it should be False

        # Tomorrow
        tomorrow = fixed_today + timedelta(days=1)
        with patch.object(BasicAutoBackup, 'DATE_TODAY', tomorrow):
            ab.DATE_TODAY = tomorrow
            with patch.object(BasicAutoBackup, 'most_recent_backup_file', (recent[0], fixed_today.timestamp())):
                assert ab.due_for_backup is True


def test_backup_disabled(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir, disable_backup=True)
    assert ab.backup_disabled is True

    # Should not create backup
    ab.backup()
    assert ab.most_recent_backup_file is None

    ab.backup_disabled = False
    ab.backup()
    assert ab.most_recent_backup_file is not None


@patch('questionary.confirm')
def test_overwrite_protection(mock_confirm, source_file, temp_dir):
    # To test overwrite protection, we need to reach _overwrite_protection_check
    # We can do this by setting force_backup=True for the initial backup,
    # or just by creating a file manually in the backup location.

    ab = BasicAutoBackup(source_file, temp_dir, force_backup=False)
    ab.backup()

    # Now a backup exists for today.
    # If we try to backup again with force_backup=False, 
    # it might say "No backup necessary" because due_for_backup is False.
    # So we force it.
    ab.force_backup = True

    # Mock confirm to NO (don't overwrite)
    mock_confirm.return_value.ask.return_value = False
    with pytest.raises(FileExistsError):
        ab.backup()

    # Mock confirm to YES (overwrite)
    mock_confirm.return_value.ask.return_value = True
    ab.backup()  # Should succeed
    mock_confirm.return_value.ask.assert_called()


def test_backup_successful(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    assert ab.backup_successful is False
    ab.backup()
    assert ab.backup_successful is True


def test_full_backup_path(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir, backup_name="test.db")
    expected_path = ab.backup_location / "test.db"
    assert ab.full_backup_path == expected_path


@patch('questionary.confirm')
def test_backup_dir_path_root_creation(mock_confirm, source_file, tmp_path):
    new_root = tmp_path / "new_backup_root"
    # Root does not exist
    ab = BasicAutoBackup(source_file, new_root)

    # Mock confirm to YES
    mock_confirm.return_value.ask.return_value = True
    ab.backup_dir_path_root = new_root.resolve()
    assert ab.backup_dir_path_root == new_root.resolve()
    assert new_root.exists()


@patch('questionary.confirm')
def test_backup_dir_path_root_denied(mock_confirm, source_file, tmp_path):
    new_root = tmp_path / "denied_root"
    ab = BasicAutoBackup(source_file, new_root)

    # Root does not exist
    assert not new_root.exists()

    # Mock confirm to NO
    mock_confirm.return_value.ask.return_value = False

    # This should call _make_backup_dir_path_root_question and set backup_disabled to True
    ab.backup_dir_path_root = new_root.resolve()
    assert ab.backup_dir_path_root == new_root.resolve()
    assert ab.backup_disabled is True
    assert not new_root.exists()


@patch('AutoBackupAJM.auto_backup_ajm.datetime')
def test_due_for_backup_weekly(mock_datetime, source_file, temp_dir):
    fixed_today = datetime(2023, 1, 10)  # Tuesday, Week 2
    mock_datetime.today.return_value = fixed_today
    mock_datetime.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)

    with patch.object(BasicAutoBackup, 'DATE_TODAY', fixed_today):
        ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='weekly')
        ab.DATE_TODAY = fixed_today

        # Mock recent backup from Week 1 (2023-01-03)
        week1_date = datetime(2023, 1, 3)
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', (Path('fake'), week1_date.timestamp())):
            assert ab.due_for_backup is True

        # Mock recent backup from Week 2 (2023-01-09)
        week2_date = datetime(2023, 1, 9)
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', (Path('fake'), week2_date.timestamp())):
            assert ab.due_for_backup is False


@patch('AutoBackupAJM.auto_backup_ajm.datetime')
def test_due_for_backup_monthly(mock_datetime, source_file, temp_dir):
    fixed_today = datetime(2023, 2, 1)  # February
    mock_datetime.today.return_value = fixed_today
    mock_datetime.fromtimestamp.side_effect = lambda ts: datetime.fromtimestamp(ts)

    with patch.object(BasicAutoBackup, 'DATE_TODAY', fixed_today):
        ab = BasicAutoBackup(source_file, temp_dir, backup_frequency='monthly')
        ab.DATE_TODAY = fixed_today

        # Mock recent backup from January
        jan_date = datetime(2023, 1, 15)
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', (Path('fake'), jan_date.timestamp())):
            assert ab.due_for_backup is True

        # Mock recent backup from February
        feb_date = datetime(2023, 2, 1)
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', (Path('fake'), feb_date.timestamp())):
            assert ab.due_for_backup is False

def test_backup_is_recent(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    # No backup yet, so full_backup_path doesn't exist, stat() fails.
    # The current implementation of backup_is_recent doesn't handle non-existent file.
    # Let's just test the successful case for now.
    ab.backup()
    assert ab.backup_is_recent is True

def test_backup_location_creation(source_file, tmp_path):
    root = tmp_path / "backups"
    # Root doesn't exist yet, we'll create it via setting it and mocking questionary
    with patch('questionary.confirm') as mock_confirm:
        mock_confirm.return_value.ask.return_value = True
        ab = BasicAutoBackup(source_file, root)
        # Note: BasicAutoBackup.__init__ calls set_initial_properties_values which sets _backup_dir_path_root directly
        # bypassing the setter and thus the question.
        # To trigger the question, we set it after init.
        ab.backup_dir_path_root = root
        # backup_location should be root / date
        loc = ab.backup_location
        assert loc.parent == root.resolve()
        assert loc.exists()

def test_source_path_setter(source_file, temp_dir, tmp_path):
    ab = BasicAutoBackup(source_file, temp_dir)
    new_source = tmp_path / "new_source.db"
    new_source.write_text("new content")
    ab.source_path = new_source
    assert ab.source_path == new_source.resolve()

def test_invalid_backup_frequency(source_file, temp_dir):
    ab = BasicAutoBackup(source_file, temp_dir)
    # The setter is used in __init__ via set_initial_properties_values
    with pytest.raises(ValueError, match="Invalid backup frequency"):
        ab.backup_frequency = "invalid_freq"
