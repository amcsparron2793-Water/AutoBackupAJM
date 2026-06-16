from pathlib import Path
from typing import Union, Tuple
from hashlib import md5


class FileHasher:
    DEFAULT_BUFFER_SIZE = 1024 ** 2  # 1MB - could be increased for faster hashing of larger files

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


class LargeFileHasher(FileHasher):
    DEFAULT_BUFFER_SIZE = 1024 ** 3  # 1GB
    WARNING_BUFFER_SIZE = DEFAULT_BUFFER_SIZE // 2

    def __init__(self, input_path: Union[str, Path], **kwargs):
        super().__init__(input_path, **kwargs)
        self._WarnLargeBufferSize()
        self.input_file_size = self.input_path.stat().st_size

    def _WarnLargeBufferSize(self):
        if self.buffer_size <= self.__class__.WARNING_BUFFER_SIZE:
            print("Warning: LargeFileHasher buffer_size is too small for large files, consider using FileHasher")
        if self.input_file_size <= self.__class__.WARNING_BUFFER_SIZE:
            print("Warning: LargeFileHasher input_file_size is too small for large files, consider using FileHasher")
