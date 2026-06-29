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

    @classmethod
    def _is_system_dir(cls, dir_path: Path) -> bool:
        return dir_path.name.startswith(tuple(cls.SYSTEM_DIR_PREFIXES))

    def _validate_input_path_is_dir(self) -> Path:
        if self.input_path.is_dir():
            dir_path = self.input_path
        else:
            raise ValueError(f"self.input_path must be a directory, to hash a file use hash_file")
        return dir_path

    def _walk_directory(self, dir_path: Path, **kwargs):
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)
        for current_dir, subdirs, files in dir_path.walk(): #dir_path.iterdir():
            if ignore_system_dirs:
                if self._is_system_dir(current_dir):
                    continue
            for file in files:
                full_path = current_dir / file
                yield full_path

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()
        self._logger.info(f"Hashing directory {dir_path.resolve()}.")
        kwargs.setdefault("ignore_system_dirs", self.ignore_system_dirs)

        # TODO: walk needs to be relative to the root dir
        #  since the root dir is always going to be
        #  different since the source is from a backup.

        # TODO: multithreading?
        for fp in self._walk_directory(dir_path, **kwargs):
            yield self.hash_file(fp, **kwargs)

    def hash_and_record_directory(self, **kwargs):
        directory_records = {}
        for f_path, f_hash in self.hash_directory():
            directory_records[f_hash] = f_path.as_posix()
        self._record_directory(directory_records, **kwargs)

    def _record_directory(self, directory_records: dict, **kwargs):
        default_file_name = "directory_hashes.json"
        default_record_path = Path(PROJECT_ROOT / "Misc_Project_Files"/ default_file_name)
        record_path = kwargs.get("record_path", default_record_path)
        with open(record_path, "w") as f:
            dump(directory_records, fp=f,  indent=4)
            self._logger.info(f"Directory hashes recorded to {record_path}")


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("../../Logs"))
    dir_hasher.hash_and_record_directory()
    # for x in dir_hasher.hash_directory():
    #     print(x[1])
