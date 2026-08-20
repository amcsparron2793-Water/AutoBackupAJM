import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory

from AutoBackupAJM.auto_backup_ajm import ExternalCompareAutoBackup, BasicAutoBackup


@pytest.fixture
def source_dir(tmp_path):
    d = tmp_path / "source_dir"
    d.mkdir()
    (d / "file1.txt").write_text("content1")
    return d


@pytest.fixture
def backup_root(tmp_path):
    d = tmp_path / "backups"
    d.mkdir()
    return d


class TestExternalCompareAutoBackup:
    def test_init(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)
        assert ecab.source_path == source_dir.resolve()
        assert ecab.backup_dir_path_root == backup_root.resolve()
        assert isinstance(ecab.comparer, ComparerFactory._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS)

    def test_source_changed_since_last_backup_no_backup(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)
        # most_recent_backup_file is None
        assert ecab.source_changed_since_last_backup is True

    def test_source_changed_since_last_backup_identical(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)
        ecab.backup()
        # After backup, they should be identical
        assert ecab.source_changed_since_last_backup is False

    def test_source_changed_since_last_backup_changed(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)
        ecab.backup()
        (source_dir / "file1.txt").write_text("changed content")
        assert ecab.source_changed_since_last_backup is True

    def test_get_comparer_type_error(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)
        with pytest.raises(TypeError, match="comparer_class must be callable"):
            ecab._get_comparer(comparer_class="not a callable")

    def test_get_comparer_fallback(self, source_dir, backup_root):
        # We want to trigger the try-except blocks in _get_comparer

        class MockComparerClass:
            def __init__(self, source, target, **kwargs):
                # First call might fail if it expects something else
                if isinstance(target, Path) and target.name != backup_root.name:
                    # Simulate failure when called with most_recent_backup_file[0]
                    raise TypeError("Simulated failure")
                self.source = source
                self.target = target

            def compare(self):
                return True

        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)

        # Manually set most_recent_backup_file using patch.object to trigger first attempt
        with patch.object(ExternalCompareAutoBackup, 'most_recent_backup_file',
                          new_callable=PropertyMock) as mock_recent:
            mock_recent.return_value = (Path("some_file"), 123.0)
            comparer = ecab._get_comparer(comparer_class=MockComparerClass)
            assert isinstance(comparer, MockComparerClass)
            # It should have failed the first attempt (with "some_file") and fallen back to backup_root
            assert comparer.target == backup_root.resolve()

    def test_external_compare_auto_backup_exit_on_error(self, source_dir, backup_root):
        ecab = ExternalCompareAutoBackup(source_path=source_dir, backup_dir_path_root=backup_root)

        # We need the first call to fail with TypeError (which it will if most_recent_backup_file is None)
        # And the second call to fail with ValueError to trigger exit(1)

        mock_factory = MagicMock()
        # Line 84 will fail with TypeError due to most_recent_backup_file=None
        # Line 88 will call mock_factory and must fail with ValueError to trigger exit(1)
        mock_factory.side_effect = [ValueError("Second fail")]

        with patch.object(ExternalCompareAutoBackup, 'most_recent_backup_file',
                          new_callable=PropertyMock) as mock_recent:
            mock_recent.return_value = None  # This will cause TypeError in line 84 anyway
            with pytest.raises(SystemExit) as cm:
                ecab._get_comparer(comparer_class=mock_factory)
            assert cm.value.code == 1


class TestBasicAutoBackupAdditional:
    def test_source_changed_since_last_backup_with_backup(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("hello")
        backup_root = tmp_path / "backups"
        backup_root.mkdir()

        ab = BasicAutoBackup(source_path=source, backup_dir_path_root=backup_root)
        ab.backup()

        assert ab.source_changed_since_last_backup is False

        source.write_text("world")
        assert ab.source_changed_since_last_backup is True
