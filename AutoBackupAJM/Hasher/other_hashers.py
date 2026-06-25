import shutil
from logging import getLogger
from pathlib import Path
from typing import Union

from AutoBackupAJM.Hasher.directory_hashers import LargeDirectoryHasher
from AutoBackupAJM.Hasher.file_hashers import LargeFileHasher


class ArchiveExtractor:
    def __init__(self, archive_path: Path, **kwargs):
        self._extract_dir = None
        self._archive_contents = None
        self.logger = kwargs.get("logger", getLogger(__name__))

        self.archive_path = archive_path
        self.extract_dir = kwargs.get("extract_dir", None)

    @property
    def extract_dir(self):
        return self._extract_dir

    @extract_dir.setter
    def extract_dir(self, value: Union[str, Path]):
        if value is None:
            self._extract_dir = Path(self.archive_path.parent / self.archive_path.stem).resolve()
            self.logger.info(f"extract_dir not specified, defaulting to {self._extract_dir}")
        else:
            self._extract_dir = Path(value).resolve()

    @property
    def archive_contents(self):
        if self.extract_dir is not None and self.extract_dir.is_dir():
            self._archive_contents = [f for f in self.extract_dir.iterdir()]
        return self._archive_contents

    def _validate_archive_extraction(self, **kwargs):
        if self.extract_dir.is_dir():
            return self.extract_dir
        else:
            raise FileNotFoundError(f"extract_dir {self.extract_dir} does not exist")

    def extract_archive(self, **kwargs) -> Path:
        try:
            shutil.unpack_archive(self.archive_path, extract_dir=self.extract_dir)
        except (shutil.ReadError, shutil.Error):
            raise ValueError(f"archive_path {self.archive_path} is not a valid archive file")

        return self._validate_archive_extraction(**kwargs)


# TODO: if file is archive, option to unzip and hash contents
class ArchiveFileHasher(LargeFileHasher):
    ARCHIVE_FILE_TYPES = ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.7z', '.rar']

    def __init__(self, input_path: Union[str, Path], **kwargs):
        super().__init__(input_path, **kwargs)
        self.unzip_and_hash_contents = kwargs.get("unzip_and_hash_contents", False)

    @LargeFileHasher.input_path.setter
    def input_path(self, value: Union[str, Path]):
        LargeFileHasher.input_path.fset(self, value)#.input_path

        if self._input_path.suffix not in self.__class__.ARCHIVE_FILE_TYPES:
            raise ValueError(f"input_path must be an archive file, not {self._input_path.suffix}")

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