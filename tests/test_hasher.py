import pytest
from pathlib import Path
from AutoBackupAJM.Hasher.custom_comparers import DirectoryToDirectoryComparer
from AutoBackupAJM.Hasher.custom_factory import CustomComparerFactory
from unittest.mock import patch, MagicMock

@pytest.fixture
def source_dir(tmp_path):
    d = tmp_path / "source_dir"
    d.mkdir()
    (d / "file1.txt").write_text("content1")
    (d / "file2.txt").write_text("content2")
    return d

@pytest.fixture
def target_dir(tmp_path):
    d = tmp_path / "target_dir"
    d.mkdir()
    return d

class TestDirectoryToDirectoryComparer:
    def test_init(self, source_dir, target_dir):
        comparer = DirectoryToDirectoryComparer(source_dir=source_dir, target_dir=target_dir)
        assert comparer.source_dir == source_dir
        assert comparer.target_dir == target_dir
        assert comparer._source_directory_hash is None

    def test_source_directory_hash(self, source_dir, target_dir):
        comparer = DirectoryToDirectoryComparer(source_dir=source_dir, target_dir=target_dir)
        h = comparer.source_directory_hash
        assert isinstance(h, dict)
        # DirectoryHasher returns {hash: rel_path}
        paths = list(h.values())
        assert any(p.endswith("file1.txt") for p in paths)
        assert any(p.endswith("file2.txt") for p in paths)
        assert comparer._source_directory_hash == h

    def test_compare_identical(self, source_dir, tmp_path):
        target_dir = tmp_path / "target_dir_identical"
        target_dir.mkdir()
        (target_dir / "file1.txt").write_text("content1")
        (target_dir / "file2.txt").write_text("content2")
        
        comparer = DirectoryToDirectoryComparer(source_dir=source_dir, target_dir=target_dir)
        # compare() returns True if they are identical (in MultiHasherMatchAJM logic usually)
        # Actually, let's check what it returns.
        # JsonToDirectoryComparer.compare() returns True if they match.
        assert comparer.compare() is True

    def test_compare_different(self, source_dir, target_dir):
        (target_dir / "file1.txt").write_text("different content")
        comparer = DirectoryToDirectoryComparer(source_dir=source_dir, target_dir=target_dir)
        assert comparer.compare() is False

    def test_delay_hashing(self, source_dir, target_dir):
        comparer = DirectoryToDirectoryComparer(source_dir=source_dir, target_dir=target_dir, delay_hashing=True)
        assert comparer.delay_hashing is True
        # trigger compare
        comparer.compare()
        assert comparer.delay_hashing is False

class TestCustomComparerFactory:
    def test_inst_comparer_class_directories(self, source_dir, target_dir):
        factory = CustomComparerFactory
        comparer = factory.inst_comparer_class(source=source_dir, target=target_dir)
        assert isinstance(comparer, DirectoryToDirectoryComparer)

    def test_inst_comparer_class_files(self, tmp_path):
        source_file = tmp_path / "source.txt"
        source_file.write_text("s")
        target_file = tmp_path / "target.txt"
        target_file.write_text("t")
        
        with patch('MultiHasherMatchAJM.MatchAndRecord.ComparerFactory.inst_comparer_class') as mock_inst:
            mock_inst.return_value = "default_comparer"
            factory = CustomComparerFactory
            comparer = factory.inst_comparer_class(source=source_file, target=target_file)
            assert comparer == "default_comparer"
            mock_inst.assert_called_once()

    def test_new_factory_instantiation(self, source_dir, target_dir):
        # CustomComparerFactory.__new__ returns an instance of a comparer
        comparer = CustomComparerFactory(source=source_dir, target=target_dir)
        assert isinstance(comparer, DirectoryToDirectoryComparer)
        assert hasattr(comparer, 'logger')

    def test_setup_logger(self):
        logger = CustomComparerFactory._setup_logger(name="TestLogger")
        assert logger.name == "AutoBackupLogger"

    def test_directory_src_targets_none(self, source_dir, tmp_path):
        target_file = tmp_path / "target.txt"
        target_file.write_text("t")
        factory = CustomComparerFactory
        # _directory_src_targets returns None if target is not a directory
        result = factory._directory_src_targets(source=source_dir, target=target_file)
        assert result is None
