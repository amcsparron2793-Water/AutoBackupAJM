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
        self.extractor = ArchiveExtractor(self.input_path, **kwargs)

    @LargeFileHasher.input_path.setter
    def input_path(self, value: Union[str, Path]):
        LargeFileHasher.input_path.fset(self, value)#.input_path

        if self._input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
            raise ValueError(f"input_path must be an archive file, "
                             f"not {self._input_path.suffix or 'a directory'}")

    def _hash_contents(self, archive_contents, **kwargs):
        if isinstance(archive_contents, list):
            if len(archive_contents) == 1 and archive_contents[0].is_file():
                return self.hash_file(archive_contents[0], **kwargs)
            else:
                raise AttributeError("use ArchiveDirectoryHasher to hash the contents")
        elif isinstance(archive_contents, Path):
            return self.hash_file(archive_contents, **kwargs)
        else:
            raise TypeError("archive_contents must be a list of Path objects or a single Path object")

    def hash_archive(self, **kwargs):
        unzip_and_hash = kwargs.get("unzip_and_hash_contents", self.unzip_and_hash_contents)
        if unzip_and_hash:
            self.extractor.extract_archive()
            return self._hash_contents(self.extractor.extract_dir, **kwargs)
        else:
            # hash as one file
            return self.hash_file(self.input_path, **kwargs)
        # raise NotImplementedError("hash_archive is not yet implemented")


class ArchiveDirectoryHasher(ArchiveFileHasher, LargeDirectoryHasher):
    def _hash_contents(self, archive_contents, **kwargs):
        if isinstance(archive_contents, list):
            if len(archive_contents) == 1 and archive_contents[0].is_file():
                raise AttributeError("use ArchiveFileHasher to hash the contents")
        elif isinstance(archive_contents, Path):
            # FIXME: this causes ValueError: input_path must be an archive file, not a directory
            self.input_path = archive_contents
        return self.hash_directory(**kwargs)


if __name__ == "__main__":
    AH = ArchiveDirectoryHasher('../../Misc_Project_Files/HostedFeatureStorage.zip')
    archive_hash = AH.hash_archive(unzip_and_hash_contents=True)
    print([x for x in archive_hash])