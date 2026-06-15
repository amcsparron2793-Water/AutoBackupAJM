from hashlib import md5
from pathlib import Path
from typing import Union, Tuple, Generator


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

    def hash_file(self, file_path: Union[str, Path, None] = None) -> str:
        path = self.input_path if file_path is None else Path(file_path)

        path = self._validate_input_path_is_file(path)
        return self._chunk_file_hash(path)


class DirectoryHasher(FileHasher):
    @staticmethod
    def _get_yielded_file(file: Path, **kwargs):
        yield_path = kwargs.get("yield_path", True)
        yielded_file = file.resolve() if yield_path else file.resolve().as_posix()
        print(f'yielding: {type(yielded_file).__name__}')
        return yielded_file

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
                yielded_file = self._get_yielded_file(file, **kwargs)
                yield yielded_file, self.hash_file(file)
            else:
                # TODO: add handling for subdirectories
                print(f"Skipping subdir {file.name}...")


if __name__ == "__main__":
    file_hasher = FileHasher('./_version.py')
    dir_hasher = DirectoryHasher('../../AutoBackupAJM')

    print(file_hasher.hash_file())
    print('\n')

    for x in dir_hasher.hash_directory():
        print(x)
