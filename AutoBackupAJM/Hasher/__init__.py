from logging import Logger
from pathlib import Path
from typing import Union


class _BaseHasher:
    DEFAULT_BUFFER_SIZE = 1024 ** 2  # 1MB - could be increased for faster hashing of larger files

    def __init__(self, input_path, **kwargs):
        self._input_path = None
        self._logger: Logger = SetupLogger.setup_logger(**kwargs)
        self._logger.info(f"Initializing {self.__class__.__name__}")

        self.buffer_size = kwargs.get("buffer_size", self.__class__.DEFAULT_BUFFER_SIZE)
        self.input_path = input_path

    @property
    def input_path(self) -> Path:
        return self._input_path

    @input_path.setter
    def input_path(self, value: Union[str, Path]):
        if isinstance(value, str):
            self._input_path = Path(value)
        elif isinstance(value, Path):
            self._input_path = value
        else:
            raise TypeError(f"input_path must be a string or a Path object, not {type(value).__name__}")

        if not self._input_path.exists():
            raise FileNotFoundError(f"self.input_path ({self._input_path}) must exist")


from AutoBackupAJM.Hasher.factory import HasherFactory
