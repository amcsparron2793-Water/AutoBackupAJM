import json
from abc import abstractmethod, ABCMeta
from pathlib import Path
from typing import Union, List, Tuple, Optional
from AutoBackupAJM import SetupLogger
from AutoBackupAJM.Hasher.archive_hashers import ArchiveDirectoryHasher
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher


class _BaseHashComparer(metaclass=ABCMeta):
    DEFAULT_SOURCE_NAME = "source_file"
    DEFAULT_TARGET_NAME = "target_file"

    def __init__(self, **kwargs):
        self._source_name = None
        self._target_name = None
        self._delay_hashing = None

        self.mismatch_dict = {}

        self.stop_on_first_mismatch = kwargs.get("stop_on_first_mismatch", False)
        self.write_mismatches_to_file = kwargs.get("write_mismatches_to_file", True)

        self.logger = self.setup_logger(**kwargs)
        self.source_name = kwargs.get("source_name", self.__class__.DEFAULT_SOURCE_NAME)
        self.target_name = kwargs.get("target_name", self.__class__.DEFAULT_TARGET_NAME)

    @abstractmethod
    def source_target_contents_match(self):
        ...

    @classmethod
    def setup_logger(cls, **kwargs):
        logger = SetupLogger.setup_logger(**kwargs)
        logger.name = cls.__name__
        logger.info(f"Initializing {cls.__name__}")
        return logger

    @property
    def source_name(self):
        return self._source_name

    @source_name.setter
    def source_name(self, value):
        self._source_name = value
        self._set_name_for_jj(value, "source_name")

    @property
    def target_name(self):
        return self._target_name

    @target_name.setter
    def target_name(self, value):
        self._target_name = value
        self._set_name_for_jj(value, "target_name")

    @property
    def delay_hashing(self):
        return self._delay_hashing

    @delay_hashing.setter
    def delay_hashing(self, value):
        self._delay_hashing = value
        if self._delay_hashing:
            self.logger.warning("delay_hashing is set to True, "
                                "archive will not be hashed until compare() is called.")
        else:
            self.logger.debug(f"delay_hashing is set to {self._delay_hashing}")

    def _set_name_for_jj(self, value, name_attr_to_set):
        if hasattr(self, 'jj_hashcomp'):
            self.logger.debug(f"Setting {name_attr_to_set} to {value} for {self.__class__.__name__}")
            setattr(self.jj_hashcomp, name_attr_to_set, value)
            return
        elif isinstance(self, JsonToJsonHashComparer):
            self.logger.debug(f"setting {name_attr_to_set} to {value} for {self.__class__.__name__}")
            self.__setattr__(f"_{name_attr_to_set}", value)
            return
        self.logger.debug(f"No jj_hashcomp attribute found for {self.__class__.__name__}")

    def _convert_to_path(self, value: Union[str, Path], **kwargs):
        self.logger.warning(f"attempting to convert {type(value).__name__} to Path object...")
        if isinstance(value, str):
            return Path(value)
        elif isinstance(value, Path):
            return value
        else:
            raise TypeError(f"value must be a string or a Path object, not {type(value).__name__}")

    def _write_mismatches(self):
        # TODO: needs better file name and error handling
        if self.write_mismatches_to_file:
            with open("mismatches.json", "w") as f:
                json.dump(self.mismatch_dict, f, indent=4)
            self.logger.info("Mismatches written to mismatches.json")

    def _log_mismatch(self, key: str, value: str, y_name: str):
        self.logger.error(f"Key {key} not found in {y_name}")
        self.mismatch_dict[key] = {"source": self.source_name,
                                   "target": self.target_name,
                                   "value": value}
        found_mismatch = True
        return found_mismatch

    def _all_x_keys_in_y_keys(self, x: dict, y: dict, y_name: str, **kwargs):
        stop_on_first_mismatch = kwargs.get("stop_on_first_mismatch", self.stop_on_first_mismatch)
        write_mismatches_to_file = kwargs.get("write_mismatches_to_file", self.write_mismatches_to_file)
        found_mismatch = False

        for key, value in x.items():
            if key not in y.keys():
                found_mismatch = self._log_mismatch(key, value, y_name=y_name)

                if stop_on_first_mismatch:
                    return False
                else:
                    continue

        if write_mismatches_to_file:
            self._write_mismatches()
        return not found_mismatch

    def compare(self):
        if not self.source_target_contents_match():
            return False
        self.logger.info("All keys found in both JSON files.")
        return True


