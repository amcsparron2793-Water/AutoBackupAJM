from pathlib import Path
from time import sleep

from AutoBackupAJM import AutoBackup


# TODO: use the_sandman for sleeping?
# TODO: refresh DATE_TODAY every hour for continuous?
class AutoBackupContinuousCheck(AutoBackup):
    def _log_intro_and_warnings(self):
        self._logger.info("Continuous Backup Monitor started...")
        self._logger.info("press ctrl+c to exit")
        self._logger.warning("_overwrite_protection_check() disabled for continuous monitor")
        self._logger.warning("_make_backup_dir_path_root_question() always returns True for continuous monitor")

    def continuous_monitor(self):
        self._log_intro_and_warnings()

        not_due_notified = False
        while True:
            try:
                if self.due_for_backup:
                    self._logger.info("attempting backup...")
                    self.backup()
                    not_due_notified = False
                else:
                    if not not_due_notified:
                        self._logger.info("no backup necessary")
                        not_due_notified = True
                self.sleep(10)  # TODO: make this based on self.backup_frequency

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
