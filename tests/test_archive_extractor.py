import pytest
import shutil
import zipfile
from pathlib import Path
from AutoBackupAJM.Hasher.archive_extractor import ArchiveExtractor


@pytest.fixture
def zip_archive(tmp_path):
    archive_path = tmp_path / "test.zip"
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "file1.txt").write_text("hello")
    (content_dir / "file2.txt").write_text("world")

    with zipfile.ZipFile(archive_path, 'w') as zipf:
        zipf.write(content_dir / "file1.txt", "file1.txt")
        zipf.write(content_dir / "file2.txt", "file2.txt")

    return archive_path


class TestArchiveExtractor:
    def test_init_default_extract_dir(self, zip_archive):
        extractor = ArchiveExtractor(zip_archive)
        expected_dir = (zip_archive.parent / zip_archive.stem).resolve()
        assert extractor.extract_dir == expected_dir

    def test_init_custom_extract_dir(self, zip_archive, tmp_path):
        custom_dir = tmp_path / "custom_extract"
        extractor = ArchiveExtractor(zip_archive, extract_dir=custom_dir)
        assert extractor.extract_dir == custom_dir.resolve()

    def test_extract_dir_setter_invalid(self, zip_archive, tmp_path):
        extractor = ArchiveExtractor(zip_archive)
        invalid_dir = tmp_path / "not_a_dir.txt"
        invalid_dir.touch()
        with pytest.raises(ValueError, match="extract_dir must be a directory, not a file"):
            extractor.extract_dir = invalid_dir

    def test_extract_archive_success(self, zip_archive, tmp_path):
        extract_to = tmp_path / "extracted"
        extractor = ArchiveExtractor(zip_archive, extract_dir=extract_to)
        returned_path = extractor.extract_archive()

        assert returned_path == extract_to.resolve()
        assert (extract_to / "file1.txt").exists()
        assert (extract_to / "file2.txt").exists()
        assert (extract_to / "file1.txt").read_text() == "hello"

    def test_extract_archive_invalid_file(self, tmp_path):
        not_an_archive = tmp_path / "not_archive.txt"
        not_an_archive.write_text("just some text")
        extractor = ArchiveExtractor(not_an_archive)
        with pytest.raises(ValueError, match="is not a valid archive file"):
            extractor.extract_archive()

    def test_archive_contents_property(self, zip_archive, tmp_path):
        extract_to = tmp_path / "contents_test"
        extractor = ArchiveExtractor(zip_archive, extract_dir=extract_to)
        # Before extraction, contents might be None if dir doesn't exist
        assert extractor.archive_contents is None

        extractor.extract_archive()
        contents = extractor.archive_contents
        assert contents is not None
        assert len(contents) == 2
        names = [f.name for f in contents]
        assert "file1.txt" in names
        assert "file2.txt" in names

    def test_validate_archive_extraction_fail(self, zip_archive, tmp_path):
        extract_to = tmp_path / "non_existent_after_extract"
        extractor = ArchiveExtractor(zip_archive, extract_dir=extract_to)
        # Manually trigger validation without extracting
        with pytest.raises(FileNotFoundError, match="does not exist"):
            extractor._validate_archive_extraction()
