"""
auto_backup_ajm.py

allows automated backup on a chosen schedule

"""
import sys

try:
    from _version import __version__
except ImportError:
    from AutoBackupAJM._version import __version__

from AutoBackupAJM import SetupLogger, MISC_PROJECT_DIR

from pathlib import Path
from datetime import datetime, timedelta
from typing import Union, Optional
from hashlib import md5

import questionary


# TODO: implement Hasher classes
class AutoBackup:
    """
    Class to handle automated backup of a file.

    :ivar source_path: The path to the file to be backed up.
    :ivar _backup_dir_path_root: The root directory path for storing backup files.
    :ivar _backup_frequency: The frequency of the backup (daily, weekly, or monthly).
    :ivar backup_name: The name of the backup file.
    :ivar _backup_location: The path where the backup will be stored.
    :ivar most_recent_backup_file: Information about the most recent backup file.
    :ivar due_for_backup: Flag indicating if a new backup is due based on the backup frequency.
    :ivar full_backup_path: The full path where the backup file will be saved.

    """
    DATE_TODAY: datetime = datetime.today()
    VALID_BACKUP_FREQUENCIES = ['hourly', 'daily', 'weekly', 'monthly']
    DEFAULT_BACKUP_FREQUENCY = 'daily'

    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        self._backup_frequency = None
        self._backup_disabled = None
        self._backup_dir_path_root = None
        kwargs.setdefault('log_level_to_stream', 'INFO')

        self._logger = SetupLogger.setup_logger(**kwargs)

        self.source_path = Path(source_path).resolve()

        self.set_initial_properties_values(backup_dir_path_root, **kwargs)

        self.backup_name = kwargs.get('backup_name', f'{self.source_path.stem}{self.source_path.suffix}')

        self.force_backup = kwargs.get('force_backup', False)

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
            self._logger.info(f"Backup frequency set to {self._backup_frequency}")
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
            date_dir = Path(self.__class__.DATE_TODAY.strftime('%m%d%Y'))
        else:
            date_dir = Path(self.__class__.DATE_TODAY.strftime('%m%d%Y_%H00'))

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
            if most_recent_datetime.date() != self.__class__.DATE_TODAY:
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
        backup_created_at = datetime.fromtimestamp(self.full_backup_path.stat().st_ctime)
        recent_cutoff = (datetime.now() - timedelta(minutes=2))
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
    def source_changed_since_last_backup(self):
        """
        Indicates whether the database has changed since the last backup was made.
        If there is no previous backup, this property will be set to True.
        If the database file's MD5 hash matches that of the most recent backup file's MD5 hash,
         the property will be set to False, indicating that the database has not changed since the last backup.
         By default, the property is True.
        """
        # TODO: to be reworked with hasher.py implementation
        if self.most_recent_backup_file is None:
            # if there isn't a backup at all, then no matter what a backup should be done
            return True

        source_hash = md5(self.source_path.read_bytes()).hexdigest()

        # TODO: if archive - unzip backup, hash contents, then compare??
        # TODO: compare paths also for unchanged but moved files?
        backup_hash = md5(self.most_recent_backup_file[0].read_bytes()).hexdigest()

        if source_hash == backup_hash:
            self._logger.debug("source has not changed since last backup")
            return False
        return True

    def backup(self):
        """
        Method to perform a backup of the data. Checks if the data is due for backup and if so,
        it copies the content of the database file to the full backup path.
        It then prints a success message with the full backup path.
        If the data is not due for backup, it prints a message indicating that no backup is necessary.
        """
        if not self.backup_disabled:
            if (self.due_for_backup and self.source_changed_since_last_backup) or self.force_backup:
                self._overwrite_protection_check()
                self.full_backup_path.write_bytes(self.source_path.read_bytes())
                self._logger.info(f"Backup successful: {self.full_backup_path}")
            else:
                self._logger.debug("No backup necessary")
        else:
            self._logger.warning('backup disabled!')

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


if __name__ == "__main__":
    ABDB = AutoBackup(Path(MISC_PROJECT_DIR/'test_file.txt'),
                      Path(MISC_PROJECT_DIR/'test_backups'))
    ABDB.backup()
