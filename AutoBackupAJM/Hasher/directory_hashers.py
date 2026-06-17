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
        print(f"Hashing directory {dir_path.resolve()}.")

        # TODO: walk needs to be relative to the root dir
        #  since the root dir is always going to be
        #  different since the source is from a backup.

        # TODO: multithreading?
        for current_dir, subdirs, files in dir_path.walk(): #dir_path.iterdir():
            if current_dir.name.startswith("__"):
                continue
            for file in files:
                full_path = current_dir / file
                yield self.hash_file(full_path, **kwargs)

            # OLD: this does work
            # if file.is_file():
            #     yield self.hash_file(file, **kwargs)
            # else:
            #     # See rework above: add handling for subdirectories
            #     print(f"Skipping subdir \'{file.resolve()}\'")


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("../"))
    for x in dir_hasher.hash_directory():
        print(x[1])
