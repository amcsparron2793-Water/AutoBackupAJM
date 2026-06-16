from pathlib import Path
from typing import Union

from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


# TODO: if file is archive, option to unzip and hash contents
class ArchiveHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    def __init__(self, input_path: Union[str, Path], **kwargs):
        # if input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
        #     raise ValueError(f"input_path must be an archive file, not {input_path.suffix}")
        super().__init__(input_path, **kwargs)

    @LargeFileHasher.input_path.setter
    def input_path(self, value: Union[str, Path]):
        LargeFileHasher.input_path.fset(self, value)#.input_path

        if self._input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
            raise ValueError(f"input_path must be an archive file, not {self._input_path.suffix}")

    def hash_archive(self, **kwargs):
        # TODO: switch to enable unzip and hash contents
        raise NotImplementedError("hash_archive is not yet implemented")

