from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Union, Optional

from AutoBackupAJM.Hasher import _BaseHasher
from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher
from AutoBackupAJM.Hasher.file_hashers import FileHasher, LargeFileHasher


class _BaseFactoryHasher(_BaseHasher, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def _process_input_path(cls, input_path: Union[str, Path], **kwargs):
        raise NotImplementedError("Must implement _process_input_path")

    @classmethod
    def validate_and_process_input_path(cls, input_path: Union[str, Path], **kwargs):
        if input_path:
            return cls._process_input_path(input_path, **kwargs)
        else:
            raise ValueError("Must specify input_path")


class HasherFactory(_BaseFactoryHasher):
    FILE_HASHER_CLASS = FileHasher
    LARGE_FILE_HASHER_CLASS = LargeFileHasher
    DIRECTORY_HASHER_CLASS = DirectoryHasher
    ARCHIVE_HASHER_CLASS = None  # TODO: implement

    @classmethod
    def _is_large_file(cls, file_path: Path) -> bool:
        return Path(file_path).stat().st_size > cls.LARGE_FILE_HASHER_CLASS.WARNING_BUFFER_SIZE

    @classmethod
    def inst_file_hasher_class(cls, file_path: Path, **kwargs):
        if cls._is_large_file(Path(file_path)):
            return cls.LARGE_FILE_HASHER_CLASS(file_path, **kwargs)
        return cls.FILE_HASHER_CLASS(file_path, **kwargs)

    @classmethod
    def inst_directory_hasher_class(cls, directory_path: Path, **kwargs):
        return cls.DIRECTORY_HASHER_CLASS(directory_path, **kwargs)

    @classmethod
    def inst_hasher_class(cls, input_path: Union[str, Path], **kwargs):
        if not isinstance(input_path, Path):
            input_path: Path = Path(input_path)

        if input_path.is_file():
            return cls.inst_file_hasher_class(input_path, **kwargs)
        elif input_path.is_dir():
            return cls.inst_directory_hasher_class(input_path, **kwargs)
        else:
            raise ValueError("input_path must be a file or directory")

    @classmethod
    def _process_input_path(cls, input_path: Union[str, Path], **kwargs):
        return cls.inst_hasher_class(input_path, **kwargs)

    def __new__(cls, *args, **kwargs):
        input_path: Optional[Union[str, Path]] = kwargs.pop("input_path", None)
        kwargs["logger"] = cls._setup_logging(**kwargs)
        return cls.validate_and_process_input_path(input_path, **kwargs)


if __name__ == "__main__":
    print(HasherFactory(input_path="../"))