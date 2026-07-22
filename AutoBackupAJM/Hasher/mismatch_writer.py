from datetime import datetime
import json
from os import PathLike
from pathlib import Path
from typing import Tuple, Union

from AutoBackupAJM import MISC_PROJECT_DIR, SetupLogger
from AutoBackupAJM.utilities import Counter


class MismatchWriter:
    DEFAULT_MISMATCH_FILE_NAME = "mismatches.json"
    DEFAULT_MISMATCH_FILE_LOCATION = Path(MISC_PROJECT_DIR)
    MISMATCH_TIMESTAMP_FORMAT = "%Y%m%d_%H%M"

    def __init__(self, **kwargs):
        self.logger = SetupLogger.setup_logger(**kwargs)
        self.logger.name = self.__class__.__name__
        self._found_mismatch = None
        self._mismatch_entry = None
        self._mismatch_file_name = None

        self.found_mismatch = False
        self.mismatch_counter = Counter()

        self.mismatch_source = None
        self.mismatch_target = None
        self.mismatch_dict = {}

        # this is purposely set this way so that it cant be changed after initialization
        self._append_timestamp_to_file_name = kwargs.get("append_timestamp_to_file_name", True)

        self.mismatch_file_name = kwargs.get("mismatch_file_name",
                                             self.__class__.DEFAULT_MISMATCH_FILE_NAME)
        self.mismatch_file_location = kwargs.get("mismatch_file_location",
                                                 self.__class__.DEFAULT_MISMATCH_FILE_LOCATION)

    @staticmethod
    def str_to_resolved_path(value: Union[Path, str]) -> Path:
        if isinstance(value, (Path, str, PathLike)):
            value: Path = Path(value).resolve()
        else:
            raise TypeError("mismatch_file_name must be a string, Path, or PathLike object")
        return value

    @property
    def append_timestamp_to_file_name(self):
        return self._append_timestamp_to_file_name

    @property
    def mismatch_file_name(self):
        return self._mismatch_file_name

    @mismatch_file_name.setter
    def mismatch_file_name(self, value: Union[Path, str]):
        value: Path = self.str_to_resolved_path(value)
        current_ts = datetime.now().strftime(self.__class__.MISMATCH_TIMESTAMP_FORMAT)
        if self.append_timestamp_to_file_name:
            self.logger.debug(f"Appending timestamp to mismatch file name ({value.name}): {current_ts}")
            self._mismatch_file_name = f"{value.stem}_{current_ts}{value.suffix}"
        else:
            self._mismatch_file_name = value.name

    @property
    def found_mismatch(self):
        return self._found_mismatch

    @found_mismatch.setter
    def found_mismatch(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError("found_mismatch must be a boolean value")

        self._found_mismatch = value
        if value:
            self.mismatch_counter.increment()

    @property
    def mismatch_file_path(self) -> Path:
        return self.mismatch_file_location / self.mismatch_file_name

    @property
    def source_type(self) -> str:
        if self.mismatch_source is None:
            raise ValueError("mismatch_source must be set before accessing source_type")
        return "file" if Path(self.mismatch_source).suffix else "directory"

    @property
    def target_type(self) -> str:
        if self.mismatch_target is None:
            raise ValueError("mismatch_target must be set before accessing target_type")
        return "file" if Path(self.mismatch_target).suffix else "directory"

    def write_mismatches(self, **kwargs):
        if not self.mismatch_dict:
            self.logger.debug("No mismatches to write")
            return
        try:
            with open(self.mismatch_file_path, "w") as f:
                json.dump(self.mismatch_dict, f, indent=4)
            self.logger.info(f"Mismatches written to {self.mismatch_file_path}")
        except Exception as e:
            self.logger.exception(f"Error writing mismatches to {self.mismatch_file_path}: {e}")

    @property
    def mismatch_entry(self):
        return self._mismatch_entry

    @mismatch_entry.setter
    def mismatch_entry(self, value: Tuple[str, str]):
        self._mismatch_entry = {
            value[0]: {
                "source": self.mismatch_source,
                "source_type": self.source_type,
                "target": self.mismatch_target,
                "target_type": self.target_type,
                "value": value[1]
            }
        }

    def log_mismatch(self, key: str, value: str, y_name: str):
        self.logger.debug(f"Key {key} not found in {y_name}")
        self.mismatch_entry = (key, value)
        self.mismatch_dict.update(self.mismatch_entry)

        self.found_mismatch = True
        return self.found_mismatch

    def log_mismatch_counter(self):
        if self.mismatch_counter.value > 0:
            self.logger.warning(f"Found {self.mismatch_counter.value: ,} mismatches.")
