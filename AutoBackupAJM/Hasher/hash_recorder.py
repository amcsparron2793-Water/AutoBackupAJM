import datetime
from abc import abstractmethod, ABCMeta
from json import dump
from logging import getLogger, Logger
from os.path import commonpath
from pathlib import Path
from typing import Union, Optional

from AutoBackupAJM import PROJECT_ROOT


class _Validators:
    VALID_FILE_TYPES = ['.json']
    DEFAULT_VALID_FILE_TYPE = VALID_FILE_TYPES[0]

    @staticmethod
    def _str_to_path(value: Union[str, Path]) -> Path:
        if isinstance(value, str):
            value: Path = Path(value)
        elif not isinstance(value, Path):
            raise TypeError("value must be a string or Path object.")
        return value

    def _validate_file_name(self, file_name: Union[str, Path]) -> Path:
        file_name: Path = self._str_to_path(file_name)
        if file_name.suffix not in self.__class__.VALID_FILE_TYPES:
            raise TypeError(f"recorder file must be one of the following types: "
                            f"{', '.join(self.__class__.VALID_FILE_TYPES)}")
        self._logger.debug(f"Validated file name: {file_name}")
        return file_name

    def _validate_record_save_dir(self, dir_path: Union[str, Path]) -> Path:
        dir_path: Path = self._str_to_path(dir_path)
        if not dir_path.suffix:
            if not dir_path.is_dir():
                dir_path.mkdir(parents=True, exist_ok=True)
                self._logger.info(f"Created directory {dir_path} for recorder files.")
            return dir_path
        else:
            raise TypeError("record_save_dir must be a directory, not a file.")

    def _flatten_common_dir_filename(self, filename: Union[str, Path]) -> Path:
        filename: Path = self._str_to_path(filename)
        if len(filename.parts) > 1:
            filename = Path(filename.name)
        return filename

    def _get_common_dir_path(self, directory_records: dict) -> Optional[Path]:
        paths = [str(p) for p in directory_records.values()]
        try:
            common = Path(commonpath(paths))
            if common.suffix or common.as_posix() == '.':
                common = common.parent.resolve().name
                self._logger.debug(f"Common directory path is a file, resolving to parent: {common}")
            self._logger.debug(f"Common directory path: {common}")
            return Path(common)
        except ValueError:
            return None

    def _get_flattened_common_dir_filename(self, dir_records: dict,
                                           filename: Optional[Union[str, Path]] = None) -> Optional[Path]:
        if not filename:
            filename = self._get_common_dir_path(dir_records)
            if filename:
                filename: Path = self._flatten_common_dir_filename(filename)
                return filename
        return None

    def _validate_common_dir_filename(self, dir_records: dict, **kwargs):
        filename = kwargs.get('filename', None)
        filename = self._get_flattened_common_dir_filename(dir_records, filename)

        if filename:
            if not filename.suffix:
                self._logger.warning(f"Filename {filename} does not have a suffix, "
                                     f"adding {self.__class__.DEFAULT_VALID_FILE_TYPE}")
                filename = filename.with_suffix(self.__class__.DEFAULT_VALID_FILE_TYPE)
            return filename
        else:
            self._logger.warning("No common directory found, using default file name.")
            return None


class _Recorder(_Validators):
    DEFAULT_FILE_NAME = "directory_hashes.json"
    DEFAULT_RECORD_SAVE_DIR = Path(PROJECT_ROOT / "Misc_Project_Files")

    def __init__(self, **kwargs):
        self._logger = self._check_and_get_logger(**kwargs)
        self._file_name = None
        self._record_save_dir = None

    def _check_and_get_logger(self, **kwargs):
        # noinspection PyTypeChecker
        _logger = kwargs.get("logger", None)
        if not _logger:
            _logger: Logger = getLogger(self.__class__.__name__)
        return _logger

    @property
    def record_save_dir(self):
        return self._record_save_dir

    @record_save_dir.setter
    def record_save_dir(self, value: Union[str, Path]):
        value = self._validate_record_save_dir(value)
        self._record_save_dir = value

    @property
    def file_name(self):
        return self._file_name

    @file_name.setter
    def file_name(self, value: Union[str, Path]):
        value = self._validate_file_name(value)
        self._file_name = value

    @property
    def record_path(self):
        return self.record_save_dir / self.file_name

    def _write_directory_record_file(self, directory_records: dict, **kwargs):
        with open(self.record_path, "w") as f:
            if self.file_name.suffix == '.json':
                dump(directory_records, fp=f, indent=4)
            elif self.file_name.suffix in self.__class__.VALID_FILE_TYPES:
                raise NotImplementedError("Writing to this file type is not yet implemented.")
            else:
                raise TypeError(f"file_name must be one of the following types: "
                                f"{', '.join(self.__class__.VALID_FILE_TYPES)}")
            self._logger.info(f"Directory hashes recorded to {self.record_path}")

    def _record_directory(self, directory_records: dict, **kwargs):
        cdf = self._validate_common_dir_filename(directory_records, **kwargs)
        if cdf:
            self.file_name = cdf
            self._logger.info(f"Using common dir filename {self.file_name} for directory hashes file.")

        self._write_directory_record_file(directory_records, **kwargs)

    def _record_and_cleanup(self, directory_records: dict, start_time: datetime.datetime, **kwargs):
        self._record_directory(directory_records, **kwargs)
        end_time = datetime.datetime.now()
        self._logger.debug(f"Directory hashed and recorded in {(end_time - start_time)} .")
        return directory_records


class HashRecorder(_Recorder, _Validators, metaclass=ABCMeta):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.file_name = kwargs.get("file_name", self.__class__.DEFAULT_FILE_NAME)
        self.record_save_dir = kwargs.get("record_save_dir", self.__class__.DEFAULT_RECORD_SAVE_DIR)

    @abstractmethod
    def hash_directory(self):
        ...

    def _gen_dir_hashes(self):
        for f_path, f_hash in self.hash_directory():
            yield f_path, f_hash

    def hash_and_record_directory(self, **kwargs):
        directory_records = {}
        relative_to = Path(kwargs.get("relative_to",
                                      getattr(self, "input_path", PROJECT_ROOT))).resolve()
        start_time = datetime.datetime.now()
        try:
            for f_path, f_hash in self._gen_dir_hashes():
                directory_records[f_hash] = f_path.relative_to(relative_to).as_posix()
        except KeyboardInterrupt:
            self._logger.error("Hashing interrupted by user. Hashed files will still be written to disk.")
        except Exception as e:
            crit_log_msg = (f"An unexpected error occurred during hashing: "
                            f"\'{e.__class__.__name__}: {e}\'. "
                            f"Hashed files will still be written to disk if possible.")
            self._logger.critical(crit_log_msg, exc_info=True)
        finally:
            return self._record_and_cleanup(directory_records, start_time, **kwargs)
