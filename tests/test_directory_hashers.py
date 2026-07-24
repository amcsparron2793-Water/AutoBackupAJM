import pytest
from pathlib import Path
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher, LargeDirectoryHasher

class TestDirectoryHasher:
    @pytest.fixture
    def test_dir(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        (d / "file1.txt").write_text("content1")
        (d / "file2.txt").write_text("content2")
        sub = d / "subdir"
        sub.mkdir()
        (sub / "file3.txt").write_text("content3")
        return d

    def test_init(self, test_dir):
        dh = DirectoryHasher(test_dir)
        assert dh.input_path == test_dir
        assert dh.ignore_system_dirs is True

    def test_validate_input_path(self, tmp_path):
        f = tmp_path / "file.txt"
        f.touch()
        dh = DirectoryHasher(tmp_path) # input_path must exist
        dh.input_path = f
        with pytest.raises(ValueError):
            dh._validate_input_path_is_dir()

    def test_walk_directory(self, test_dir):
        dh = DirectoryHasher(test_dir)
        files = list(dh._walk_directory(test_dir))
        # Should find 3 files
        assert len(files) == 3
        filenames = [f.name for f in files]
        assert "file1.txt" in filenames
        assert "file2.txt" in filenames
        assert "file3.txt" in filenames

    def test_hash_directory(self, test_dir):
        dh = DirectoryHasher(test_dir)
        hashes = list(dh.hash_directory())
        assert len(hashes) == 3
        for path, h in hashes:
            assert isinstance(path, Path)
            assert isinstance(h, str)
            assert len(h) == 32 # md5 hexdigest

    def test_hash_and_record_directory(self, test_dir, tmp_path):
        save_dir = tmp_path / "records"
        file_name = "custom_record.json"
        dh = DirectoryHasher(test_dir, record_save_dir=save_dir, file_name=file_name)
        records = dh.hash_and_record_directory(relative_to=test_dir, filename=file_name)
        
        assert len(records) == 3
        assert (save_dir / file_name).exists()

    def test_ignore_system_dirs(self, test_dir):
        # SYSTEM_DIR_PREFIXES = ['.', '__', 'venv']
        system_dir = test_dir / ".hidden"
        system_dir.mkdir()
        (system_dir / "trash.txt").write_text("trash")
        
        dh = DirectoryHasher(test_dir, ignore_system_dirs=True)
        files = list(dh._walk_directory(test_dir))
        filenames = [f.name for f in files]
        assert "trash.txt" not in filenames
        
        dh_no_ignore = DirectoryHasher(test_dir, ignore_system_dirs=False)
        files_all = list(dh_no_ignore._walk_directory(test_dir))
        filenames_all = [f.name for f in files_all]
        assert "trash.txt" in filenames_all

class TestLargeDirectoryHasher:
    @pytest.fixture
    def test_dir_large(self, tmp_path):
        d = tmp_path / "data_large"
        d.mkdir()
        (d / "file1.txt").write_text("content1")
        return d

    def test_init(self, test_dir_large):
        # LargeFileHasher (parent of LargeDirectoryHasher) calls stat().st_size on input_path
        # and compares it with WARNING_BUFFER_SIZE (512MB)
        ldh = LargeDirectoryHasher(test_dir_large)
        assert ldh.input_path == test_dir_large
        # Since test_dir size is small, it should have logged a warning, 
        # but we just check if it initialized correctly.
        assert ldh.buffer_size == 1024**3 # 1GB
