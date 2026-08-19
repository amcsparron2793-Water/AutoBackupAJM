from pathlib import Path

from MultiHasherMatchAJM.Hasher.directory_hashers import DirectoryHasher
from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import JsonToDirectoryComparer, _BaseHashComparer

from AutoBackupAJM import MISC_PROJECT_DIR


class DirectoryToDirectoryComparer(JsonToDirectoryComparer, _BaseHashComparer):
    def __init__(self, source_dir: Path, target_dir: Path, **kwargs):
        _BaseHashComparer.__init__(self, **kwargs)
        kwargs.setdefault('logger', self.logger)

        self._source_directory_hash = None
        self.source_dir = source_dir

        self.source_directory_hasher = DirectoryHasher(input_path=self.source_dir, **kwargs)
        self.target_dir = target_dir

        # noinspection PyTypeChecker
        JsonToDirectoryComparer.__init__(self, source_json=None if self.delay_hashing else self.source_directory_hash,
                                         target_dir=self.target_dir, **kwargs)

    @property
    def source_directory_hash(self) -> dict:
        if self._source_directory_hash is None:
            self._source_directory_hash = self.source_directory_hasher.hash_and_record_directory()
        return self._source_directory_hash

    def compare(self):
        if self.delay_hashing or self.source_directory_hash is None:
            self.jj_hashcomp.source_json = self.source_directory_hash
            self.jj_hashcomp.target_json = self.directory_hash
            self.delay_hashing = False
        return super().compare()


if __name__ == '__main__':
    dtdc = DirectoryToDirectoryComparer(source_dir=Path(MISC_PROJECT_DIR / "HostedFeatureStorage_Other"),
                                        target_dir=Path(MISC_PROJECT_DIR / 'HostedFeatureStorage'))
    dtdc.compare()
