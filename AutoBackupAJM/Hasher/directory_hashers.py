from json import dumps, dump
from pathlib import Path
from typing import Generator, Tuple, Union
from AutoBackupAJM import PROJECT_ROOT
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher


class DirectoryHasher(FileHasher):
    SYSTEM_DIR_PREFIXES = ['.', '__']

    def __init__(self, input_path: Path, ignore_system_dirs: bool = True, **kwargs):
        self.ignore_system_dirs = ignore_system_dirs
        super().__init__(input_path, **kwargs)
        kwargs.setdefault("logger", self._logger)
        HashRecorder.__init__(self, **kwargs)

    @classmethod
    def _is_system_dir(cls, dir_path: Path) -> bool:
        return dir_path.name.startswith(tuple(cls.SYSTEM_DIR_PREFIXES))

    def _validate_input_path_is_dir(self) -> Path:
        if self.input_path.is_dir():
            dir_path = self.input_path
        else:
            raise ValueError(f"self.input_path must be a directory, to hash a file use hash_file")
        return dir_path

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()
        self._logger.info(f"Hashing directory {dir_path.resolve()}.")
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)

        # TODO: walk needs to be relative to the root dir
        #  since the root dir is always going to be
        #  different since the source is from a backup.

        # TODO: multithreading?
        for current_dir, subdirs, files in dir_path.walk(): #dir_path.iterdir():
            if ignore_system_dirs:
                if self._is_system_dir(current_dir):
                    continue
            for file in files:
                full_path = current_dir / file
                yield self.hash_file(full_path, **kwargs)


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("../"))
    for x in dir_hasher.hash_directory():
        print(x[1])
