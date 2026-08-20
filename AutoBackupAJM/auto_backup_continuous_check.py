from pathlib import Path
from time import sleep
from typing import Union

from AutoBackupAJM import BasicAutoBackup


# TODO: use the_sandman for sleeping?
# TODO: refresh DATE_TODAY every hour for continuous?
class AutoBackupContinuousCheck(BasicAutoBackup):
    def __init__(self, source_path: Union[Path, str], backup_dir_path_root: Union[Path, str], **kwargs):
        super().__init__(source_path, backup_dir_path_root, **kwargs)
        self.not_due_notified = False

    def _log_intro_and_warnings(self):
        self._logger.info("Continuous Backup Monitor started...")
        self._logger.info("press ctrl+c to exit")
        self._logger.warning("_overwrite_protection_check() disabled for continuous monitor")
        self._logger.warning("_make_backup_dir_path_root_question() always returns True for continuous monitor")

    def _monitor_loop(self):
        if self.due_for_backup:
            self._logger.info("Attempting backup...")
            self.backup()
            self.not_due_notified = False
        else:
            if not self.not_due_notified:
                self._logger.info("no backup necessary")
                self.not_due_notified = True
        self.sleep(10)  # TODO: make this based on self.backup_frequency

    def continuous_monitor(self):
        self._log_intro_and_warnings()

        while True:
            try:
                self._monitor_loop()
            except KeyboardInterrupt as e:
                self._logger.warning("user interrupted backup process, exiting...")
                break

    def sleep(self, seconds: int):
        self._logger.debug(f"sleeping for {seconds} seconds...")
        sleep(seconds)

    def _overwrite_protection_check(self):
        return

    def _make_backup_dir_path_root_question(self, backup_dir_path_root: Path):
        return True


if __name__ == "__main__":
    ABCC = AutoBackupContinuousCheck('../tox.ini',
                                     '../Misc_Project_Files/test_backups')
    ABCC.continuous_monitor()
