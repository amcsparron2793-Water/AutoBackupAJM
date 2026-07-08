import json
from pathlib import Path
from typing import Union, List, Tuple, Optional
from AutoBackupAJM import SetupLogger
from AutoBackupAJM.Hasher.archive_hashers import ArchiveDirectoryHasher
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher


# TODO: Integrate with AutoBackup
class JsonToJsonHashComparer:
    def __init__(self, source_json: Optional[Union[list, dict, Path]],
                 target_json: Optional[Union[list, dict, Path]], **kwargs):
        self._source_json = None
        self._target_json = None

        self.source_name = kwargs.get("source_name", "source_json")
        self.target_name = kwargs.get("target_name", "target_json")

        self.logger = self.setup_logger(**kwargs)
        self.source_json = source_json
        self.target_json = target_json

    @classmethod
    def setup_logger(cls, **kwargs):
        logger = SetupLogger.setup_logger(**kwargs)
        logger.name = cls.__name__
        logger.info(f"Initializing {cls.__name__}")
        return logger

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

    @staticmethod
    def _load_json(path_to_json: Path, **kwargs):
        if isinstance(path_to_json, Path):
            with open(path_to_json, 'r') as f:
                if path_to_json.suffix == '.json':
                    return json.load(f)
                raise ValueError(f"File {path_to_json} is not a JSON file")
        else:
            raise TypeError("path_to_json must be a Path")

    @property
    def target_json(self):
        return self._target_json

    @target_json.setter
    def target_json(self, value):
        self._target_json = self._get_json(value)

    @property
    def source_json(self):
        return self._source_json

    @source_json.setter
    def source_json(self, value):
        self._source_json = self._get_json(value)

    def _all_source_in_target(self):
        for key, value in self.source_json.items():
            if key not in self.target_json:
                self.logger.error(f"Key {key} not found in {self.target_name}")
                return False
        return True

    def _all_target_in_source(self):
        for key, value in self.target_json.items():
            if key not in self.source_json:
                self.logger.error(f"Key {key} not found in {self.source_name}")
                return False
        return True

    def source_target_contents_match(self):
        return self._all_source_in_target() and self._all_target_in_source()

    def compare(self):
        if not self.source_json or not self.target_json:
            raise ValueError("source_json and target_json cannot be None")

        if not self.source_target_contents_match():
            return False
        self.logger.info("All keys found in both JSON files.")
        return True


class JsonToArchiveComparer:
    def __init__(self, archive_file: Path, source_json: Union[Path, List[dict], dict], **kwargs):
        self._archive_hash = None
        self._delay_hashing = None
        self.logger = JsonToJsonHashComparer.setup_logger(**kwargs)
        kwargs.setdefault('logger', self.logger)

        self.source_json = source_json
        self.jj_hashcomp = JsonToJsonHashComparer(source_json=self.source_json,
                                                  target_json=None, **kwargs)

        self.delay_hashing = kwargs.get("delay_hashing", True)

        self.archive_file, self.archive_hasher, kwargs = self.setup_archive_hasher(archive_file, **kwargs)

        kwargs.setdefault('target_name', self.archive_file.name)

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

    def compare(self):
        self.jj_hashcomp.target_json = self.archive_hash
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


class ArchiveToArchiveComparer(JsonToArchiveComparer):
    def __init__(self, source_archive_file: Path, target_archive_file: Path, **kwargs):
        self._source_archive_hash = None
        self._delay_hashing = None
        self.logger = JsonToJsonHashComparer.setup_logger(**kwargs)
        kwargs.setdefault('logger', self.logger)

        self.source_archive_file = source_archive_file
        self.target_archive_file = target_archive_file

        (self.source_archive_file,
         self.source_archive_hasher,
         kwargs) = self.setup_archive_hasher(archive_file=self.source_archive_file, **kwargs)
        # noinspection PyTypeChecker
        super().__init__(source_json=self.source_archive_hash,
                         archive_file=self.target_archive_file, **kwargs)

    @property
    def source_archive_hash(self) -> Union[dict, List[dict]]:
        if self._source_archive_hash is None:
            self.logger.info(f"Hashing archive file {self.source_archive_file.name}")
            self._source_archive_hash = self.source_archive_hasher.hash_archive()
        # noinspection PyTypeChecker
        return self._source_archive_hash


class JsonToDirectoryComparer:
    def __init__(self, source_json: Path, target_dir: Path, **kwargs):
        self._source_dir_hash = None
        self._delay_hashing = None
        self.logger = JsonToJsonHashComparer.setup_logger(**kwargs)
        kwargs.setdefault('logger', self.logger)

        self.source_json = source_json
        self.target_dir = target_dir
        self.directory_hasher = DirectoryHasher(input_path=self.target_dir, **kwargs)
        self.directory_hash = self.directory_hasher.hash_and_record_directory(**kwargs)

        self.jj_hashcomp = JsonToJsonHashComparer(source_json=self.source_json,
                                                  target_json=self.directory_hash, **kwargs)

        self.delay_hashing = kwargs.get("delay_hashing", True)

    # TODO: make this a part of a base class or something?
    def compare(self):
        self.jj_hashcomp.target_json = self.directory_hash
        return self.jj_hashcomp.compare()


class _QuickTest:
    test_backup_json = Path("../../Misc_Project_Files/HostedFeatureStorage.json")
    test_new_zip = Path("../../Misc_Project_Files/HostedFeatureStorage.zip")
    test_other_zip = Path("../../Misc_Project_Files/HostedFeatureStorage_Other.zip")
    test_new_json = Path("../../Misc_Project_Files/HostedFeatureStorage_Other.json")

    def __init__(self, jj=False, ja=False, aa=False, **kwargs):
        self.hc = None
        self.jj = jj
        self.ja = ja
        self.aa = aa

        self.comparer_to_use = [x for x in [self.jj, self.ja, self.aa] if x]

        if len(self.comparer_to_use) > 1:
            raise ValueError("Only one hasher can be used at a time")

    def get_hc(self, **kwargs):
        if self.jj:
            self.hc = JsonToJsonHashComparer(source_json=self.test_backup_json,
                                             target_json=self.test_new_json,
                                             source_name=self.test_new_json.name,
                                             target_name=self.test_new_json.name,
                                             **kwargs)
        elif self.ja:
            self.hc = JsonToArchiveComparer(source_json=self.test_backup_json,
                                            archive_file=self.test_new_zip,
                                            **kwargs)
        elif self.aa:
            self.hc = ArchiveToArchiveComparer(source_archive_file=self.test_new_zip,
                                               target_archive_file=self.test_other_zip,
                                               **kwargs)

    def compare_test(self):
        if self.hc:
            self.hc.compare()
        else:
            raise AttributeError("No hasher initialized")


if __name__ == '__main__':
    jd = JsonToDirectoryComparer(source_json=Path("../../Misc_Project_Files/Desktop_backup.json"),
                                 target_dir=Path("~/Desktop").expanduser())
    jd.compare()

    # qt = _QuickTest(aa=True)
    # qt.get_hc()
    # qt.compare_test()
