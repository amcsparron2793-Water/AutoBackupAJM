from logging import getLogger
from shutil import unpack_archive
from pathlib import Path
from typing import Any

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory
from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import DirectoryToDirectoryComparer


class _FactoryFileToDirHelpers:
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
        # TODO:
        # do_not_unzip = kwargs.get('do_not_unzip', False)
        unzip_target = Path(target).parent / Path(target).stem

        logger.info(f"target_zip_exists: True")
        logger.debug(f"Unpacking {possible_zip_file} to {unzip_target}")

        unpack_archive(possible_zip_file, unzip_target)
        was_unzipped = True

        return unzip_target, was_unzipped

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
    def _use_hash_file(cls, source: Any, target: Any, **kwargs):
        logger = kwargs.setdefault('logger', getLogger(cls.__name__))
        ignore_hash_file = kwargs.get('ignore_hash_file', False)
        target, has_hash_file = cls._has_hash_file(target, **kwargs)

        if ignore_hash_file:
            logger.info('hash file is being ignored, directory will be rehashed.')

        if has_hash_file and not ignore_hash_file:
            # FIXME: this needs to be prettied up.
            dir_source = source
            json_target = target
            # FIXME: THIS DOES NOT CLEAN UP AFTER ITSELF - dir_source is not deleted after zipping etc.
            if hasattr(cls, '_JSON_SOURCE_DIRECTORY_TARGET_CLS'):
                return getattr(cls, '_JSON_SOURCE_DIRECTORY_TARGET_CLS')(
                    source_json=json_target, target_dir=dir_source, **kwargs)
            else:
                logger.error(f"No _JSON_SOURCE_DIRECTORY_TARGET_CLS")
        return None


class _ComparerNewBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_source_is_zip = kwargs.get('original_source_is_zip', False)
        # noinspection PyUnresolvedReferences
        self.logger.name = self.__class__.__name__


class AutoBackupDirToDirComparer(_ComparerNewBase, DirectoryToDirectoryComparer):
    ...


class AutoBackupComparerFactory(_FactoryFileToDirHelpers, ComparerFactory):
    _DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS = AutoBackupDirToDirComparer

    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        if not source.exists():
            raise FileNotFoundError(f"source file {source} does not exist")
        return super().inst_comparer_class(source, target, **kwargs)

    @classmethod
    def _directory_src_targets(cls, source: Any, target: Any, **kwargs):
        print("*************************************************************************************************\n"
              "IGNORE HASH FILE IS SET TO TRUE BY DEFAULT, THIS MEANS THE DIRECTORY WILL BE REHASHED EVERY TIME.\n"
              "*************************************************************************************************\n")
        kwargs.setdefault('ignore_hash_file', True)
        target_is_directory = cls._is_directory_input(target)

        target, was_unzipped = cls._detect_and_unzip_archive(target, **kwargs)
        kwargs.setdefault('original_source_is_zip', was_unzipped)

        if was_unzipped:
            target_is_directory = cls._is_directory_input(target)

        if target_is_directory:
            hash_file_class = cls._use_hash_file(source, target, **kwargs)
            if hash_file_class is not None:
                return hash_file_class

            return cls._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS(
                source_dir=source,
                target_dir=target,
                **kwargs,
            )
        return None
