from json import dump
from logging import getLogger
from pathlib import Path
from typing import Union

from AutoBackupAJM import PROJECT_ROOT


class HashRecorder:
    DEFAULT_FILE_NAME = "directory_hashes.json"
    DEFAULT_RECORD_SAVE_DIR = Path(PROJECT_ROOT / "Misc_Project_Files")
    DEFAULT_RECORD_PATH = DEFAULT_RECORD_SAVE_DIR / DEFAULT_FILE_NAME

    def __init__(self, **kwargs):
        self._file_name = None
        self._record_save_dir = None
        self._logger = kwargs.get("logger", getLogger(__name__))

        self.record_path = kwargs.get("record_path", self.__class__.DEFAULT_RECORD_PATH)

    @staticmethod
    def _str_to_path(value: Union[str, Path]) -> Path:
        if isinstance(value, str):
            value: Path = Path(value)
        elif not isinstance(value, Path):
            raise TypeError("value must be a string or Path object.")
        return value

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

    def _validate_file_name(self, file_name: Union[str, Path]) -> Path:
        file_name: Path = self._str_to_path(file_name)

        if not file_name.suffix == ".json":
            raise TypeError("recorder file must be a .json file.")

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

    def hash_and_record_directory(self, **kwargs):
        directory_records = {}
        for f_path, f_hash in self.hash_directory():
            # FIXME: is this the right relative path?
            #  should it be PROJECT_ROOT or dir_path (would need to be passed in)
            #  regardless, file CONTENT will hash the same
            #  - need to figure out how to match paths if a file is moved also
            directory_records[f_hash] = f_path.relative_to(PROJECT_ROOT).as_posix()
        self._record_directory(directory_records, **kwargs)

    def _record_directory(self, directory_records: dict, **kwargs):
        # TODO: file name should default to the name of the root directory

        with open(self.record_path, "w") as f:
            dump(directory_records, fp=f,  indent=4)
            self._logger.info(f"Directory hashes recorded to {self.record_path}")
