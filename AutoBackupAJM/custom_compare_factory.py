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

    # TODO: generalize this to be used for any file type so that code from _detect_and_unzip_archive can be reused
    @classmethod
    def _has_hash_file(cls, target: Any, **kwargs):
        logger = kwargs.get('logger', getLogger(cls.__name__))
        has_hash_file = False
        possible_hash_file = Path(target).with_suffix('.json')
        target_hash_file_exists = bool([x for x in Path(target).parent.iterdir()
                                        if x == possible_hash_file])
        hash_file_full_path = Path(target).parent / possible_hash_file
        if target_hash_file_exists:
            logger.info(f"target_hash_file_exists: {target_hash_file_exists}")
            logger.debug(f"hash_file_full_path: {hash_file_full_path}")

            has_hash_file = True
            return hash_file_full_path, has_hash_file

        return target, has_hash_file

    @classmethod
    def _detect_and_unzip_archive(cls, target: Any, **kwargs) -> tuple:
        logger = kwargs.get('logger', getLogger(cls.__name__))
        was_unzipped = False
        possible_zip_file = Path(target).with_suffix('.zip')
        target_zip_exists = bool([x for x in Path(target).parent.iterdir()
                                  if x == possible_zip_file])
        unzip_target = Path(target).parent / Path(target).stem
        if target_zip_exists:
            logger.info(f"target_zip_exists: {target_zip_exists}")
            logger.debug(f"Unpacking {possible_zip_file} to {unzip_target}")

            unpack_archive(possible_zip_file, unzip_target)
            was_unzipped = True

            return unzip_target, was_unzipped

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
