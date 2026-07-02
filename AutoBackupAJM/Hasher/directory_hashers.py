from pathlib import Path
from typing import Generator, Tuple, Union
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher
from AutoBackupAJM.Hasher.hash_recorder import HashRecorder


class DirectoryHasher(FileHasher, HashRecorder):
    SYSTEM_DIR_PREFIXES = ['.', '__', 'venv']

    def __init__(self, input_path: Path, ignore_system_dirs: bool = True, **kwargs):
        self.ignore_system_dirs = ignore_system_dirs
        super().__init__(input_path, **kwargs)
        kwargs.setdefault("logger", self._logger)
        HashRecorder.__init__(self, **kwargs)

    @classmethod
    def _parent_is_system_dir(cls, dir_path: Path) -> bool:
        parent_is_system_dir = any([
            dpp.name.startswith(tuple(cls.SYSTEM_DIR_PREFIXES))
            for dpp in dir_path.parents])
        return parent_is_system_dir

    @classmethod
    def _curr_dir_is_system_dir(cls, dir_path: Path) -> bool:
        curr_dir_is_system_dir = dir_path.name.startswith(tuple(cls.SYSTEM_DIR_PREFIXES))

        return curr_dir_is_system_dir

    def _validate_input_path_is_dir(self) -> Path:
        if self.input_path.is_dir():
            dir_path = self.input_path
        else:
            raise ValueError(f"self.input_path must be a directory, to hash a file use hash_file")
        return dir_path

    def _walk_directory(self, dir_path: Path, **kwargs):
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)
        parent_counter = 0
        child_counter = 0

        for current_dir, subdirs, files in dir_path.walk(): #dir_path.iterdir():
            if ignore_system_dirs:
                if self._parent_is_system_dir(current_dir):
                    child_counter += 1
                    continue
                elif self._curr_dir_is_system_dir(current_dir):
                    self._logger.debug(f"Ignoring system directory {current_dir}")
                    parent_counter += 1
                    continue

            for file in files:
                full_path = current_dir / file
                yield full_path
        self._logger.info(f"Ignored {parent_counter: ,} parent directories "
                          f"and {child_counter: ,} child directories.")

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()
        self._logger.info(f"Hashing directory {dir_path.resolve()}.")
        kwargs.setdefault("ignore_system_dirs", self.ignore_system_dirs)

        # TODO: multithreading?
        for fp in self._walk_directory(dir_path, **kwargs):
            yield self.hash_file(fp, **kwargs)

    def hash_and_record_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        kwargs.setdefault("relative_to", self.input_path.parent)
        return super().hash_and_record_directory(**kwargs)


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("~/Desktop").expanduser())#Path("../../logs"))
    for x in dir_hasher.hash_and_record_directory():
        ...
        #print(x)
    # for x in dir_hasher.hash_directory():
    #     print(x[1])
