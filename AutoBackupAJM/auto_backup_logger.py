from logging import Logger, getLogger, basicConfig
from typing import Optional

from EasyLoggerAJM import EasyLogger
from AutoBackupAJM import PROJECT_ROOT


class AutoBackupLogger(EasyLogger):
    _PROJECT_ROOT = PROJECT_ROOT
    ROOT_LOG_LOCATION_DEFAULT = _PROJECT_ROOT / 'logs'
    PROJECT_NAME = 'AutoBackupAJM'

    def __init__(self, **kwargs):
        kwargs.setdefault('project_name', self.__class__.PROJECT_NAME)
        kwargs.setdefault('show_warning_logs_in_console', True)
        kwargs.setdefault('log_spec', 'hourly')
        super().__init__(**kwargs)
        self.logger.name = self.__class__.__name__

    def __call__(self, **kwargs) -> Logger:
        return self.logger


class SetupLogger:
    """
    Provides methods to configure and manage a logging mechanism. This class
    ensures that a logger is properly initialized and allows fallback
    configuration for cases where no logger handlers are defined.

    :ivar log_level_to_stream: Default log level for streaming logs as a string.
    :type log_level_to_stream: str
    :ivar basic_config_level: Default log level for basic configuration as a string.
    :type basic_config_level: str
    """

    def __new__(cls, *args, **kwargs):
        raise TypeError("SetupLogger cannot be instantiated. Use SetupLogger.setup_logger(...) instead.")

    @classmethod
    def setup_logger(cls, **kwargs) -> Logger:
        kwargs.setdefault('log_level_to_stream', 'INFO')
        logger = kwargs.pop('logger', None)
        if not logger:
            logger = AutoBackupLogger(**kwargs)()
        logger = cls._check_fallback_logger_config(logger=logger, **kwargs)
        return logger

    @classmethod
    def _check_fallback_logger_config(cls, default_logger_name: Optional[str] = None, **kwargs) -> Logger:
        default_logger_name = default_logger_name or cls.__name__
        logger = kwargs.get('logger', None)
        basic_config_level = kwargs.pop('basic_config_level', 'DEBUG')

        if not logger:
            logger = getLogger(default_logger_name)
        if logger.name == default_logger_name or not logger.hasHandlers():
            basicConfig(level=basic_config_level)
            logger.info(f'using basic config with level: {basic_config_level}')
        else:
            logger.info(f"logger: {logger.name} already has handlers, not using basicConfig")
        logger.info(f"Using logger: {logger.name}")
        return logger


if __name__ == '__main__':
    abl = AutoBackupLogger()()
    abl.info("this is an info message")
    abl.warning("this is a warning message")
