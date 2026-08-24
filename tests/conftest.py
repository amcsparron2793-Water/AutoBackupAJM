from pathlib import Path

# noinspection PyPackageRequirements
import pytest

from EasyLoggerAJM import SetupLogger
from AutoBackupAJM.auto_backup_logger import AutoBackupLogger

TEST_LOGS_PROJECT_NAME = 'TestLogs'
TEST_LOGS_ROOT_LOG_LOCATION = Path(AutoBackupLogger.ROOT_LOG_LOCATION_DEFAULT / TEST_LOGS_PROJECT_NAME)


@pytest.fixture(autouse=True)
def disable_logger_console_output(monkeypatch):
    original_setup_logger = SetupLogger.setup_logger

    def setup_logger_without_console(**kwargs):
        kwargs.setdefault("show_warning_logs_in_console", False)
        kwargs.setdefault('project_name', TEST_LOGS_PROJECT_NAME)
        kwargs.setdefault('root_log_location', TEST_LOGS_ROOT_LOG_LOCATION)
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
