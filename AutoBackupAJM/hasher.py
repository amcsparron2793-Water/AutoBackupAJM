from hashlib import md5
from pathlib import Path
from typing import Union, Tuple, Generator


class Hasher:
    DEFAULT_BUFFER_SIZE = 8192  # 8kb - could be increased for faster hashing of larger files

    def __init__(self, file_path: Union[str, Path], **kwargs):
        self._file_path = None
        self.file_path = file_path
        self.buffer_size = kwargs.get("buffer_size", self.__class__.DEFAULT_BUFFER_SIZE)

    @property
    def file_path(self) -> Path:
        return self._file_path

    @file_path.setter
    def file_path(self, value: Union[str, Path]):
        if isinstance(value, str):
            self._file_path = Path(value)
        elif isinstance(value, Path):
            self._file_path = value
        else:
            raise TypeError("file_path must be a string or a Path object")

    def _chunk_file_hash(self, path: Path):
        with open(path, 'rb') as file:
            file_hash = md5()
            while chunk := file.read(self.buffer_size):
                file_hash.update(chunk)
            return file_hash.hexdigest()

    def hash_file(self, file_path: Union[str, Path, None] = None) -> str:
        path = self.file_path if file_path is None else Path(file_path)

        if not path.is_file():
            raise ValueError("file_path must be a file, to hash a directories contents use hash_directory")
        return self._chunk_file_hash(path)

    def hash_directory(self, **kwargs) -> Generator[Tuple[Union[Path, str], str], None, None]:
        yield_path = kwargs.get("yield_path", True)

        if self.file_path.is_dir():
            dir_path = self.file_path
        else:
            raise ValueError(f"file_path must be a directory, to hash a file use hash_file")

        for file in dir_path.iterdir():
            if file.is_file():
                print(f"Hashing {file.name}...")
                yielded_file = file.resolve() if yield_path else file.resolve().as_posix()
                print(f'yielding: {type(yielded_file).__name__}')
                yield yielded_file, self.hash_file(file)
            else:
                # TODO: add handling for subdirectories
                print(f"Skipping subdir {file.name}...")


if __name__ == "__main__":
    file_hasher = Hasher('./_version.py')
    dir_hasher = Hasher('../../AutoBackupAJM')

    print(file_hasher.hash_file())

    for x in dir_hasher.hash_directory():
        print(x)
