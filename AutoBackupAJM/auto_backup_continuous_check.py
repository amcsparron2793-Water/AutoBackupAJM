from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Union

from AutoBackupAJM import BasicAutoBackup, ExternalCompareAutoBackup, MISC_PROJECT_DIR


# TODO: use the_sandman for sleeping?
# FIXME: needs logger work?
class BasicAutoBackupContinuousCheck(BasicAutoBackup):
    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        super().__init__(source_path, backup_dir_path_root, **kwargs)
        self.not_due_notified = False
        self._logger.name = self.__class__.__name__

    def _log_intro_and_warnings(self):
        self._logger.info("Continuous Backup Monitor started...", print_msg=True)
        self._logger.info("press ctrl+c to exit", print_msg=True)
        self._logger.warning("_overwrite_protection_check() disabled for continuous monitor")
        self._logger.warning("_make_backup_dir_path_root_question() always returns True for continuous monitor")

    def _monitor_loop(self):
        if self.due_for_backup:
            self.backup()
        self.sleep(10)  # TODO: make this based on self.backup_frequency

    def _process_no_backup_due(self, **kwargs):
        self.__class__.DATE_TODAY = datetime.today()
        if not self.not_due_notified:
            self._logger.debug("No backup necessary", print_msg=True)
            self.not_due_notified = True

    def _attempt_backup(self, use_progress_bar: bool = True):
        self._logger.info("Attempting backup...", print_msg=True)
        super()._attempt_backup(use_progress_bar=use_progress_bar)
        self.not_due_notified = False

    def continuous_monitor(self):
        self._log_intro_and_warnings()

        while True:
            try:
                self._monitor_loop()
            except KeyboardInterrupt as e:
                self._logger.error("user interrupted backup process, exiting...")
                break

    def sleep(self, seconds: int):
        self._logger.debug(f"sleeping for {seconds} seconds...")
        sleep(seconds)

    def _overwrite_protection_check(self):
        return

    def _make_backup_dir_path_root_question(self, backup_dir_path_root: Path):
        return True


class ExternalCompareContinuousCheck(ExternalCompareAutoBackup, BasicAutoBackupContinuousCheck):
    def __init__(self, source_path: Path, backup_dir_path_root: Path, **kwargs):
        super().__init__(source_path, backup_dir_path_root, **kwargs)
        self._logger.name = self.__class__.__name__


if __name__ == "__main__":
    ABCC = ExternalCompareContinuousCheck(Path(MISC_PROJECT_DIR / 'HostedFeatureStorage_Other.zip'),
                                          Path(MISC_PROJECT_DIR / 'test_backups'))
    ABCC.continuous_monitor()
