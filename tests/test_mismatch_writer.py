import pytest
import json
from pathlib import Path
from AutoBackupAJM.Hasher.mismatch_writer import MismatchWriter

class TestMismatchWriter:
    @pytest.fixture
    def writer(self, tmp_path):
        return MismatchWriter(mismatch_file_location=tmp_path, append_timestamp_to_file_name=False)

    def test_init(self, writer, tmp_path):
        assert writer.mismatch_file_location == tmp_path
        assert writer.found_mismatch is False
        assert writer.mismatch_counter.value == 0
        assert writer.mismatch_dict == {}

    def test_found_mismatch_setter(self, writer):
        writer.found_mismatch = True
        assert writer.found_mismatch is True
        assert writer.mismatch_counter.value == 1
        
        with pytest.raises(TypeError):
            writer.found_mismatch = "not a bool"

    def test_mismatch_file_name_timestamp(self, tmp_path):
        writer = MismatchWriter(mismatch_file_location=tmp_path, append_timestamp_to_file_name=True)
        # It should contain a timestamp, so it won't be just "mismatches.json"
        assert writer.mismatch_file_name != "mismatches.json"
        assert "mismatches_" in writer.mismatch_file_name
        assert writer.mismatch_file_name.endswith(".json")

    def test_log_mismatch(self, writer):
        writer.mismatch_source = "source_path"
        writer.mismatch_target = "target_path"
        
        writer.log_mismatch("key1", "val1", "target_name")
        
        assert writer.found_mismatch is True
        assert writer.mismatch_counter.value == 1
        assert "key1" in writer.mismatch_dict
        assert writer.mismatch_dict["key1"]["value"] == "val1"
        assert writer.mismatch_dict["key1"]["source"] == "source_path"

    def test_write_mismatches(self, writer, tmp_path):
        writer.mismatch_source = "source.zip"
        writer.mismatch_target = "target.zip"
        writer.log_mismatch("file1", "hash1", "target")
        
        writer.write_mismatches()
        
        expected_path = tmp_path / writer.mismatch_file_name
        assert expected_path.exists()
        
        with open(expected_path, "r") as f:
            data = json.load(f)
        
        assert "file1" in data
        assert data["file1"]["value"] == "hash1"

    def test_source_target_type(self, writer):
        writer.mismatch_source = "source.zip"
        assert writer.source_type == "file"
        
        writer.mismatch_source = "source_dir"
        assert writer.source_type == "directory"
        
        writer.mismatch_target = "target.zip"
        assert writer.target_type == "file"
        
        writer.mismatch_target = "target_dir"
        assert writer.target_type == "directory"

    def test_source_target_type_error(self, writer):
        with pytest.raises(ValueError):
            _ = writer.source_type
        with pytest.raises(ValueError):
            _ = writer.target_type
