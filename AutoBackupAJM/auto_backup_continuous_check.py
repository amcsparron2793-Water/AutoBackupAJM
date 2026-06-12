from AutoBackupAJM import AutoBackup


class AutoBackupContinuousCheck(AutoBackup):
    def continuous_monitor(self):
        ...

    def _overwrite_protection_check(self):
        return


if __name__ == "__main__":
    AutoBackupContinuousCheck('','')