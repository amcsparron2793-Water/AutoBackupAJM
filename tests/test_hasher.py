import pytest
from pathlib import Path
import hashlib
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher
from AutoBackupAJM.Hasher.factory import HasherFactory
from AutoBackupAJM.Hasher.other_hashers import ArchiveHasher

@pytest.fixture
def temp_file(tmp_path):
    f = tmp_path / "test_file.txt"
    content = b"hello world"
    f.write_bytes(content)
    expected_hash = hashlib.md5(content).hexdigest()
    return f, expected_hash

@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    f1 = d / "file1.txt"
    f1.write_bytes(b"content1")
    f2 = d / "file2.txt"
    f2.write_bytes(b"content2")
    sub = d / "subdir"
    sub.mkdir()
    f3 = sub / "file3.txt"
    f3.write_bytes(b"content3")
    return d

class TestFileHasher:
    def test_init(self, temp_file):
        path, _ = temp_file
        hasher = FileHasher(path)
        assert hasher.input_path == path
        
        hasher_str = FileHasher(str(path))
        assert hasher_str.input_path == path

    def test_init_invalid_type(self):
        with pytest.raises(TypeError, match="input_path must be a string or a Path object"):
            FileHasher(123)

    def test_hash_file(self, temp_file):
        path, expected_hash = temp_file
        hasher = FileHasher(path)
        returned_path, h = hasher.hash_file()
        assert returned_path == path.resolve()
        assert h == expected_hash

    def test_hash_file_with_str_return(self, temp_file):
        path, expected_hash = temp_file
        hasher = FileHasher(path)
        returned_path, h = hasher.hash_file(return_path=False)
        assert isinstance(returned_path, str)
        assert returned_path == path.resolve().as_posix()
        assert h == expected_hash

    def test_hash_file_not_a_file(self, tmp_path):
        d = tmp_path / "not_a_file"
        d.mkdir()
        hasher = FileHasher(d)
        with pytest.raises(ValueError, match="self.input_path must be a file"):
            hasher.hash_file()

class TestLargeFileHasher:
    def test_init_and_warnings(self, temp_file, capsys):
        path, _ = temp_file
        # LargeFileHasher warns if buffer_size or file_size is small
        # WARNING_BUFFER_SIZE is 1GB // 2 = 512MB
        # By default, buffer_size for LargeFileHasher is 1GB, which is > WARNING_BUFFER_SIZE
        # So only input_file_size warning should appear for small file
        hasher = LargeFileHasher(path)
        captured = capsys.readouterr()
        assert "Warning: LargeFileHasher input_file_size is too small" in captured.out
        assert hasattr(hasher, 'input_file_size')

    def test_init_buffer_size_warning(self, temp_file, capsys):
        path, _ = temp_file
        # Force small buffer size to trigger warning
        hasher = LargeFileHasher(path, buffer_size=1024)
        captured = capsys.readouterr()
        assert "Warning: LargeFileHasher buffer_size is too small" in captured.out

class TestDirectoryHasher:
    def test_hash_directory(self, temp_dir):
        hasher = DirectoryHasher(temp_dir)
        results = list(hasher.hash_directory())
        # Should have 2 files, subdir should be skipped
        assert len(results) == 2
        paths = [r[0] for r in results]
        assert (temp_dir / "file1.txt").resolve() in paths
        assert (temp_dir / "file2.txt").resolve() in paths

    def test_hash_directory_invalid(self, temp_file):
        path, _ = temp_file
        hasher = DirectoryHasher(path)
        with pytest.raises(ValueError, match="self.input_path must be a directory"):
            list(hasher.hash_directory())

class TestHasherFactory:
    def test_factory_file(self, temp_file):
        path, _ = temp_file
        hasher = HasherFactory(input_path=path)
        assert isinstance(hasher, FileHasher)
        # Since it's a small file, it should be FileHasher, not LargeFileHasher

    def test_factory_directory(self, temp_dir):
        hasher = HasherFactory(input_path=temp_dir)
        assert isinstance(hasher, DirectoryHasher)

    def test_factory_invalid_path(self, tmp_path):
        non_existent = tmp_path / "non_existent"
        with pytest.raises(ValueError, match="input_path must be a file or directory"):
            HasherFactory(input_path=non_existent)

    def test_factory_no_input(self):
        with pytest.raises(ValueError, match="Must specify input_path"):
            HasherFactory()

class TestArchiveHasher:
    def test_init_archive(self, tmp_path):
        archive = tmp_path / "test.zip"
        archive.write_bytes(b"some zip content")
        hasher = ArchiveHasher(archive)
        assert hasher.input_path == archive

    def test_init_not_archive(self, temp_file):
        path, _ = temp_file
        with pytest.raises(ValueError, match="input_path must be an archive file"):
            ArchiveHasher(path)
