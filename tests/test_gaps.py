import pytest
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from AutoBackupAJM import BasicAutoBackup


class TestBaseAndMixinsGaps:
    @pytest.fixture
    def setup_dirs(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("hello")
        backup_root = tmp_path / "backups"
        backup_root.mkdir()
        return source, backup_root

    def test_get_mrb_timestamp_zip(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        backup_root = tmp_path / "backups"
        backup_root.mkdir()
        
        # Create a directory backup that was unzipped
        backup_dir = backup_root / "20230101"
        backup_dir.mkdir(parents=True)
        backup_name_dir = backup_dir / "source"
        backup_name_dir.mkdir()
        
        # Create the corresponding zip file
        zip_file = backup_dir / "source.zip"
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr("file.txt", "hello")
        
        ab = BasicAutoBackup(source, backup_root)
        ab.original_source_is_zip = True
        
        # Mock most_recent_backup_file to return our backup_name_dir
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', 
                          new=(backup_name_dir, backup_name_dir.stat().st_ctime)):
            ts = ab._get_mrb_timestamp()
            assert ts == zip_file.stat().st_mtime

    def test_make_backup_dir_path_root_declined(self, source_file, tmp_path):
        backup_root = tmp_path / "non_existent_root"
        # We don't create it
        
        with patch('questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            ab = BasicAutoBackup(source_file, backup_root)
            # Setting it triggers the check
            ab.backup_dir_path_root = backup_root
            assert ab.backup_disabled is True

    def test_make_backup_dir_path_root_error(self, source_file, tmp_path):
        backup_root = tmp_path / "error_root"
        
        with patch('questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            with patch.object(Path, 'mkdir') as mock_mkdir:
                mock_mkdir.side_effect = OSError("Mocked Error")
                ab = BasicAutoBackup(source_file, backup_root)
                ab.backup_dir_path_root = backup_root
                assert ab.backup_disabled is True

    def test_copy_bytes_for_file_error(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("hello")
        backup_root = tmp_path / "backups"
        backup_root.mkdir()
        
        ab = BasicAutoBackup(source, backup_root)
        with patch('shutil.copy2', side_effect=shutil.Error("Copy failed")):
            with pytest.raises(shutil.Error):
                ab._write_backup_bytes_for_file()

    def test_copy_bytes_for_dir_error(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        with patch('shutil.copytree', side_effect=shutil.Error("Copytree failed")):
            with pytest.raises(shutil.Error):
                ab._write_backup_bytes_for_dir()

    def test_write_file_hash_with_backup_errors(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        ab.backup() # create full_backup_path
        
        hash_file = source / "hashes.txt"
        hash_file.write_text("hash123")
        
        # Test copy error (should log and return)
        with patch('shutil.copy2', side_effect=shutil.Error("Hash copy failed")):
            ab._write_file_hash_with_backup(hash_file)
            
        # Test hash_file_path is None
        ab._write_file_hash_with_backup(None)

    @pytest.mark.skip("feature is being implemented")
    def test_zip_and_clean_backup_not_implemented_cleanup(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        ab.backup()
        
        # This should log error because cleanup_backup_path=True is NotImplemented
        ab._zip_and_clean_backup(cleanup_backup_path=True)

    def test_log_methods(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        ab._log_attempted_backup()
        ab._log_no_backup_due()
        
        # To test _process_no_backup_due we need a backup to exist
        ab.backup()
        ab._process_no_backup_due()
        ab._eval_for_and_attempt_backup()

    def test_get_original_zip_mtime(self, tmp_path):
        zip_path = tmp_path / "test.zip"
        content = "test content"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", content)
        
        mtime = BasicAutoBackup._get_original_zip_mtime(zip_path, "test.txt")
        assert isinstance(mtime, datetime)

    def test_write_backup_bytes_not_found(self, tmp_path):
        source = tmp_path / "non_existent"
        backup_root = tmp_path / "backups"
        backup_root.mkdir()
        
        ab = BasicAutoBackup(source, backup_root)
        with patch.object(Path, 'is_file', return_value=False):
            with patch.object(Path, 'is_dir', return_value=False):
                with pytest.raises(FileNotFoundError):
                    ab._write_backup_bytes()

    def test_is_due_frequencies(self):
        # We need a dummy object with DATE_TODAY
        fixed_today = datetime(2023, 1, 1, 12, 0)
        
        class Dummy(_IsDueForBackupMixin):
            DATE_TODAY = fixed_today
            def full_backup_path(self): return Path()
            def backup_dir_path_root(self): return Path()
            def backup_dir_path_root(self, v): pass
            
        d = Dummy()
        d._logger = MagicMock()
        
        # Hourly - same day, different hour
        d.backup_frequency = 'hourly'
        assert d._is_due(datetime(2023, 1, 1, 11, 0)) is True
        assert d._is_due(datetime(2023, 1, 1, 12, 0)) is False
        
        # Weekly - same ISO week
        d.backup_frequency = 'weekly'
        assert d._is_due(datetime(2022, 12, 25)) is True
        # 2023-01-01 (Sunday) is week 52 of 2022 in ISO calendar
        # 2023-01-02 (Monday) is week 1 of 2023. So they ARE different weeks.
        # Let's use 2022-12-28 (Wednesday) which is same ISO week as 2023-01-01
        assert d._is_due(datetime(2022, 12, 28)) is False 
        
        # Monthly - different month
        d.backup_frequency = 'monthly'
        assert d._is_due(datetime(2022, 12, 1)) is True
        assert d._is_due(datetime(2023, 1, 15)) is False

    def test_no_backup_cleanup(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        
        # Create a mock backup file
        mrb = backup_root / "source"
        mrb.mkdir()
        
        with patch.object(BasicAutoBackup, 'most_recent_backup_file', new=(mrb, 123.0)):
            # original_source_is_zip = True and matches dir
            ab.original_source_is_zip = True
            ab._no_backup_cleanup()
            assert not mrb.exists()
            
            # Reset and test do_not_clean_up=True
            mrb.mkdir()
            ab._no_backup_cleanup(do_not_clean_up=True)
            assert mrb.exists()

    def test_overwrite_protection_check_raising(self, setup_dirs):
        source, backup_root = setup_dirs
        ab = BasicAutoBackup(source, backup_root)
        ab.backup() # Creates the dir
        
        # Now try to backup again without force_backup should raise FileExistsError
        with pytest.raises(FileExistsError, match="already exist"):
            ab._overwrite_protection_check()
            
        # With force_backup=True but declined in questionary
        ab.force_backup = True
        with patch('questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = False
            with pytest.raises(FileExistsError):
                ab._overwrite_protection_check()

from AutoBackupAJM._BaseAndMixins import _IsDueForBackupMixin
