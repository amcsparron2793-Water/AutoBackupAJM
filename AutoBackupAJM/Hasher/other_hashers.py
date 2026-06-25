from pathlib import Path
from typing import Union

from AutoBackupAJM.Hasher.archive_extractor import ArchiveExtractor
from AutoBackupAJM.Hasher.directory_hashers import LargeDirectoryHasher
from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


# TODO: if file is archive, option to unzip and hash contents
class ArchiveFileHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    def __init__(self, input_path: Union[str, Path], **kwargs):
        super().__init__(input_path, **kwargs)
        kwargs.setdefault('logger', self._logger)
        self.unzip_and_hash_contents = kwargs.get("unzip_and_hash_contents", False)

    @LargeFileHasher.input_path.setter
    def input_path(self, value: Union[str, Path]):
        LargeFileHasher.input_path.fset(self, value)#.input_path

        if self._input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
            raise ValueError(f"input_path must be an archive file, not {self._input_path.suffix}")
            raise ValueError(f"input_path must be an archive file, not {self._input_path.suffix or 'a directory'}")

    def hash_archive(self, **kwargs):
        unzip_and_hash = kwargs.get("unzip_and_hash_contents", self.unzip_and_hash_contents)
        if unzip_and_hash:
            raise NotImplementedError("unzip_and_hash_contents is not yet implemented")
        else:
            return self.hash_file(self.input_path, **kwargs)
        # raise NotImplementedError("hash_archive is not yet implemented")


class ArchiveDirectoryHasher(ArchiveFileHasher, LargeDirectoryHasher):
    def hash_archive(self, **kwargs):
        unzip_and_hash = kwargs.get("unzip_and_hash_contents", self.unzip_and_hash_contents)
        if unzip_and_hash:
            self.hash_directory(**kwargs)
        else:
            raise NotImplementedError("unzip_and_hash_contents is not yet implemented")


if __name__ == "__main__":
    AH = ArchiveFileHasher('../../Misc_Project_Files/HostedFeatureStorage.zip')
    archive_hash = AH.hash_archive(unzip_and_hash_contents=False)
    print(archive_hash)