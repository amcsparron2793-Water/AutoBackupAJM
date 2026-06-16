from pathlib import Path
from typing import Optional, Union

from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


# TODO: if file is archive, option to unzip and hash contents
class ArchiveHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    # TODO: piggy back on validate_and_process_input_path
    def __new__(cls, *args, **kwargs):
        input_path: Optional[Union[str, Path]] = kwargs.pop("input_path", None)
        if not input_path:
            raise ValueError("Must specify input_path")

        if not isinstance(input_path, Path):
            input_path: Path = Path(input_path)

        if input_path.suffix in cls.ARCHIVE_FILE_TYPES:
            return cls(input_path, **kwargs)
        else:
            raise ValueError(f"input_path must be an archive file, not {input_path.suffix}")
