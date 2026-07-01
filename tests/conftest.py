# noinspection PyPackageRequirements
import pytest

from AutoBackupAJM import SetupLogger


@pytest.fixture(autouse=True)
def disable_logger_console_output(monkeypatch):
    original_setup_logger = SetupLogger.setup_logger

    def setup_logger_without_console(**kwargs):
        kwargs.setdefault("show_warning_logs_in_console", False)
        return original_setup_logger(**kwargs)

    monkeypatch.setattr(
        SetupLogger,
        "setup_logger",
        setup_logger_without_console,
    )


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
