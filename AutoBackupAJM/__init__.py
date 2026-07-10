from pathlib import Path
from typing import Optional


def find_project_root(start: Optional[Path] = None, **kwargs) -> Path:
    start: Path = start or Path(__file__).resolve()
    marker_file = kwargs.get("marker_file", "setup.py")

    for path in [start, *start.parents]:
        if (path / marker_file).exists():
            return path

    raise FileNotFoundError(f"Could not find project root containing {marker_file}")


PROJECT_ROOT = find_project_root()
MISC_PROJECT_DIR = PROJECT_ROOT / "Misc_Project_Files"


from AutoBackupAJM.auto_backup_logger import AutoBackupLogger, SetupLogger
from AutoBackupAJM.auto_backup_ajm import AutoBackup

from AutoBackupAJM import Hasher
# from AutoBackupAJM.auto_backup_continuous_check import AutoBackupContinuousCheck
