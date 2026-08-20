from logging import Logger
from typing import Any, Union

from EasyLoggerAJM import SetupLogger
from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory
from .custom_comparers import DirectoryToDirectoryComparer


class CustomComparerFactory(ComparerFactory):
    """ adds in DirectoryToDirectoryComparer for direct directory-to-directory comparison"""
    _DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS = DirectoryToDirectoryComparer

    @classmethod
    def _directory_src_targets(cls, source: Any, target: Any, **kwargs):
        target_is_directory = cls._is_directory_input(target)
        if target_is_directory:
            return cls._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS(
                source_dir=source,
                target_dir=target,
                **kwargs,
            )
        return None

    @staticmethod
    def _setup_logger(**kwargs) -> Union[Logger]:
        from .. import AutoBackupLogger
        setup_logger_class = kwargs.pop('setup_logger_class', SetupLogger)

        kwargs.setdefault('log_level_to_stream', 'WARNING')

        setup_logger_class.DEFAULT_CUSTOM_LOGGER = AutoBackupLogger
        # noinspection PyTypeChecker
        return setup_logger_class.setup_logger(**kwargs)

    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        source_is_directory = cls._is_directory_input(source)
        if source_is_directory:
            return cls._directory_src_targets(source, target, **kwargs)
        return ComparerFactory.inst_comparer_class(source, target, **kwargs)

    def __new__(cls, source: Any, target: Any, **kwargs):
        kwargs["logger"] = cls._setup_logger(**kwargs)
        return cls.inst_comparer_class(source, target, **kwargs)
