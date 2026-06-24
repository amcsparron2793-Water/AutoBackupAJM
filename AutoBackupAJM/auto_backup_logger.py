from logging import Logger

from EasyLoggerAJM import EasyLogger

from AutoBackupAJM import PROJECT_ROOT


# TODO: implement
class AutoBackupLogger(EasyLogger):
    _PROJECT_ROOT = PROJECT_ROOT
    # ROOT_LOG_LOCATION_DEFAULT = PROJECT_ROOT / 'logs'
    PROJECT_NAME = 'AutoBackupAJM'

    def __init__(self, **kwargs):
        kwargs.setdefault('project_name', self.__class__.PROJECT_NAME)
        kwargs.setdefault('show_warning_logs_in_console', True)
        kwargs.setdefault('log_spec', 'hourly')
        super().__init__(**kwargs)
        self.logger.name = self.__class__.__name__

    def __call__(self, **kwargs) -> Logger:
        return self.logger


if __name__ == '__main__':
    abl = AutoBackupLogger()()
    abl.info("this is an info message")
    abl.warning("this is a warning message")
