import pytest
import json
from pathlib import Path
from AutoBackupAJM.Hasher.hash_recorder import HashRecorder, _Validators, _Recorder

class TestValidators:
    @pytest.fixture
    def validators(self):
        v = _Validators()
        # Mocking _logger since _Validators doesn't have it initialized in __init__
        from unittest.mock import MagicMock
        v._logger = MagicMock()
        return v

    def test_str_to_path(self, validators):
        assert validators._str_to_path("test") == Path("test")
        assert validators._str_to_path(Path("test")) == Path("test")
        with pytest.raises(TypeError):
            validators._str_to_path(123)

    def test_validate_file_name(self, validators):
        assert validators._validate_file_name("test.json") == Path("test.json")
        with pytest.raises(TypeError):
            validators._validate_file_name("test.txt")

    def test_validate_record_save_dir(self, validators, tmp_path):
        d = tmp_path / "new_dir"
        assert validators._validate_record_save_dir(d) == d
        assert d.is_dir()
        with pytest.raises(TypeError):
            validators._validate_record_save_dir(tmp_path / "file.txt")

class MockRecorder(HashRecorder):
    def __init__(self, hashes=None, **kwargs):
        super().__init__(**kwargs)
        self.hashes = hashes or []

    def hash_directory(self):
        for h in self.hashes:
            yield h

class TestHashRecorder:
    def test_hash_and_record_directory(self, tmp_path):
        save_dir = tmp_path / "hashes"
        file_name = "test_hashes.json"
        
        # We need to simulate some files.
        # Path.relative_to will be used.
        f1 = tmp_path / "file1.txt"
        f1.touch()
        
        recorder = MockRecorder(
            hashes=[(f1, "hash1")],
            record_save_dir=save_dir,
            file_name=file_name,
            input_path=tmp_path
        )
        
        records = recorder.hash_and_record_directory(relative_to=tmp_path, filename=file_name)
        
        assert "hash1" in records
        assert records["hash1"] == "file1.txt"
        
        # Check if file was written
        record_path = save_dir / file_name
        assert record_path.exists()
        with open(record_path, "r") as f:
            data = json.load(f)
        assert data == records

    def test_common_dir_filename(self, tmp_path):
        # Test if it automatically uses common directory name for filename
        d1 = tmp_path / "MyProject"
        d1.mkdir()
        f1 = d1 / "file1.txt"
        f1.touch()
        
        # If we DON'T specify file_name, it should use common dir name
        recorder = MockRecorder(
            hashes=[(f1, "hash1")],
            record_save_dir=tmp_path,
            input_path=d1
        )
        # We need to trigger common dir logic. _record_directory does it.
        # hash_and_record_directory calls _record_and_cleanup which calls _record_directory
        
        # By default _Recorder has a DEFAULT_FILE_NAME
        # But _validate_common_dir_filename might override it if filename is not passed to it.
        
        records = recorder.hash_and_record_directory(relative_to=d1)
        
        # The common path of [f1] relative to d1 is "file1.txt"
        # commonpath(["file1.txt"]) is "file1.txt" -> parent -> "."
        
        # Let's try multiple files in a subdir
        sub = d1 / "subdir"
        sub.mkdir()
        f2 = sub / "file2.txt"
        f2.touch()
        f3 = sub / "file3.txt"
        f3.touch()
        
        recorder = MockRecorder(
            hashes=[(f2, "hash2"), (f3, "hash3")],
            record_save_dir=tmp_path,
            input_path=d1
        )
        # records should be {"hash2": "subdir/file2.txt", "hash3": "subdir/file3.txt"}
        # common path of ["subdir/file2.txt", "subdir/file3.txt"] is "subdir"
        
        recorder.hash_and_record_directory(relative_to=d1)
        assert recorder.file_name == Path("subdir.json")
