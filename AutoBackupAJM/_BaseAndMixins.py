import shutil
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union, TYPE_CHECKING, List

import questionary
from tqdm import tqdm
from EasyLoggerAJM import SetupLogger

from AutoBackupAJM.auto_backup_logger import AutoBackupLogger

if TYPE_CHECKING:
    from logging import Logger
    # noinspection PyProtectedMember
    from EasyLoggerAJM import _EasyLoggerCustomLogger


class _IsDueForBackupMixin(metaclass=ABCMeta):
    DATE_TODAY: datetime = None
    VALID_BACKUP_FREQUENCIES = ['hourly', 'daily', 'weekly', 'monthly']
    DEFAULT_BACKUP_FREQUENCY = 'daily'
    RECENT_CUTOFF_DELTA_MINUTES = 2

    def __init__(self):
        super().__init__()
        self._backup_frequency = None
        self.backup_name = None
        self._logger = None
        self.use_custom_file_for_backup_due = False

    def __init_subclass__(cls, **kwargs):
        if cls.DATE_TODAY is None:
            raise ValueError("DATE_TODAY must be set in the subclass.")

    @property
    @abstractmethod
    def full_backup_path(self) -> Path:
        ...

    @property
    @abstractmethod
    def backup_dir_path_root(self):
        ...

    @backup_dir_path_root.setter
    @abstractmethod
    def backup_dir_path_root(self, value: Path):
        ...

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

    @property
    def backup_is_recent(self):
        """
        @property
        Check if a full backup was recent by verifying if the full backup path exists and
         its creation time is within the last 2 minutes compared to the current time.
        Returns True if the backup was recent, False otherwise.
        """
        backup_created_at = datetime.fromtimestamp(self.full_backup_path.stat().st_ctime)
        recent_cutoff = (datetime.now() - timedelta(minutes=self.__class__.RECENT_CUTOFF_DELTA_MINUTES))
        self._logger.debug(f"backup_created_at: {backup_created_at}, "
                           f"recent_cutoff time: {recent_cutoff}, "
                           f"recent_cutoff_delta: {self.__class__.RECENT_CUTOFF_DELTA_MINUTES}")
        return backup_created_at > recent_cutoff

    @staticmethod
    def glob_with_optional_zip(folder: Path, name: str) -> list[Path]:
        return [
            *folder.rglob(name),
            *folder.rglob(f"{name}.zip"),
        ]

    @property
    def most_recent_backup_file(self) -> Optional[tuple[Path, float]]:
        """
        Returns the most recent backup file in the backup directory specified by backup_dir_path_root.

        Returns:
            Tuple containing the most recent backup file and its creation time, or None if no backup files are found.
        """
        file_create_times = [(file, file.stat().st_ctime)
                             for file in self.glob_with_optional_zip(
                self.backup_dir_path_root, self.backup_name)]

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
        if self.use_custom_file_for_backup_due:
            # TODO: how to get this file?
            ...

        # if there are no backup files then no matter what create them
        if self.most_recent_backup_file is not None:
            # noinspection PyTypeChecker
            most_recent_datetime = datetime.fromtimestamp(self.most_recent_backup_file[1])
        else:
            return True
        return self._is_due(most_recent_datetime)

    def _is_due(self, most_recent_datetime: datetime):
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


