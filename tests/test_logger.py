import pytest
import logging
from AutoBackupAJM.auto_backup_logger import AutoBackupLogger


class TestAutoBackupLogger:
    def test_init(self):
        abl = AutoBackupLogger()
        logger = abl()
        assert logger.name == "AutoBackupLogger"
        # Check some default kwargs
        # EasyLogger sets up handlers, we can check if it has any
        assert logger.hasHandlers()

    def test_call_returns_logger(self):
        abl = AutoBackupLogger()
        logger = abl()
        assert isinstance(logger, logging.Logger)
