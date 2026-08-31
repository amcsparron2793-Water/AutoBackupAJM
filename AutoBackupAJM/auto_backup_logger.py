from logging import Logger

# noinspection PyProtectedMember
from EasyLoggerAJM import EasyLogger, _EasyLoggerCustomLogger
from AutoBackupAJM import PROJECT_ROOT
from ColorizerAJM import Colorizer


class _AutoBackupCustomLogger(_EasyLoggerCustomLogger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colorizer = Colorizer()

    def _log(self, level, msg, args,
             exc_info=None, extra=None,
             stack_info=False, **kwargs):
        """
        _log is called by every logging method to actually log the message.

        :param level: The logging level specified for the log message.
        :type level: int
        :param msg: The message that needs to be logged.
        :type msg: str
        :param args: Arguments to be merged into the log message.
        :type args: tuple
        :param exc_info: Indicator or exception information for the log message. Can be a tuple, exception, or boolean.
        :type exc_info: Optional[Union[tuple, Exception, bool]]
        :param extra: Additional context information to include in the log record.
        :type extra: Optional[dict]
        :param stack_info: Whether stack information should be added to the log record.
        :type stack_info: bool
        :param kwargs: Additional keyword arguments to modify the log behavior.
        :type kwargs: dict
        :return: None
        :rtype: None
        """
        # noinspection PyTypeChecker
        self._print_msg(msg, print_msg=kwargs.pop('print_msg', False),
                        print_in_color=kwargs.pop('print_in_color', True),
                        color_to_print=kwargs.pop('color_to_print', None))
        msg = self.sanitize_msg(msg)
        # noinspection PyProtectedMember
        super()._log(level, msg, args,
                     exc_info=exc_info,
                     extra=extra, stack_info=stack_info,
                     **kwargs)

    def _format_printed_msg_color(self, msg, **kwargs):
        print_in_color = kwargs.pop('print_in_color', False)
        color_to_print = kwargs.pop('color_to_print', None)
        if print_in_color:
            msg = self.colorizer.colorize(msg, color=color_to_print)
        return msg

    def _print_msg(self, msg, **kwargs):
        msg = self._format_printed_msg_color(msg, **kwargs)
        super()._print_msg(msg, **kwargs)


class AutoBackupLogger(EasyLogger):
    _PROJECT_ROOT = PROJECT_ROOT
    ROOT_LOG_LOCATION_DEFAULT = _PROJECT_ROOT / 'logs'
    PROJECT_NAME = 'AutoBackupAJM'

    def _set_logger_class(self, logger_class=None, **kwargs):
        if logger_class is None:
            logger_class = _AutoBackupCustomLogger
        return super()._set_logger_class(logger_class=logger_class, **kwargs)

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
