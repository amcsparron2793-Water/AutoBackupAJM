from logging import getLogger, basicConfig, Logger
from pathlib import Path
from typing import Union


class _BaseHasher:
    DEFAULT_BUFFER_SIZE = 1024 ** 2  # 1MB - could be increased for faster hashing of larger files

    def __init__(self, input_path, **kwargs):
        self._input_path = None
        self._logger: Logger = self._setup_logging(**kwargs)  # kwargs.get("logger", getLogger(self.__class__.__name__))
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
            raise TypeError("input_path must be a string or a Path object")

        if not self._input_path.exists():
            raise FileNotFoundError(f"self.input_path ({self._input_path}) must exist")

    @classmethod
    def _setup_logging(cls, **kwargs):
        logger = kwargs.pop("logger", getLogger(cls.__name__))
        basic_config_level = kwargs.pop("basic_config_level", 'INFO')

        if not logger or not logger.hasHandlers():
            basicConfig(level=basic_config_level)
            logger.info(f"Using basic config with level: {basic_config_level}")
        return logger


from AutoBackupAJM.Hasher.factory import HasherFactory
