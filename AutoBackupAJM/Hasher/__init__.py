from logging import getLogger, basicConfig, Logger


class _BaseHasher:
    DEFAULT_BUFFER_SIZE = 1024 ** 2  # 1MB - could be increased for faster hashing of larger files

    def __init__(self, input_path, **kwargs):
        self._logger: Logger = self._setup_logging(**kwargs)  # kwargs.get("logger", getLogger(self.__class__.__name__))
        self._logger.info(f"Initializing {self.__class__.__name__}")

        self.buffer_size = kwargs.get("buffer_size", self.__class__.DEFAULT_BUFFER_SIZE)

    @classmethod
    def _setup_logging(cls, **kwargs):
        logger = kwargs.pop("logger", getLogger(cls.__name__))
        if not logger or not logger.hasHandlers():
            basicConfig(level='INFO')
        return logger


from AutoBackupAJM.Hasher.factory import HasherFactory
