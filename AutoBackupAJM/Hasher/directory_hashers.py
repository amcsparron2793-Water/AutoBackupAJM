from tqdm import tqdm

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Generator, Tuple, Union, List, Optional, Iterable, Set
import threading
from AutoBackupAJM.utilities import Counter
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher
from AutoBackupAJM.Hasher.hash_recorder import HashRecorder


class DirectoryHasher(FileHasher, HashRecorder):
    SYSTEM_DIR_PREFIXES = ['.', '__', 'venv']

    def __init__(self, input_path: Path, ignore_system_dirs: bool = True, **kwargs):
        self.ignore_system_dirs = ignore_system_dirs
        super().__init__(input_path, **kwargs)
        kwargs.setdefault("logger", self._logger)
        HashRecorder.__init__(self, **kwargs)
        self.multithreaded = kwargs.get("multithreaded", True)

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

    def _count_and_continue(self, parent_counter: Counter, child_counter: Counter,
                            current_dir: Path, **kwargs) -> Tuple[Counter, Counter, bool]:
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)

        if ignore_system_dirs:
            if current_dir.name.startswith(tuple(self.SYSTEM_DIR_PREFIXES)):
                self._logger.debug(f"Ignoring system directory {current_dir}")
                parent_counter.increment()
                return parent_counter, child_counter, True
            elif self._parent_is_system_dir(current_dir):
                child_counter.increment()
                return child_counter, parent_counter, True

        return parent_counter, child_counter, False

    @staticmethod
    def _gen_walk_full_dir_path(current_dir: Path, files: list):
        for file in files:
            full_path = current_dir / file
            yield full_path

    def _walk_directory(self, dir_path: Path, **kwargs) -> Generator[Path, None, None]:
        multithreaded = kwargs.get("multithreaded", self.multithreaded)
        if multithreaded:
            yield from self._mt_walk_directory(dir_path, **kwargs)
        else:
            yield from self._st_walk_directory(dir_path, **kwargs)

    def _st_walk_directory(self, dir_path: Path, **kwargs) -> Generator[Path, None, None]:
        # TODO: HERE
        parent_counter = Counter()
        child_counter = Counter()
        total_counter = Counter()

        for current_dir, subdirs, files in dir_path.walk():  #dir_path.iterdir():
            # see if we should continue walking
            parent_counter, child_counter, should_continue = self._count_and_continue(
                parent_counter, child_counter, current_dir, **kwargs
            )
            if should_continue:
                total_counter.increment()
                continue

            yield from self._gen_walk_full_dir_path(current_dir, files)
        self._logger.info(f"Ignored a total of {total_counter: ,} directories,"
                          f" including {parent_counter: ,} parent directories "
                          f"and {child_counter: ,} child directories.")

    def _mt_walk_directory(self, dir_path: Path, **kwargs) -> Generator[Path, None, None]:
        max_workers = kwargs.get("max_workers", None)
        ignore_system_dirs = kwargs.get("ignore_system_dirs", self.ignore_system_dirs)

        files_list = []
        files_lock = threading.Lock()
        # TODO: HERE
        parent_counter = Counter()
        child_counter = Counter()
        total_counter = Counter()
        counter_lock = threading.Lock()

        def process_dir(current_dir: Path):
            nonlocal parent_counter, child_counter, total_counter
            
            # Check if this directory should be ignored
            if ignore_system_dirs:
                if self._curr_dir_is_system_dir(current_dir):
                    self._logger.debug(f"Ignoring system directory {current_dir}")
                    with counter_lock:
                        parent_counter.increment()
                        total_counter.increment()
                    return []
                elif self._parent_is_system_dir(current_dir):
                    with counter_lock:
                        child_counter.increment()
                        total_counter.increment()
                    return []

            try:
                # We only want files in the current dir, and subdirs to be processed by other tasks
                # But wait, if we use path.walk() here, it will walk the whole subtree.
                # If we want to multithread the walk, we should probably do it level by level or 
                # use a queue.
                
                # Using os.scandir or Path.iterdir for finer control
                local_files = []
                subdirs = []
                for entry in current_dir.iterdir():
                    if entry.is_file():
                        local_files.append(entry)
                    elif entry.is_dir():
                        subdirs.append(entry)
                
                if local_files:
                    with files_lock:
                        files_list.extend(local_files)
                
                return subdirs
            except PermissionError:
                self._logger.warning(f"Permission denied: {current_dir}")
                return []
            except Exception as e:
                self._logger.error(f"Error walking {current_dir}: {e}")
                return []

        pending_dirs = [dir_path]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while pending_dirs:
                futures = [executor.submit(process_dir, d) for d in pending_dirs]
                pending_dirs = []
                for future in as_completed(futures):
                    subdirs = future.result()
                    pending_dirs.extend(subdirs)

        self._logger.info(f"Ignored a total of {total_counter.value: ,} directories,"
                          f" including {parent_counter.value: ,} parent directories "
                          f"and {child_counter.value: ,} child directories.")
        
        yield from files_list

    def _get_files_with_count(self, dir_path, **kwargs) -> Tuple[List[Union[Path, str]], int]:
        self._logger.info("walking directory for file paths and count...")
        files = [x for x in self._walk_directory(dir_path, **kwargs)]
        total_files = len(files)
        self._logger.info(f"Found {total_files:,} files to hash.")
        return files, total_files

    def _get_progress_bar(self, file_list: List[Union[Path, str]], **kwargs):
        dir_path_name = kwargs.get('dir_path_name', '')
        description = kwargs.get('description', f"Hashing directory {dir_path_name}")
        total_files = len(file_list)
        unit = kwargs.get('unit', ' files')

        progress_bar = tqdm(total=total_files,
                            desc=description,
                            unit=unit)
        return progress_bar

    def _setup_and_get_progress_bar(self, dir_path: Path, **kwargs) -> Tuple[Optional[tqdm], int, Optional[List[Union[Path, str]]]]:
        use_progress_bar = kwargs.get("use_progress_bar", True)
        if use_progress_bar:
            files, total_files = self._get_files_with_count(dir_path, **kwargs)
        else:
            files = None  # self._walk_directory(dir_path, **kwargs)
            total_files = -1

        progress_bar = self._get_progress_bar(files, dir_path_name=dir_path.name) if files else None
        return progress_bar, total_files, files

    def _mt_hash_directory(self, fp_iterable: Iterable,
                           max_workers: Optional[int],
                           progress_bar: Optional[tqdm] = None,
                           **kwargs):
        # TODO: make this work for self._get_files_with_count
        # Consume the iterable to get all file paths if we haven't already
        if not isinstance(fp_iterable, list):
            fp_list = list(fp_iterable)
            self._logger.debug("converted iterable to list for multithreading")
        else:
            fp_list = fp_iterable

        self._logger.info("Starting multithreaded hashing...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We need to be careful with kwargs and progress_bar
            # hash_file uses its own progress bar if not careful, but here it's fine
            future_to_fp = {executor.submit(self.hash_file, fp, **kwargs): fp for fp in fp_list}
            for future in as_completed(future_to_fp):
                yield future.result()
                if progress_bar:
                    progress_bar.update(1)

    def _st_hash_directory(self, fp_iterable: Iterable, progress_bar: Optional[tqdm] = None, **kwargs):
        for fp in fp_iterable:
            if progress_bar:
                progress_bar.update(1)
            yield self.hash_file(fp, **kwargs)

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()
        kwargs.setdefault("ignore_system_dirs", self.ignore_system_dirs)
        kwargs.setdefault("use_progress_bar", True)

        multithreaded = kwargs.get("multithreaded", self.multithreaded)
        max_workers = kwargs.get("max_workers", None)
        self._logger.debug("multithreaded: %s, max_workers: %s", multithreaded, max_workers)

        self._logger.info(f"Hashing directory {dir_path.resolve()}")

        progress_bar, total_files, files = self._setup_and_get_progress_bar(dir_path, **kwargs)

        self._logger.info(f"Hashing {total_files:,} files in directory {dir_path.name}.")
        fp_iterable = files if files else self._walk_directory(dir_path, **kwargs)

        if multithreaded:
            self._logger.info("Hashing files in parallel...")
            yield from self._mt_hash_directory(fp_iterable, max_workers, progress_bar, **kwargs)
        else:
            self._logger.info("Hashing files sequentially...")
            yield from self._st_hash_directory(fp_iterable, progress_bar, **kwargs)

    def hash_and_record_directory(self, **kwargs) -> dict:  #Generator[Tuple[Union[Path, str], str], None, None]:
        kwargs.setdefault("relative_to", self.input_path.parent)
        return super().hash_and_record_directory(**kwargs)


class LargeDirectoryHasher(LargeFileHasher, DirectoryHasher):
    ...


if __name__ == "__main__":
    dir_hasher = DirectoryHasher(Path("~/Desktop/ArcMap and Pro Projects").expanduser())  #Path("../../logs"))
    hr = dir_hasher.hash_and_record_directory()
    #print(x)
    # for x in dir_hasher.hash_directory():
    #     print(x[1])