# TODO: Integrate with AutoBackup
class JsonToJsonHashComparer(_BaseHashComparer):
    def __init__(self, source_json: Optional[Union[list, dict, Path]],
                 target_json: Optional[Union[list, dict, Path]],
                 **kwargs):
        super().__init__(**kwargs)
        kwargs.setdefault('logger', self.logger)

        self._source_json = None
        self._target_json = None

        self.source_json = source_json
        self.target_json = target_json

    def _get_json(self, value: Union[Path, list, dict], **kwargs):
        if value:
            if isinstance(value, Path):
                value = self._load_json(value, **kwargs)
            elif isinstance(value, (list, dict)):
                # just pass it through
                pass
            else:
                raise TypeError(f"value must be a Path or a list or a dict, not {type(value).__name__}")
        return value

    def _load_json(self, path_to_json: Path, **kwargs):
        if isinstance(path_to_json, Path):
            try:
                with open(path_to_json, 'r') as f:
                    if path_to_json.suffix == '.json':
                        return json.load(f)
                    raise ValueError(f"File {path_to_json} is not a JSON file")
            except FileNotFoundError:
                self.logger.error(f"File {path_to_json} not found")
                raise
            except json.JSONDecodeError:
                self.logger.error(f"File {path_to_json} is not a valid JSON file")
                raise
            except Exception as e:
                self.logger.error(f"Error loading JSON file {path_to_json}: {e}")
                raise
        else:
            try:
                raise TypeError("path_to_json must be a Path")
            except TypeError as e:
                self.logger.error(f"TypeError: {e}")
                path_to_json = self._convert_to_path(path_to_json, **kwargs)
                return self._load_json(path_to_json, **kwargs)

    @property
    def target_json(self):
        return self._target_json

    @target_json.setter
    def target_json(self, value):
        if isinstance(value, Path):
            self.target_name = value.name
        self._target_json = self._get_json(value)

    @property
    def source_json(self):
        return self._source_json

    @source_json.setter
    def source_json(self, value):
        if isinstance(value, Path):
            self.source_name = value.name
        self._source_json = self._get_json(value)

    def _all_source_in_target(self):
        return self._all_x_keys_in_y_keys(x=self.source_json,
                                          y=self.target_json,
                                          y_name=self.target_name)

    def _all_target_in_source(self):
        return self._all_x_keys_in_y_keys(x=self.target_json,
                                          y=self.source_json,
                                          y_name=self.source_name)

    def source_target_contents_match(self):
        return self._all_source_in_target() and self._all_target_in_source()


class JsonToArchiveComparer(_BaseHashComparer):
    def __init__(self, archive_file: Path, source_json: Union[Path, List[dict], dict], **kwargs):
        super().__init__(**kwargs)
        kwargs.setdefault('logger', self.logger)

        self._archive_hash = None

        self.source_json = source_json
        self.archive_file, self.archive_hasher, kwargs = self.setup_archive_hasher(archive_file, **kwargs)

        self.jj_hashcomp = JsonToJsonHashComparer(source_json=self.source_json,
                                                  target_json=None if self.delay_hashing else self.archive_hash,
                                                  **kwargs)

        self.target_name = self.archive_file.name

    def source_target_contents_match(self):
        return self.jj_hashcomp.source_target_contents_match()

    def compare(self):
        if self.delay_hashing or self.archive_hash is None or self.jj_hashcomp.target_json is None:
            self.jj_hashcomp.target_json = self.archive_hash
            self.delay_hashing = False
        return self.jj_hashcomp.compare()

    @property
    def archive_hash(self) -> Union[dict, List[dict]]:
        if self._archive_hash is None:
            self.logger.info(f"Hashing archive file {self.archive_file.name}")
            self._archive_hash = self.archive_hasher.hash_archive()
        # noinspection PyTypeChecker
        return self._archive_hash

    def setup_archive_hasher(self, archive_file: Path, **kwargs) -> Tuple[Path, ArchiveDirectoryHasher, dict]:
        kwargs.setdefault('unzip_and_hash_contents', True)
        kwargs.setdefault('preserve_archive', False)
        archive_hasher = ArchiveDirectoryHasher(input_path=archive_file, **kwargs)
        self.logger.info(f"Archive hasher initialized for {archive_file.name}")
        return archive_file, archive_hasher, kwargs


