import pytest
import logging
from AutoBackupAJM.auto_backup_logger import AutoBackupLogger, SetupLogger

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

class TestSetupLogger:
    def test_instantiation_raises_type_error(self):
        with pytest.raises(TypeError, match="SetupLogger cannot be instantiated"):
            SetupLogger()

    def test_setup_logger_default(self):
        logger = SetupLogger.setup_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "AutoBackupLogger"

    def test_setup_logger_custom_name(self):
        # If we don't pass a logger, it uses AutoBackupLogger which defaults to 'AutoBackupLogger'
        # But _check_fallback_logger_config uses default_logger_name if no logger passed to it.
        # Actually SetupLogger.setup_logger calls AutoBackupLogger(**kwargs)() if no logger.
        logger = SetupLogger.setup_logger(project_name="TestProject")
        # AutoBackupLogger sets logger.name = self.__class__.__name__ (AutoBackupLogger)
        assert logger.name == "AutoBackupLogger"

    def test_check_fallback_logger_config_with_logger(self):
        custom_logger = logging.getLogger("Custom")
        logger = SetupLogger._check_fallback_logger_config(logger=custom_logger)
        assert logger == custom_logger
        assert logger.name == "Custom"

    def test_check_fallback_logger_config_no_handlers(self):
        # Create a logger with no handlers
        no_handler_logger = logging.getLogger("NoHandlersUnique5")
        no_handler_logger.handlers = []
        no_handler_logger.propagate = False
        
        # We need to mock hasHandlers to return False because pytest adds handlers
        import unittest.mock as mock
        # We MUST mock AutoBackupAJM.auto_backup_logger.basicConfig because it was imported with 'from'
        with mock.patch("AutoBackupAJM.auto_backup_logger.basicConfig") as mock_basic_config:
            with mock.patch.object(no_handler_logger, 'hasHandlers', return_value=False):
                with mock.patch.object(no_handler_logger, 'info') as mock_info:
                    logger = SetupLogger._check_fallback_logger_config(logger=no_handler_logger)
        
        assert logger == no_handler_logger
        mock_basic_config.assert_called_once()
        # Check if any call to info contains "using basic config"
        found = False
        for call in mock_info.call_args_list:
            if "using basic config" in call.args[0]:
                found = True
                break
        assert found, f"Expected 'using basic config' in logs, got {mock_info.call_args_list}"
