import shutil
from logging import getLogger
from pathlib import Path
from typing import Union
from itertools import chain


class ArchiveExtractor:
    SUPPORTED_ARCHIVE_TYPES = list(chain.from_iterable(
        [x for x in [x[1] for x in shutil.get_unpack_formats()]]
    ))

    def __init__(self, archive_path: Path, **kwargs):
        self._extract_dir = None
        self._archive_contents = None
        self.logger = kwargs.get("logger", getLogger(__name__))

        self.archive_path = archive_path
        self.extract_dir = kwargs.get("extract_dir", None)

    @property
    def extract_dir(self):
        return self._extract_dir

    @extract_dir.setter
    def extract_dir(self, value: Union[str, Path]):
        if value is None:
            self._extract_dir = Path(self.archive_path.parent / self.archive_path.stem).resolve()
            self.logger.info(f"extract_dir not specified, defaulting to {self._extract_dir}")
        else:
            resolved_path = Path(value).resolve()
            if resolved_path.suffix:
                raise ValueError(f"extract_dir must be a directory, not a file: {resolved_path}")
            self._extract_dir = resolved_path

    @property
    def archive_contents(self):
        if self.extract_dir is not None and self.extract_dir.is_dir():
            self._archive_contents = [f for f in self.extract_dir.iterdir()]
        return self._archive_contents

    def _validate_archive_extraction(self, **kwargs):
        if self.extract_dir.is_dir():
            return self.extract_dir
        else:
            raise FileNotFoundError(f"extract_dir {self.extract_dir} does not exist")

    def extract_archive(self, **kwargs) -> Path:
        try:
            shutil.unpack_archive(self.archive_path, extract_dir=self.extract_dir)
        except (shutil.ReadError, shutil.Error):
            raise ValueError(f"archive_path {self.archive_path} is not a valid archive file")

        return self._validate_archive_extraction(**kwargs)
