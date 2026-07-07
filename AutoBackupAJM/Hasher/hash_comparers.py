import json
from pathlib import Path
from typing import Union, List, Tuple
from AutoBackupAJM import SetupLogger
from AutoBackupAJM.Hasher.other_hashers import ArchiveDirectoryHasher


class JsonToJsonHashComparer:
    def __init__(self, source_json: Union[list, dict, Path],
                 target_json: Union[list, dict, Path], **kwargs):
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
        if isinstance(value, Path):
            value = self._load_json(value, **kwargs)
        elif isinstance(value, (list, dict)):
            # just pass it through
            pass
        else:
            raise TypeError("value must be a Path or a list or a dict")
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

    def compare(self):
        for key, value in self.source_json.items():
            if key not in self.target_json:
                self.logger.error(f"Key {key} not found in {self.target_name}")
                return False
        self.logger.info("All keys found in both JSON files.")
        return True


class JsonToArchiveComparer(JsonToJsonHashComparer):
    def __init__(self, archive_file: Path, **kwargs):
        self._archive_hash = None
        self.logger = self.setup_logger(**kwargs)

        kwargs.setdefault('logger', self.logger)

        self._override_passed_in_target_json(**kwargs)

        self.archive_file, self.archive_hasher, kwargs = self.setup_archive_hasher(archive_file, **kwargs)

        kwargs.setdefault('target_name', self.archive_file.name)
        kwargs.setdefault('target_json', None)
        super().__init__(**kwargs)

    @property
    def target_json(self):
        return self.archive_hash

    @target_json.setter
    def target_json(self, value):
        try:
            raise ValueError("target_json cannot be set"
                             "when using JsonToArchiveComparer, "
                             "value is locked to self.archive_hash")
        except Exception as e:
            self.logger.warning(e)

    @property
    def archive_hash(self) -> Union[dict, List[dict]]:
        if self._archive_hash is None:
            self.logger.info(f"Hashing archive file {self.archive_file.name}")
            self._archive_hash = self.archive_hasher.hash_archive()
        # noinspection PyTypeChecker
        return self._archive_hash

    def _override_passed_in_target_json(self, **kwargs):
        if 'target_json' in kwargs:
            try:
                raise ValueError("target_json attribute cannot be "
                                 "provided when using JsonToArchiveComparer")
            except Exception as e:
                self.logger.error(e)
                raise

    def setup_archive_hasher(self, archive_file: Path, **kwargs) -> Tuple[Path, ArchiveDirectoryHasher, dict]:
        kwargs.setdefault('unzip_and_hash_contents', True)
        archive_hasher = ArchiveDirectoryHasher(input_path=archive_file, **kwargs)
        self.logger.info(f"Archive hasher initialized for {archive_file.name}")
        return archive_file, archive_hasher, kwargs


# TODO: ArchiveToArchiveComparer


if __name__ == '__main__':
    test_backup_json = Path("../../Misc_Project_Files/HostedFeatureStorage.json")
    test_new_json = Path("../../Misc_Project_Files/HostedFeatureStorage.zip")
    # j2j_hc = JsonToJsonHashComparer(source_json=test_backup_json,
    #                                 target_json=test_new_json,
    #                                 source_name=test_new_json.name,
    #                                 target_name=test_new_json.name)

    j2a_hc = JsonToArchiveComparer(source_json=test_backup_json,
                                   archive_file=test_new_json)

    j2a_hc.compare()
