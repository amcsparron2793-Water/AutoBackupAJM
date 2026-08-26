from shutil import unpack_archive
from pathlib import Path
from typing import Any

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory


class AutoBackupComparerFactory(ComparerFactory):
    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        if not source.exists():
            raise FileNotFoundError(f"source file {source} does not exist")
        return super().inst_comparer_class(source, target, **kwargs)

    @classmethod
    def _detect_and_unzip_archive(cls, target: Any):
        possible_zip_file = Path(target).with_suffix('.zip')
        target_zip_exists = bool([x for x in Path(target).parent.iterdir()
                                  if x == possible_zip_file])
        unzip_target = Path(target).parent / Path(target).stem
        if target_zip_exists:
            print(f"target_zip_exists: {target_zip_exists}")
            print(f"Unpacking {possible_zip_file} to {unzip_target}")
            unpack_archive(possible_zip_file, unzip_target)
            return unzip_target
        return target

    @classmethod
    def _directory_src_targets(cls, source: Any, target: Any, **kwargs):
        target_is_directory = cls._is_directory_input(target)
        target = cls._detect_and_unzip_archive(target)
        # FIXME: the unzipped directories create time (BUT NOT THE FILES INSIDE)
        #  is going to be the same as the current time,
        #  so we need to set it to the create time of the zip file or the file inside
        #import datetime
        #print(datetime.datetime.fromtimestamp(target.stat().st_ctime))
        if target_is_directory:
            return cls._DIRECTORY_SOURCE_DIRECTORY_TARGET_CLS(
                source_dir=source,
                target_dir=target,
                **kwargs,
            )
        return None
