from pathlib import Path
from typing import Optional, Union

from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


# TODO: if file is archive, option to unzip and hash contents
class ArchiveHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    def __init__(self, input_path: Union[str, Path], **kwargs):
        if not isinstance(input_path, Path):
            input_path = Path(input_path)
            
        if input_path.suffix not in self.ARCHIVE_FILE_TYPES:
            raise ValueError(f"input_path must be an archive file, not {input_path.suffix}")
        super().__init__(input_path, **kwargs)
