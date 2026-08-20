"""
auto_backup_ajm.py

allows automated backup on a chosen schedule

"""
from typing import TYPE_CHECKING, Type, Union, Optional
from abc import ABCMeta, abstractmethod

if TYPE_CHECKING:
    from logging import Logger
    # noinspection PyProtectedMember
    from EasyLoggerAJM import _EasyLoggerCustomLogger
    # noinspection PyProtectedMember
    from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import _BaseHashComparer
    from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory

try:
    from _version import __version__
except ImportError:
    from AutoBackupAJM._version import __version__

import questionary

from EasyLoggerAJM import SetupLogger
from AutoBackupAJM import MISC_PROJECT_DIR, AutoBackupLogger, CustomComparerFactory

import shutil
from pathlib import Path
from datetime import datetime, timedelta
from hashlib import md5


class _BaseAutoBackup(metaclass=ABCMeta):
    # noinspection GrazieStyle
    """
        Abstract base class for implementing auto-backup functionality.

        This class provides a foundational framework for managing and configuring automated
        backups. It includes properties and methods for handling backup frequencies, backup
        locations, and tracking whether the source has changed since the last backup. Subclasses
        should implement the abstract property `source_changed_since_last_backup` to define
        specific logic for detecting changes to the source.

        :ivar source_path: The resolved path to the source that will be backed up.
        :type source_path: pathlib.Path
        :ivar backup_name: The name of the backup file, which defaults to the stem and suffix of
            the source path unless otherwise specified.
        :type backup_name: str
        :ivar force_backup: Flag indicating whether to forcibly create a backup regardless of other
            conditions.
        :type force_backup: bool
    """
    DATE_TODAY: datetime = datetime.today()
    VALID_BACKUP_FREQUENCIES = ['hourly', 'daily', 'weekly', 'monthly']
    DEFAULT_BACKUP_FREQUENCY = 'daily'

    NON_HOURLY_DATE_FORMAT = '%m%d%Y'
    HOURLY_DATE_FORMAT = '%m%d%Y_%H00'

    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        self._backup_frequency = None
        self._backup_disabled = None
        self._backup_dir_path_root = None

        self._logger = self._setup_logger(**kwargs)

        self.source_path = Path(source_path).resolve()

        self.set_initial_properties_values(backup_dir_path_root, **kwargs)

        self.backup_name = kwargs.get('backup_name', f'{self.source_path.stem}{self.source_path.suffix}')

        self.force_backup = kwargs.get('force_backup', False)

    @property
    @abstractmethod
    def source_changed_since_last_backup(self) -> bool:
        """
        Indicates whether the file has changed since the last backup was made.
        If there is no previous backup, this property will be set to True.
        If the file's MD5 hash matches that of the most recent backup file's MD5 hash,
         the property will be set to False, indicating that the file has not changed since the last backup.
         By default, the property is True.
        """
        ...

    @staticmethod
    def _setup_logger(**kwargs) -> Union['Logger', '_EasyLoggerCustomLogger']:
        setup_logger_class = kwargs.pop('setup_logger_class', SetupLogger)

        kwargs.setdefault('log_level_to_stream', 'WARNING')

        setup_logger_class.DEFAULT_CUSTOM_LOGGER = AutoBackupLogger
        # noinspection PyTypeChecker
        return setup_logger_class.setup_logger(**kwargs)

    def set_initial_properties_values(self, backup_dir_path_root, **kwargs):
        self.backup_disabled = kwargs.get('disable_backup', False)
        # _backup_dir_path_root is set directly so testing patch works
        self._backup_dir_path_root = Path(backup_dir_path_root).resolve()
        self.backup_frequency = kwargs.get('backup_frequency', self.__class__.DEFAULT_BACKUP_FREQUENCY)

    @property
    def backup_disabled(self):
        return self._backup_disabled

    @backup_disabled.setter
    def backup_disabled(self, value):
        if value != self._backup_disabled:
            if value:
                self._logger.warning('backup disabled!')
            else:
                self._logger.info('backup enabled!')
        self._backup_disabled = value

    @property
    def backup_frequency(self):
        """
        @property
        backup_frequency(self)

        This property method is used to retrieve the backup frequency of the object.
        It checks if the provided backup frequency is within the valid backup frequencies list
         and converts it to lowercase before returning the value. If the backup frequency is not valid,
          it raises a ValueError with a message indicating the invalid backup frequency.
        """
        if self._backup_frequency:
            self._backup_frequency = self._backup_frequency.lower()
        return self._backup_frequency

    @backup_frequency.setter
    def backup_frequency(self, value: str):
        if value.lower() in self.__class__.VALID_BACKUP_FREQUENCIES:
            self._backup_frequency = value.lower()
            self._logger.debug(f"Backup frequency set to {self._backup_frequency}")
        else:
            raise ValueError(f"Invalid backup frequency: {value.lower()}")

    def _make_backup_dir_path_root_question(self, backup_dir_path_root: Path):
        make = questionary.confirm(
            f"{backup_dir_path_root} does not exist, would you like to create it?").ask()
        if make:
            return True
        else:
            self.backup_disabled = True
            self._logger.error(f"{backup_dir_path_root} does not exist, and user declined to create it.")
            return False

    def _make_backup_dir_path_root(self, backup_dir_path_root: Path):
        try:
            backup_dir_path_root.mkdir(parents=True, exist_ok=True)
        except (OSError, FileNotFoundError) as e:
            self._logger.warning(e)
            self.backup_disabled = True

    @property
    def backup_dir_path_root(self):
        """
        Property to get the root path for the backup directory. If the directory does not exist,
        it prompts the user to confirm the creation of the directory before returning the path.
        """
        return self._backup_dir_path_root

    @backup_dir_path_root.setter
    def backup_dir_path_root(self, value: Path):
        value = Path(value).resolve()
        self._backup_dir_path_root = value

        if value.is_dir():
            return

        if self._make_backup_dir_path_root_question(value):
            self._make_backup_dir_path_root(value)

    @property
    def backup_location(self):
        """
        Returns the backup location where backups will be stored.
        """
        if self.backup_frequency != 'hourly':
            date_dir = Path(self.__class__.DATE_TODAY.strftime(self.__class__.NON_HOURLY_DATE_FORMAT))
        else:
            date_dir = Path(self.__class__.DATE_TODAY.strftime(self.__class__.HOURLY_DATE_FORMAT))

        backup_location = self.backup_dir_path_root / date_dir
        backup_location.mkdir(parents=True, exist_ok=True)

        return backup_location

    @property
    def most_recent_backup_file(self) -> Optional[tuple[Path, float]]:
        """
        Returns the most recent backup file in the backup directory specified by backup_dir_path_root.

        Returns:
            Tuple containing the most recent backup file and its creation time, or None if no backup files are found.
        """
        file_create_times = [(file, file.stat().st_ctime) for file in self.backup_dir_path_root.rglob(self.backup_name)]
        try:
            return max(file_create_times, key=lambda x: x[1])
        except ValueError:
            return None

    @property
    def due_for_backup(self):
        """
        Check if a backup is due based on the backup file history and the backup frequency set.
        Returns True if a backup is due, False otherwise.
        """
        # if there are no backup files then no matter what create them
        if self.most_recent_backup_file is not None:
            # noinspection PyTypeChecker
            most_recent_datetime = datetime.fromtimestamp(self.most_recent_backup_file[1])
        else:
            return True
        if self.backup_frequency == 'hourly':
            if (
                    (most_recent_datetime.hour != self.__class__.DATE_TODAY.hour)
                    and (most_recent_datetime.date() == self.__class__.DATE_TODAY.date())
            ):
                return True
        elif self.backup_frequency == 'daily':
            if most_recent_datetime.date() != self.__class__.DATE_TODAY.date():
                return True
        elif self.backup_frequency == 'weekly':
            if most_recent_datetime.isocalendar()[1] != self.__class__.DATE_TODAY.isocalendar()[1]:
                return True
        elif self.backup_frequency == 'monthly':
            if most_recent_datetime.month != self.__class__.DATE_TODAY.month:
                return True
        return False

    @property
    def full_backup_path(self):
        """
        This method returns the full path for the backup by combining the backup location and backup name provided.
        """
        return self.backup_location / self.backup_name

    @property
    def backup_is_recent(self):
        """
        @property
        Check if a full backup was recent by verifying if the full backup path exists and
         its creation time is within the last 2 minutes compared to the current time.
        Returns True if the backup was recent, False otherwise.
        """
        recent_cutoff_delta_minutes = 2
        backup_created_at = datetime.fromtimestamp(self.full_backup_path.stat().st_ctime)
        recent_cutoff = (datetime.now() - timedelta(minutes=recent_cutoff_delta_minutes))
        self._logger.debug(f"backup_created_at: {backup_created_at}, "
                           f"recent_cutoff time: {recent_cutoff}, "
                           f"recent_cutoff_delta: {recent_cutoff_delta_minutes}")
        return backup_created_at > recent_cutoff

    @property
    def backup_successful(self):
        """
        @property
        Check if a full backup was successful by verifying if the full backup path exists and
         its creation time is within the last 2 minutes compared to the current time.
        Returns True if the backup was successful, False otherwise.
        """
        if not self.backup_disabled:
            if (
                    (
                            self.full_backup_path.is_file()
                            and self.backup_is_recent
                    )
                    or (self.force_backup and self.full_backup_path.is_file())
            ):
                self._logger.info(f"Backup successful: {self.full_backup_path}")
                return True
            return False
        self._logger.warning('backup disabled!')
        return False

    @property
    def due_and_changed(self):
        return self.due_for_backup and self.source_changed_since_last_backup

    def _write_backup_bytes(self):
        if self.source_path.is_file():
            self.full_backup_path.write_bytes(self.source_path.read_bytes())
        elif self.source_path.is_dir():
            shutil.copytree(self.source_path, self.full_backup_path)
        else:
            raise FileNotFoundError(f"{self.source_path} does not exist")

    def backup(self, **kwargs):
        """
        Method to perform a backup of the data. Checks if the data is due for backup and if so,
        it copies the content of the file to the full backup path.
        It then prints a success message with the full backup path.
        If the data is not due for backup, it prints a message indicating that no backup is necessary.
        """
        self.force_backup = kwargs.get('force_backup', self.force_backup)
        if not self.backup_disabled:
            if self.due_and_changed or self.force_backup:
                self._overwrite_protection_check()
                try:
                    self._write_backup_bytes()
                    self._logger.info(f"Backup successful: {self.full_backup_path}", print_msg=True)
                except Exception as e:
                    self._logger.exception(f"Backup failed: {e}")
            else:
                self._logger.debug("No backup necessary", print_msg=True)
        else:
            self._logger.warning('backup disabled!', print_msg=True)

    def _overwrite_protection_check(self):
        FEE_text = f"backups of {self.backup_name} seem to already exist in this directory"
        overwrite_question_text = f'Do you wish to overwrite {self.backup_name}'

        for f in self.backup_location.iterdir():
            if f.name == self.backup_name:
                if not self.force_backup:
                    raise FileExistsError(FEE_text)
                if self.force_backup and questionary.confirm(overwrite_question_text,
                                                             default=False).ask():
                    # FIXME: self.backup_success() doesn't detect this properly,
                    #  but backup seems to work successfully
                    pass
                else:
                    raise FileExistsError(FEE_text)


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
    DEFAULT_COMPARER_CLASS = CustomComparerFactory

    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        super().__init__(source_path, backup_dir_path_root, **kwargs)
        kwargs.setdefault('logger', self._logger)

        kwargs.setdefault('comparer_class', self.__class__.DEFAULT_COMPARER_CLASS)
        self.comparer = self._get_comparer(**kwargs)

    def _get_comparer(self,
                      comparer_class: Union['_BaseHashComparer', Type[CustomComparerFactory], Type['ComparerFactory']],
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
    ECAB.backup()  # force_backup=True)
