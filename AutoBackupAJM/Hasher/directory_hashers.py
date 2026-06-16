from pathlib import Path
from typing import Generator, Tuple, Union

from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher


class DirectoryHasher(FileHasher):
    def _validate_input_path_is_dir(self) -> Path:
        if self.input_path.is_dir():
            dir_path = self.input_path
        else:
            raise ValueError(f"self.input_path must be a directory, to hash a file use hash_file")
        return dir_path

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()

        for file in dir_path.iterdir():
            if file.is_file():
                yield self.hash_file(file, **kwargs)
            else:
                # TODO: add handling for subdirectories
                print(f"Skipping subdir \'{file.resolve()}\'")


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...
