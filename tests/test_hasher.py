# noinspection PyPackageRequirements
import pytest
import hashlib
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher
from AutoBackupAJM.Hasher.factory import HasherFactory
from AutoBackupAJM.Hasher.archive_hashers import ArchiveFileHasher, ArchiveDirectoryHasher
import zipfile


@pytest.fixture
def zip_archive(tmp_path):
    archive_path = tmp_path / "test.zip"
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "file_in_zip.txt").write_text("hello in zip")

    with zipfile.ZipFile(archive_path, 'w') as zipf:
        zipf.write(content_dir / "file_in_zip.txt", "file_in_zip.txt")

    return archive_path


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
    def test_init_and_warnings(self, temp_file, caplog):
        path, _ = temp_file
        # LargeFileHasher warns if buffer_size or file_size is small
        # WARNING_BUFFER_SIZE is 1GB // 2 = 512MB
        # By default, buffer_size for LargeFileHasher is 1GB, which is > WARNING_BUFFER_SIZE
        # So only input_file_size warning should appear for small file
        hasher = LargeFileHasher(path)
        captured = caplog.text
        assert "Warning: LargeFileHasher input_file_size is too small" in captured
        assert hasattr(hasher, 'input_file_size')

    def test_init_buffer_size_warning(self, temp_file, caplog):
        path, _ = temp_file
        # Force small buffer size to trigger warning
        hasher = LargeFileHasher(path, buffer_size=1024)
        captured = caplog.text
        assert "Warning: LargeFileHasher buffer_size is too small" in captured


class TestDirectoryHasher:
    def test_hash_directory(self, temp_dir):
        hasher = DirectoryHasher(temp_dir)
        results = list(hasher.hash_directory())
        # Should have 3 files including the one in subdir
        assert len(results) == 3
        paths = [r[0] for r in results]
        assert (temp_dir / "file1.txt").resolve() in paths
        assert (temp_dir / "file2.txt").resolve() in paths
        assert (temp_dir / "subdir" / "file3.txt").resolve() in paths

    def test_hash_directory_invalid(self, temp_file):
        path, _ = temp_file
        hasher = DirectoryHasher(path)
        with pytest.raises(ValueError, match="self.input_path must be a directory"):
            list(hasher.hash_directory())


class TestHasherFactory:
    def test_factory_file(self, temp_file):
        path, _ = temp_file
        # Set WARNING_BUFFER_SIZE to a small value to trigger LargeFileHasher if needed,
        # but here we want to test that a small file gets FileHasher.
        hasher = HasherFactory(input_path=path)
        assert isinstance(hasher, FileHasher)
        assert not isinstance(hasher, LargeFileHasher)

    def test_factory_large_file(self, tmp_path, monkeypatch):
        # Mock WARNING_BUFFER_SIZE to be very small
        monkeypatch.setattr(LargeFileHasher, "WARNING_BUFFER_SIZE", 0)
        path = tmp_path / "large_file.txt"
        path.write_bytes(b"large content")
        hasher = HasherFactory(input_path=path)
        assert isinstance(hasher, LargeFileHasher)

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


class TestArchiveFileHasher:
    def test_init_archive(self, zip_archive):
        hasher = ArchiveFileHasher(zip_archive)
        assert hasher.input_path == zip_archive

    def test_init_not_archive(self, temp_file):
        path, _ = temp_file
        with pytest.raises(ValueError, match="input_path must be an archive file"):
            ArchiveFileHasher(path)

    def test_hash_archive_as_file(self, zip_archive):
        hasher = ArchiveFileHasher(zip_archive)
        results = hasher.hash_archive(unzip_and_hash_contents=False)
        assert isinstance(results, dict)
        assert list(results.values())[0] == zip_archive.resolve()
        assert list(results.keys())[0] == hashlib.md5(zip_archive.read_bytes()).hexdigest()

    def test_hash_archive_unzip_single_file(self, zip_archive, tmp_path):
        extract_dir = tmp_path / "manual_extract"
        hasher = ArchiveFileHasher(zip_archive, extract_dir=extract_dir)
        # ArchiveFileHasher._hash_contents calls _handle_path if extract_dir is a Path
        # and _handle_path raises AttributeError if it's a directory
        with pytest.raises(AttributeError, match="use ArchiveDirectoryHasher to hash the contents of this directory"):
            hasher.hash_archive(unzip_and_hash_contents=True)

    def test_is_single_file_list(self, tmp_path):
        f1 = tmp_path / "f1.txt"
        f1.touch()
        f2 = tmp_path / "f2.txt"
        f2.touch()
        
        is_list, is_single = ArchiveFileHasher.is_single_file_list([f1])
        assert is_list is True
        assert is_single is True
        
        is_list, is_single = ArchiveFileHasher.is_single_file_list([f1, f2])
        assert is_list is True
        assert is_single is False
        
        is_list, is_single = ArchiveFileHasher.is_single_file_list("not a list")
        assert is_list is False
        assert is_single is False


class TestArchiveDirectoryHasher:
    def test_hash_archive_unzip_directory(self, zip_archive, tmp_path):
        # Even if it's a single file, ArchiveDirectoryHasher should handle it as a directory
        extract_dir = tmp_path / "dir_extract"
        hasher = ArchiveDirectoryHasher(zip_archive, extract_dir=extract_dir)
        # ArchiveDirectoryHasher.hash_archive returns a dict if unzip_and_hash_contents=True
        results = hasher.hash_archive(unzip_and_hash_contents=True)

        assert isinstance(results, dict)
        assert len(results) == 1

        expected_hash = hashlib.md5(b"hello in zip").hexdigest()
        assert expected_hash in results
        assert results[expected_hash] == "dir_extract/file_in_zip.txt"
