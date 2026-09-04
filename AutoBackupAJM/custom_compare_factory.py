from logging import getLogger
from shutil import unpack_archive
from pathlib import Path
from typing import Any

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory
from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import DirectoryToDirectoryComparer


class AutoBackupDirToDirComparer(DirectoryToDirectoryComparer):
    def __init__(self, source_dir: Path, target_dir: Path, **kwargs):
        super().__init__(source_dir, target_dir, **kwargs)
        self.original_source_is_zip = kwargs.get('original_source_is_zip', False)
        self.logger.name = self.__class__.__name__


class AutoBackupComparerFactory(ComparerFactory):
    _DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS = AutoBackupDirToDirComparer

    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        if not source.exists():
            raise FileNotFoundError(f"source file {source} does not exist")
        return super().inst_comparer_class(source, target, **kwargs)

    @classmethod
    def _target_file_with_ext_exists_in_parent(cls, target: Any, file_suffix: str, **kwargs):
        possible_file = Path(target).with_suffix(file_suffix)
        target_file_exists = bool([x for x in Path(target).parent.iterdir()
                                   if x == possible_file])
        return target_file_exists, possible_file

    @classmethod
    def _process_existing_hash_file(cls, hash_file_full_path: Path, **kwargs) -> tuple[Path, bool]:
        logger = kwargs.setdefault('logger', getLogger(cls.__name__))
        logger.info(f"target_hash_file_exists: True")
        logger.debug(f"hash_file_full_path: {hash_file_full_path}")

        has_hash_file = True
        return hash_file_full_path, has_hash_file

    @classmethod
    def _process_existing_zip_file(cls, possible_zip_file: Path, target: Path, **kwargs) -> tuple[Path, bool]:
        logger = kwargs.setdefault('logger', getLogger(cls.__name__))
        unzip_target = Path(target).parent / Path(target).stem

        logger.info(f"target_zip_exists: True")
        logger.debug(f"Unpacking {possible_zip_file} to {unzip_target}")

        unpack_archive(possible_zip_file, unzip_target)
        was_unzipped = True

        return unzip_target, was_unzipped

    # TODO: generalize this to be used for any file type so that code from _detect_and_unzip_archive can be reused
    @classmethod
    def _has_hash_file(cls, target: Any, **kwargs):
        hash_file_suffix = '.json'
        has_hash_file = False

        (target_hash_file_exists,
         possible_hash_file) = cls._target_file_with_ext_exists_in_parent(target,
                                                                          hash_file_suffix,
                                                                          **kwargs)

        if target_hash_file_exists:
            hash_file_full_path = Path(target).parent / possible_hash_file

            return cls._process_existing_hash_file(hash_file_full_path, **kwargs)

        return target, has_hash_file

    @classmethod
    def _detect_and_unzip_archive(cls, target: Any, **kwargs) -> tuple:
        zip_suffix = '.zip'
        was_unzipped = False

        (target_zip_exists,
         possible_zip_file) = cls._target_file_with_ext_exists_in_parent(target,
                                                                         zip_suffix,
                                                                         **kwargs)

        if target_zip_exists:
            return cls._process_existing_zip_file(possible_zip_file, target, **kwargs)

        return target, was_unzipped

    @classmethod
    def _directory_src_targets(cls, source: Any, target: Any, **kwargs):
        target_is_directory = cls._is_directory_input(target)

        # FIXME: THIS IS VERY MUCH IN PROGRESS
        target, has_hash_file = cls._has_hash_file(target)
        print(has_hash_file)
        exit(-1)
        # FIXME: END IN PROGRESS

        target, was_unzipped = cls._detect_and_unzip_archive(target)
        kwargs.setdefault('original_source_is_zip', was_unzipped)

        if was_unzipped:
            target_is_directory = cls._is_directory_input(target)

        if target_is_directory:
            return cls._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS(
                source_dir=source,
                target_dir=target,
                **kwargs,
            )
        return None
