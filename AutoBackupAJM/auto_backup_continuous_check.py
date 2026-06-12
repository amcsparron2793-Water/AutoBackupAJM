from pathlib import Path

from AutoBackupAJM import AutoBackup


class AutoBackupContinuousCheck(AutoBackup):
    def continuous_monitor(self):
        self._logger.info("continuous backup monitor started...")
        self._logger.info("press ctrl+c to exit")
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

            except KeyboardInterrupt as e:
                self._logger.warning("user interrupted backup process, exiting...")
                break

    def _overwrite_protection_check(self):
        return

    def _make_backup_dir_path_root_question(self, backup_dir_path_root: Path):
        return True


if __name__ == "__main__":
    ABCC = AutoBackupContinuousCheck('../tox.ini','../test_backups')
    ABCC.continuous_monitor()