from tqdm import tqdm

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

    def _count_and_continue(self, parent_counter: int, child_counter: int,
                            current_dir: Path, **kwargs) -> Tuple[int, int, bool]:
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)

        if ignore_system_dirs:
            if self._parent_is_system_dir(current_dir):
                child_counter += 1
                return child_counter, parent_counter, True
            elif self._curr_dir_is_system_dir(current_dir):
                self._logger.debug(f"Ignoring system directory {current_dir}")
                parent_counter += 1
                return parent_counter, child_counter, True

        return parent_counter, child_counter, False

    @staticmethod
    def _gen_walk_full_dir_path(current_dir: Path, files: list):
        for file in files:
            full_path = current_dir / file
            yield full_path

    def _walk_directory(self, dir_path: Path, **kwargs):
        parent_counter = 0
        child_counter = 0
        total_counter = 0

        for current_dir, subdirs, files in dir_path.walk(): #dir_path.iterdir():
            # see if we should continue walking
            parent_counter, child_counter, should_continue = self._count_and_continue(
                parent_counter, child_counter, current_dir, **kwargs
            )
            if should_continue:
                total_counter += 1
                continue

            yield from self._gen_walk_full_dir_path(current_dir, files)
        self._logger.info(f"Ignored a total of {total_counter: ,} directories,"
                          f" including {parent_counter: ,} parent directories "
                          f"and {child_counter: ,} child directories.")

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()
        self._logger.info(f"Hashing directory {dir_path.resolve()}.")
        kwargs.setdefault("ignore_system_dirs", self.ignore_system_dirs)

        # TODO: multithreading?
        # TODO: tqdm?

        # total_files = [x for x in self._walk_directory(dir_path, **kwargs)]
        # print(len(total_files))

        # TODO: this works, but does not have any real progress bar
        #  need to figure out a way to efficiently count to get a total first
        for fp in tqdm(self._walk_directory(dir_path, **kwargs), #total=total_files,
                       desc=f"Hashing directory {dir_path.name}", unit=" files"):
            yield self.hash_file(fp, **kwargs)

    def hash_and_record_directory(self, **kwargs) -> dict: #Generator[Tuple[Union[Path, str], str], None, None]:
        kwargs.setdefault("relative_to", self.input_path.parent)
        return super().hash_and_record_directory(**kwargs)


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("~/Desktop").expanduser())#Path("../../logs"))
    hr = dir_hasher.hash_and_record_directory()
        #print(x)
    # for x in dir_hasher.hash_directory():
    #     print(x[1])