class _MakeBackupDirPathRootMixin(metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self._backup_dir_path_root = None
        self._logger = None
        self._backup_disabled = None

    @property
    @abstractmethod
    def backup_disabled(self):
        ...

    @backup_disabled.setter
    @abstractmethod
    def backup_disabled(self, value):
        ...

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


class _CopyBytesMixin(metaclass=ABCMeta):
    ZIP_BACKUP_DEFAULT = True
    CLEANUP_BACKUP_PATH_DEFAULT = False

    def __init__(self):
        super().__init__()
        self._logger = None
        self.source_path = None
        self.zip_backup = None
        self.cleanup_backup_path = None
        self.backup_was_cleaned = None

    @property
    @abstractmethod
    def full_backup_path(self) -> Path:
        ...

    def _get_files_to_copy(self) -> List[Path]:
        if self.source_path.is_file():
            return [self.source_path]
        elif self.source_path.is_dir():
            self._logger.debug(f"Getting files to copy from dir: {self.source_path}")
            x = tqdm([f for f in self.source_path.rglob('*') if f.is_file()],
                     desc=f"Getting files to copy from dir: {self.source_path.name}")
            return list(x)
        return []

    def _write_backup_bytes_for_file(self, progress_bar: Optional[tqdm] = None):
        try:
            shutil.copy2(self.source_path, self.full_backup_path)
            if progress_bar:
                progress_bar.update(1)
        except shutil.Error as e:
            self._logger.exception(f"Could not copy {self.source_path} to {self.full_backup_path}: {e}")
            raise

    def _write_backup_bytes_for_dir(self, progress_bar: Optional[tqdm] = None, **kwargs):
        try:
            if progress_bar:
                def copy_with_progress(src, dst, *, follow_symlinks=True):
                    shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
                    # noinspection PyUnresolvedReferences
                    progress_bar.update(1)

                shutil.copytree(self.source_path, self.full_backup_path, copy_function=copy_with_progress)
            else:
                shutil.copytree(self.source_path, self.full_backup_path)
        except shutil.Error as e:
            self._logger.exception(f"Could not copy {self.source_path} to {self.full_backup_path}: {e}")
            raise

        if self.zip_backup:
            self._zip_and_clean_backup(**kwargs)

    def _write_file_hash_with_backup(self, hash_file_path: Optional[Path], **kwargs):
        """ Writes the hashes of the backed-up directory contents to the specified path."""
        hash_file_copy_dest = kwargs.get('hash_file_copy_dest', self.full_backup_path.parent)
        self._logger.debug(f"hash_file_copy_dest: {hash_file_copy_dest}")

        if hash_file_path is not None:
            try:
                shutil.copy2(hash_file_path, hash_file_copy_dest)
                self._logger.debug(f"Copied {hash_file_path} to {hash_file_copy_dest}")
                return
            except shutil.Error as e:
                try:
                    raise shutil.Error(f"Could not copy {hash_file_path} to {hash_file_copy_dest}") from e
                except shutil.Error as e:
                    self._logger.exception(e)
                    self._logger.warning("hash_file not copied to new destination. "
                                         "Backup should be intact.")
                    return
        self._logger.error(f"hash_file_path not provided, not copying hash file to new destination. "
                           f"Backup should be intact.")

    # FIXME: the CLEANUP portion of this creates an issue for detecting existing DIRECTORY backups,
    #  if the backup dir is removed, then the directory backup will never not be due,
    #  since the directory isn't in the backup folder. cleanup portion has been temp disabled
    def _zip_and_clean_backup(self, fmt='zip', **kwargs):
        self.cleanup_backup_path = kwargs.get('cleanup_backup_path', self.cleanup_backup_path)

        shutil.make_archive(base_name=self.full_backup_path.as_posix(),
                            format=fmt, root_dir=self.full_backup_path,
                            logger=self._logger)

        expected_archive_file_path = self.full_backup_path.with_suffix(f'.{fmt}')

        if expected_archive_file_path.is_file():
            self._logger.info(f"Zipped backup successfully: {expected_archive_file_path}", print_msg=True)

        # FIXME: this is NotImplemented because while the cleanup works,
        #  it causes issues detecting previous backups
        if self.cleanup_backup_path:
            try:
                raise NotImplementedError("cleanup_backup_path not implemented yet")
            except NotImplementedError as e:
                self._logger.error(e)
                return
            shutil.rmtree(self.full_backup_path)
            self.backup_was_cleaned = True
            self._write_file_hash_with_backup(**kwargs)

    def _write_backup_bytes(self, progress_bar: Optional[tqdm] = None, **kwargs):
        if self.source_path.is_file():
            self._write_backup_bytes_for_file(progress_bar)
        elif self.source_path.is_dir():
            self._write_backup_bytes_for_dir(progress_bar, **kwargs)
        else:
            raise FileNotFoundError(f"{self.source_path} does not exist")

    def _get_backup_progress_bar(self, use_progress_bar: bool) -> Optional[tqdm]:
        progress_bar = None
        if use_progress_bar:
            files_to_copy = self._get_files_to_copy()
            progress_bar = tqdm(total=len(files_to_copy),
                                desc=f"Backing up {self.source_path.name}",
                                unit="file")
        return progress_bar


class _BaseAutoBackup(_MakeBackupDirPathRootMixin,
                      _IsDueForBackupMixin,
                      _CopyBytesMixin, metaclass=ABCMeta):
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

    NON_HOURLY_DATE_FORMAT = '%m%d%Y'
    HOURLY_DATE_FORMAT = '%m%d%Y_%H00'

    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        super().__init__()
        self._backup_disabled = None
        self._logger = self._setup_logger(**kwargs)

        self.source_path = Path(source_path).resolve()

        self._set_initial_properties_values(backup_dir_path_root, **kwargs)

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
    def full_backup_path(self):
        """
        This method returns the full path for the backup by combining the backup location and backup name provided.
        """
        return self.backup_location / self.backup_name

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

    def _set_initial_properties_values(self, backup_dir_path_root, **kwargs):
        self.backup_disabled = kwargs.get('disable_backup', False)
        self.zip_backup = kwargs.get('zip_backup', self.__class__.ZIP_BACKUP_DEFAULT)
        self.cleanup_backup_path = kwargs.get('cleanup_backup_path', self.__class__.CLEANUP_BACKUP_PATH_DEFAULT)

        # _backup_dir_path_root is set directly so testing patch works
        self._backup_dir_path_root = Path(backup_dir_path_root).resolve()
        self.backup_frequency = kwargs.get('backup_frequency', self.__class__.DEFAULT_BACKUP_FREQUENCY)

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

    def _attempt_backup(self, use_progress_bar: bool = True, **kwargs):
        self._overwrite_protection_check()
        progress_bar = self._get_backup_progress_bar(use_progress_bar)

        self._log_attempted_backup()

        try:
            self._write_backup_bytes(progress_bar=progress_bar, **kwargs)
            if progress_bar:
                progress_bar.close()
            self._logger.info(f"Backup successful: {self.full_backup_path}", print_msg=True)
        except Exception as e:
            if progress_bar:
                progress_bar.close()
            self._logger.exception(f"Backup failed: {e}")

    def _log_attempted_backup(self, **kwargs):
        self._logger.info(f"Attempting backup at {datetime.today()} "
                          f"for {self.source_path.name}...", print_msg=True)
        self._logger.debug(f"full source_path is {self.source_path}, "
                           f"full backup_dir_path_root is {self.backup_dir_path_root}")

    def _log_no_backup_due(self):
        self._logger.debug(f"No backup necessary at {datetime.today()} "
                           f"for {self.source_path.name}", print_msg=True)
        self._logger.debug(f"full source_path is {self.source_path}, "
                           f"full backup_dir_path_root is {self.backup_dir_path_root}")

    def _process_no_backup_due(self, **kwargs):
        self._log_no_backup_due()

    def _eval_for_and_attempt_backup(self, **kwargs):
        kwargs.setdefault('use_progress_bar', True)
        if self.due_and_changed or self.force_backup:
            self._attempt_backup(**kwargs)
        else:
            self._process_no_backup_due()

    def backup(self, **kwargs):
        """
        Method to perform a backup of the data. Checks if the data is due for backup and if so,
        it copies the content of the file to the full backup path.
        It then prints a success message with the full backup path.
        If the data is not due for backup, it prints a message indicating that no backup is necessary.
        """
        self.force_backup = kwargs.get('force_backup', self.force_backup)
        kwargs.setdefault('use_progress_bar', True)

        if not self.backup_disabled:
            self._eval_for_and_attempt_backup(**kwargs)
        else:
            self._logger.warning('backup disabled!', print_msg=True)
