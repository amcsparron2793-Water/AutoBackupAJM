from hashlib import md5
from pathlib import Path
from typing import Union, Tuple, Generator, Optional


class FileHasher:
    DEFAULT_BUFFER_SIZE = 8192  # 8kb - could be increased for faster hashing of larger files

    def __init__(self, input_path: Union[str, Path], **kwargs):
        self._input_path = None

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

    def _chunk_file_hash(self, path: Path):
        with open(path, 'rb') as file:
            file_hash = md5()
            while chunk := file.read(self.buffer_size):
                file_hash.update(chunk)
            print(f"Hashing {path} complete...")
            return file_hash.hexdigest()

    @staticmethod
    def _validate_input_path_is_file(path: Path) -> Path:
        if path.is_file():
            return path
        else:
            raise ValueError(f"self.input_path must be a file, to hash a directory use hash_directory")

    @staticmethod
    def _get_return_path(file: Path, **kwargs):
        return_path = kwargs.get("return_path", True)
        returned_path = file.resolve() if return_path else file.resolve().as_posix()
        print(f'returning: {type(returned_path).__name__}')
        return returned_path

    def _setup_hash_path(self, file_path: Union[str, Path, None] = None, **kwargs) -> Tuple[Path, Union[Path, str]]:
        path_to_hash = self.input_path if file_path is None else Path(file_path)

        path_to_hash = self._validate_input_path_is_file(path_to_hash)
        returned_file_path = self._get_return_path(path_to_hash, **kwargs)
        return path_to_hash, returned_file_path

    def hash_file(self, file_path: Union[str, Path, None] = None, **kwargs) -> Tuple[Union[Path, str], str]:
        path, returned_file_path = self._setup_hash_path(file_path, **kwargs)

        return returned_file_path, self._chunk_file_hash(path)


class DirectoryHasher(FileHasher):
    def _validate_input_path_is_dir(self) -> Path:
        if self.input_path.is_dir():
            dir_path = self.input_path
        else:
            raise ValueError(f"self.input_path must be a directory, to hash a file use hash_file")
        return dir_path

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        dir_path = self._validate_input_path_is_dir()

        for file in dir_path.iterdir():
            if file.is_file():
                yield self.hash_file(file, **kwargs)
            else:
                # TODO: add handling for subdirectories
                print(f"Skipping subdir {file.name}...")


class HasherFactory:
    FILE_HASHER_CLASS = FileHasher
    DIRECTORY_HASHER_CLASS = DirectoryHasher

    @classmethod
    def inst_hasher_class(cls, input_path: Union[str, Path], **kwargs):
        if Path(input_path).is_file():
            return cls.FILE_HASHER_CLASS(input_path, **kwargs)
        elif Path(input_path).is_dir():
            return cls.DIRECTORY_HASHER_CLASS(input_path, **kwargs)
        else:
            raise ValueError("input_path must be a file or directory")

    @classmethod
    def validate_input_path(cls, input_path: Optional[Union[str, Path]], *args, **kwargs):
        if input_path:
            return cls.inst_hasher_class(input_path, **kwargs)
        else:
            raise ValueError("Must specify input_path")

    def __new__(cls, *args, **kwargs):
        input_path: Optional[Union[str, Path]] = kwargs.pop("input_path", None)
        return cls.validate_input_path(input_path, *args, **kwargs)


def _test_hashing(hasher):
    print(f"testing with {hasher.__class__.__name__}\n")
    if hasher.__class__ in [FileHasher, HasherFactory]:
        print(hasher.hash_file())

    if hasattr(hasher, 'hash_directory'):
        for x in hasher.hash_directory():
            print(x)
    print('\n')


def _test_non_factory_hashing():
    file_hasher = FileHasher(test_file)
    dir_hasher = DirectoryHasher(test_dir)
    _test_hashing(file_hasher)
    _test_hashing(dir_hasher)


def _test_factory_hashing(input_path: Optional[Union[str, Path]]):
    factory_hasher = HasherFactory(input_path=input_path)
    print(factory_hasher.__class__.__name__)
    _test_hashing(factory_hasher)


if __name__ == "__main__":
    test_non_factory = False
    test_file = './_version.py'
    test_dir = '../../AutoBackupAJM'

    if test_non_factory:
        _test_non_factory_hashing()
    else:
        _test_factory_hashing(test_file)
        _test_factory_hashing(test_dir)




