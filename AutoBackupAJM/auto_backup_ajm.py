"""
auto_backup_ajm.py

allows automated backup on a chosen schedule

"""
from typing import TYPE_CHECKING, Type, Union, Optional
from pathlib import Path
from hashlib import md5

from AutoBackupAJM import MISC_PROJECT_DIR
from AutoBackupAJM._BaseAndMixins import _BaseAutoBackup

from AutoBackupAJM.custom_compare_factory import AutoBackupComparerFactory

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import _BaseHashComparer
    from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory


class BasicAutoBackup(_BaseAutoBackup):
    """
    Automates the backup process by determining if the source has changed
    since the last backup. It compares the hash of the source file to the
    most recent backup file to detect changes.

    :ivar most_recent_backup_file: The most recent backup file used for comparison.
    :type most_recent_backup_file: Optional[List[pathlib.Path]]
    :ivar source_path: The file path that is being monitored for changes.
    :type source_path: pathlib.Path
    :ivar _logger: Internal logger for debugging and tracing execution.
    :type _logger: logging.Logger
    """

    @property
    def source_changed_since_last_backup(self):

        if self.most_recent_backup_file is None:
            # if there isn't a backup at all, then no matter what a backup should be done
            return True

        source_hash = md5(self.source_path.read_bytes()).hexdigest()

        # noinspection PyTypeChecker
        most_recent_backup_file_path: Path = self.most_recent_backup_file[0]
        backup_hash = md5(most_recent_backup_file_path.read_bytes()).hexdigest()

        if source_hash == backup_hash:
            self._logger.debug("source has not changed since last backup")
            return False
        return True


class ExternalCompareAutoBackup(_BaseAutoBackup):
    """
    Compares the current state of files with the most recent backup state and determines if a backup is necessary.

    This class specializes in utilizing an EXTERNAL comparer to evaluate whether the current source files have changed
    since the last backup. Its primary purpose is to streamline the process of automated backups by avoiding
    redundant operations when no changes are detected. The comparer used is either customized or default,
    depending on the provided configuration.

    :ivar DEFAULT_COMPARER_CLASS: The default class used to instantiate the comparer if no custom comparer
        is provided.
    :type DEFAULT_COMPARER_CLASS: Type[CustomComparerFactory]
    :ivar comparer: The comparer instance used to evaluate changes between source files and backup files.
    :type comparer: Union['_BaseHashComparer', Type[CustomComparerFactory], Type['ComparerFactory']]
    """
    DEFAULT_COMPARER_CLASS = AutoBackupComparerFactory

    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        super().__init__(source_path, backup_dir_path_root, **kwargs)
        kwargs.setdefault('logger', self._logger)

        kwargs.setdefault('comparer_class', self.__class__.DEFAULT_COMPARER_CLASS)
        self.comparer = self._get_comparer(**kwargs)

    def _get_comparer(self,
                      comparer_class: Union['_BaseHashComparer', Type['ComparerFactory']],
                      **kwargs):
        if not callable(comparer_class):
            raise TypeError(f"comparer_class must be callable, "
                            f"{type(comparer_class)} does not have a __call__ method.")
        try:
            return comparer_class(self.source_path, self.most_recent_backup_file[0], **kwargs)
        except TypeError as e:
            self._logger.warning(e)
            try:
                return comparer_class(self.source_path, self.backup_dir_path_root, **kwargs)
            except ValueError as e:
                self._logger.exception(e)
                exit(1)

    @property
    def source_changed_since_last_backup(self):
        if self.most_recent_backup_file is None:
            # if there isn't a backup at all, then no matter what a backup should be done
            return True
        # comparer returns True if the hashes match,
        # since we want to check if the hashes DON'T match,
        # we need to return the inverse
        return not self.comparer.compare()


if __name__ == "__main__":
    ECAB = ExternalCompareAutoBackup(source_path=Path(MISC_PROJECT_DIR / 'HostedFeatureStorage_Other'),
                                     backup_dir_path_root=Path(MISC_PROJECT_DIR / 'test_backups'))
    ECAB.backup(force_backup=True, log_level_to_stream='DEBUG')
