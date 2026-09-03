import pytest
from pathlib import Path
import zipfile
from AutoBackupAJM.custom_compare_factory import AutoBackupComparerFactory, AutoBackupDirToDirComparer

class TestCustomCompareFactory:
    @pytest.fixture
    def setup_paths(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"
        target.mkdir()
        return source, target

    def test_inst_comparer_class_source_not_exists(self, tmp_path):
        source = tmp_path / "non_existent"
        target = tmp_path / "target"
        target.mkdir()
        
        with pytest.raises(FileNotFoundError, match="source file .* does not exist"):
            AutoBackupComparerFactory.inst_comparer_class(source, target)

    def test_detect_and_unzip_archive_no_zip(self, tmp_path):
        target = tmp_path / "target_dir"
        target.mkdir()
        
        result_path, was_unzipped = AutoBackupComparerFactory._detect_and_unzip_archive(target)
        
        assert result_path == target
        assert was_unzipped is False

    def test_detect_and_unzip_archive_with_zip(self, tmp_path):
        target_dir = tmp_path / "target_dir"
        zip_path = tmp_path / "target_dir.zip"
        
        # Create content to zip
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        test_file = content_dir / "test.txt"
        test_file.write_text("hello")
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(test_file, arcname="test.txt")
        
        # Run
        result_path, was_unzipped = AutoBackupComparerFactory._detect_and_unzip_archive(target_dir)
        
        # Verify
        assert was_unzipped is True
        assert result_path == target_dir
        assert result_path.is_dir()
        assert (result_path / "test.txt").exists()
        assert (result_path / "test.txt").read_text() == "hello"

    def test_directory_src_targets_none_when_not_dir(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target_file.txt"
        target.write_text("not a directory")
        
        comparer = AutoBackupComparerFactory._directory_src_targets(source, target)
        assert comparer is None

    def test_directory_src_targets_creation(self, setup_paths):
        source, target = setup_paths
        
        comparer = AutoBackupComparerFactory._directory_src_targets(source, target)
        
        assert isinstance(comparer, AutoBackupDirToDirComparer)
        assert comparer.source_dir == source
        assert comparer.target_dir == target
        assert comparer.original_source_is_zip is False

    def test_directory_src_targets_with_unzip(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        
        target_dir = tmp_path / "target_dir"
        zip_path = tmp_path / "target_dir.zip"
        
        # Create zip
        content_dir = tmp_path / "content"
        content_dir.mkdir()
        (content_dir / "file.txt").write_text("data")
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(content_dir / "file.txt", arcname="file.txt")
            
        comparer = AutoBackupComparerFactory._directory_src_targets(source, target_dir)
        
        assert isinstance(comparer, AutoBackupDirToDirComparer)
        assert comparer.target_dir == target_dir
        assert comparer.original_source_is_zip is True
        assert (target_dir / "file.txt").exists()

    def test_auto_backup_dir_to_dir_comparer_init(self, setup_paths):
        source, target = setup_paths
        comparer = AutoBackupDirToDirComparer(source, target, original_source_is_zip=True)
        
        assert comparer.original_source_is_zip is True
        assert comparer.logger.name == "AutoBackupDirToDirComparer"
