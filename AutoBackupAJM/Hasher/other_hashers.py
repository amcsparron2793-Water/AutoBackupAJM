from pathlib import Path
from typing import Union

from AutoBackupAJM.Hasher.archive_extractor import ArchiveExtractor
from AutoBackupAJM.Hasher.directory_hashers import LargeDirectoryHasher
from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


# TODO: if file is archive, option to unzip and hash contents
class ArchiveFileHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    def __init__(self, input_path: Union[str, Path], **kwargs):
        self._is_initial_file_check = True

        super().__init__(input_path, **kwargs)

        # so that ArchiveExtractor can access logger easily
        kwargs.setdefault('logger', self._logger)

        self.unzip_and_hash_contents = kwargs.get("unzip_and_hash_contents", False)
        self.extractor = ArchiveExtractor(self.input_path, **kwargs)

    @LargeFileHasher.input_path.setter
    def input_path(self, value: Union[str, Path]):
        LargeFileHasher.input_path.fset(self, value)#.input_path
        if self._is_initial_file_check:
            if self._input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
                raise ValueError(f"input_path must be an archive file, "
                                 f"not {self._input_path.suffix or 'a directory'}")
            self._is_initial_file_check = False

    @staticmethod
    def is_single_file_list(contents: list[Path]) -> tuple[bool, bool]:
        is_list = isinstance(contents, list)
        if not is_list:
            return False, False
        return is_list, (len(contents) == 1 and contents[0].is_file())

    def _handle_list(self, archive_contents: list[Path], is_single_file: bool, **kwargs):
        if is_single_file:
            return self.hash_file(archive_contents[0], **kwargs)
        else:
            raise AttributeError("use ArchiveDirectoryHasher to hash the contents of this directory")

    def _handle_path(self, archive_contents: Path, **kwargs):
        return self.hash_file(archive_contents, **kwargs)

    def _hash_contents(self, archive_contents, **kwargs):
        is_list, is_single_file = self.is_single_file_list(archive_contents)
        if is_list:
            return self._handle_list(archive_contents, is_single_file, **kwargs)
        elif isinstance(archive_contents, Path):
            return self._handle_path(archive_contents, **kwargs)
        else:
            raise TypeError("archive_contents must be a list of Path objects or a single Path object")

    def hash_archive(self, **kwargs):
        unzip_and_hash = kwargs.get("unzip_and_hash_contents", self.unzip_and_hash_contents)
        if unzip_and_hash:
            self.extractor.extract_archive()
            self._logger.info(f"Unzipped archive to {self.extractor.extract_dir}")
            return self._hash_contents(self.extractor.extract_dir, **kwargs)
        else:
            # hash as one file
            return self.hash_file(self.input_path, **kwargs)
        # raise NotImplementedError("hash_archive is not yet implemented")


class ArchiveDirectoryHasher(ArchiveFileHasher, LargeDirectoryHasher):
    # TODO: is this ever used?
    def _handle_list(self, archive_contents: list[Path], is_single_file: bool, **kwargs):
        if is_single_file:
            raise AttributeError("use ArchiveFileHasher to hash the contents of this file")
        else:
            print([x.parent for x in archive_contents])
            exit(-1)

    def _handle_path(self, archive_contents: Path, **kwargs):
        self.input_path = archive_contents
        return self.hash_directory(**kwargs)


if __name__ == "__main__":
    # TODO: functional, but needs a way to record and compare hashes -
    #  also needs to be integrated with factory and tests
    AH = ArchiveDirectoryHasher('../../Misc_Project_Files/HostedFeatureStorage.zip')
    archive_hash = AH.hash_archive(unzip_and_hash_contents=False)
    print([x for x in archive_hash])
