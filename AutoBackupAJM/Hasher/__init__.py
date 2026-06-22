from logging import getLogger, basicConfig


class _BaseHasher:
    @classmethod
    def _setup_logging(cls, **kwargs):
        logger = kwargs.pop("logger", getLogger(cls.__name__))
        if not logger or not logger.hasHandlers():
            basicConfig(level='INFO')
        return logger


from AutoBackupAJM.Hasher.factory import HasherFactory
