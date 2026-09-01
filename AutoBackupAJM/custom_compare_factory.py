from shutil import unpack_archive
from pathlib import Path
from typing import Any

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory
from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import DirectoryToDirectoryComparer


class AutoBackupDirToDirComparer(DirectoryToDirectoryComparer):
    def __init__(self, source_dir: Path, target_dir: Path, **kwargs):
        super().__init__(source_dir, target_dir, **kwargs)
        self.original_source_is_zip = kwargs.get('original_source_is_zip', False)


class AutoBackupComparerFactory(ComparerFactory):
    _DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS = AutoBackupDirToDirComparer

    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        if not source.exists():
            raise FileNotFoundError(f"source file {source} does not exist")
        return super().inst_comparer_class(source, target, **kwargs)

    @classmethod
    def _detect_and_unzip_archive(cls, target: Any):
        was_unzipped = False
        possible_zip_file = Path(target).with_suffix('.zip')
        target_zip_exists = bool([x for x in Path(target).parent.iterdir()
                                  if x == possible_zip_file])
        unzip_target = Path(target).parent / Path(target).stem
        if target_zip_exists:
            print(f"target_zip_exists: {target_zip_exists}")
            print(f"Unpacking {possible_zip_file} to {unzip_target}")
            unpack_archive(possible_zip_file, unzip_target)
            was_unzipped = True
            return unzip_target, was_unzipped
        return target, was_unzipped

    @classmethod
    def _directory_src_targets(cls, source: Any, target: Any, **kwargs):
        target_is_directory = cls._is_directory_input(target)

        target, was_unzipped = cls._detect_and_unzip_archive(target)
        kwargs.setdefault('original_source_is_zip', was_unzipped)

        if was_unzipped:
            target_is_directory = cls._is_directory_input(target)

        # FIXME: the unzipped directory's create time (BUT NOT THE FILES INSIDE)
        #  is going to be the same as the current time,
        #  so we need to set it to the create time of the zip file or the file inside
        if target_is_directory:
            return cls._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS(
                source_dir=source,
                target_dir=target,
                **kwargs,
            )
        return None
