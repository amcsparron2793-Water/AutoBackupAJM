from pathlib import Path
from typing import Union, Optional

from AutoBackupAJM.Hasher.directory_hashers import DirectoryHasher
from AutoBackupAJM.Hasher.factory import HasherFactory
from AutoBackupAJM.Hasher.file_hashers import FileHasher


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
    test_dir = './'

    if test_non_factory:
        _test_non_factory_hashing()
    else:
        _test_factory_hashing(test_file)
        _test_factory_hashing(test_dir)
