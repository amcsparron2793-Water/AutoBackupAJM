from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent


from AutoBackupAJM.auto_backup_logger import AutoBackupLogger
from AutoBackupAJM.auto_backup_ajm import AutoBackup

from AutoBackupAJM import Hasher
# from AutoBackupAJM.auto_backup_continuous_check import AutoBackupContinuousCheck
