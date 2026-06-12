# noinspection PyPackageRequirements
import pytest
from pathlib import Path
import shutil


@pytest.fixture
def temp_dir(tmp_path):
    """Provides a temporary directory for tests."""
    d = tmp_path / "test_backup_root"
    d.mkdir()
    yield d


@pytest.fixture
def source_file(tmp_path):
    """Provides a temporary source file for tests."""
    f = tmp_path / "source.db"
    f.write_bytes(b"initial content")
    yield f
