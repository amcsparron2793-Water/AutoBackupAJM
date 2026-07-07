import json
from pathlib import Path
from typing import Union
from AutoBackupAJM import SetupLogger


class JsonHashComparer:
    def __init__(self, source_json: Union[list, dict, Path],
                 target_json: Union[list, dict, Path], **kwargs):
        self._source_json = None
        self._target_json = None

        self.source_name = kwargs.get("source_name", "source_json")
        self.target_name = kwargs.get("target_name", "target_json")

        self.logger = SetupLogger.setup_logger(**kwargs)
        self.logger.name = self.__class__.__name__
        self.logger.info(f"Initializing {self.__class__.__name__}")
        self.source_json = source_json
        self.target_json = target_json

    def _get_json(self, value: Union[Path, list, dict]):
        if isinstance(value, Path):

            value = self._load_json(value)
        elif isinstance(value, (list, dict)):
            # just pass it through
            pass
        else:
            raise TypeError("value must be a Path or a list or a dict")
        return value

    @staticmethod
    def _load_json(path_to_json: Path):
        if isinstance(path_to_json, Path):
            with open(path_to_json, 'r') as f:
                return json.load(f)
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
        return True


if __name__ == '__main__':
    test_backup_json = Path("../../Misc_Project_Files/Desktop_backup.json")
    test_new_json = Path("../../Misc_Project_Files/Desktop.json")
    jhc = JsonHashComparer(source_json=test_backup_json,
                           target_json=test_new_json,
                           source_name=test_new_json.name,
                           target_name=test_new_json.name)
    jhc.compare()