class ArchiveToArchiveComparer(JsonToArchiveComparer, _BaseHashComparer):
    def __init__(self, source_archive_file: Path, target_archive_file: Path, **kwargs):
        self._source_archive_hash = None
        self._delay_hashing = None

        _BaseHashComparer.__init__(self, **kwargs)
        kwargs.setdefault('logger', self.logger)

        self.source_archive_file = source_archive_file
        self.target_archive_file = target_archive_file

        (self.source_archive_file,
         self.source_archive_hasher,
         kwargs) = self.setup_archive_hasher(archive_file=self.source_archive_file, **kwargs)
        # noinspection PyTypeChecker
        super().__init__(source_json=None if self.delay_hashing else self.source_archive_hash,
                         archive_file=self.target_archive_file, **kwargs)

        self.source_name = kwargs.get("source_name", self.source_archive_file.name)
        self.target_name = kwargs.get("target_name", self.target_archive_file.name)

    @property
    def source_archive_hash(self) -> Union[dict, List[dict]]:
        if self._source_archive_hash is None:
            self.logger.info(f"Hashing archive file {self.source_archive_file.name}")
            self._source_archive_hash = self.source_archive_hasher.hash_archive()
        # noinspection PyTypeChecker
        return self._source_archive_hash

    def compare(self):
        if self.delay_hashing or self.source_archive_hash is None:
            self.jj_hashcomp.source_json = self.source_archive_hash
            self.delay_hashing = False
        return super().compare()


class JsonToDirectoryComparer(_BaseHashComparer):
    def __init__(self, source_json: Path, target_dir: Path, **kwargs):
        super().__init__(**kwargs)
        kwargs.setdefault('logger', self.logger)
        self._delay_hashing = None
        self._directory_hash = None

        self.source_json = source_json
        self.target_dir = target_dir
        self.directory_hasher = DirectoryHasher(input_path=self.target_dir, **kwargs)

        self.jj_hashcomp = JsonToJsonHashComparer(source_json=self.source_json,
                                                  target_json=None if self.delay_hashing else self.directory_hash,
                                                  **kwargs)

        self.source_name = self.source_json.name
        self.target_name = self.target_dir.name

    @property
    def directory_hash(self):
        if not self._directory_hash:
            self._directory_hash = self.directory_hasher.hash_and_record_directory()
        return self._directory_hash

    def source_target_contents_match(self):
        return self.jj_hashcomp.source_target_contents_match()

    def compare(self):
        if self.delay_hashing or self.directory_hash is None:
            self.jj_hashcomp.target_json = self.directory_hash
            self.delay_hashing = False
        return self.jj_hashcomp.compare()


class _QuickTest:
    test_backup_json = Path("../../Misc_Project_Files/HostedFeatureStorage.json")
    test_new_zip = Path("../../Misc_Project_Files/HostedFeatureStorage.zip")
    test_other_zip = Path("../../Misc_Project_Files/HostedFeatureStorage_Other.zip")
    test_new_json = Path("../../Misc_Project_Files/HostedFeatureStorage_Other.json")
    test_dir_json = Path("../../Misc_Project_Files/Desktop_backup.json")
    test_target_dir = Path("~/Desktop").expanduser()
    # test_target_dir = Path("../../Misc_Project_Files")#.expanduser()

    def __init__(self, jj=False, ja=False, aa=False, jd=False, **kwargs):
        self.hc = None
        self.jj = jj
        self.ja = ja
        self.aa = aa
        self.jd = jd

        self.comparer_to_use = [x for x in [self.jj, self.ja, self.aa, self.jd] if x]

        if len(self.comparer_to_use) > 1:
            raise ValueError("Only one hasher can be used at a time")

    def get_hc(self, **kwargs):
        if self.jj:
            self.hc = JsonToJsonHashComparer(source_json=self.test_backup_json,
                                             target_json=self.test_new_json,
                                             # FIXME: setting source name like this doesnt seem to work?
                                             # source_name="totally_not_the_real_name",
                                             **kwargs)
        elif self.ja:
            self.hc = JsonToArchiveComparer(source_json=self.test_backup_json,
                                            archive_file=self.test_new_zip,
                                            **kwargs)
        elif self.aa:
            self.hc = ArchiveToArchiveComparer(source_archive_file=self.test_new_zip,
                                               target_archive_file=self.test_other_zip,
                                               **kwargs)
        elif self.jd:
            self.hc = JsonToDirectoryComparer(source_json=self.test_dir_json,
                                              target_dir=self.test_target_dir,
                                              **kwargs)

    def compare_test(self):
        if self.hc:
            self.hc.compare()
        else:
            raise AttributeError("No hasher initialized")


if __name__ == '__main__':
    qt = _QuickTest(jd=True)
    qt.get_hc()
    qt.compare_test()
