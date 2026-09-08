from MultiHasherMatchAJM.MatchAndRecord.hash_comparers import DirectoryToDirectoryComparer


class _ComparerNewBase:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_source_is_zip = kwargs.get('original_source_is_zip', False)
        # noinspection PyUnresolvedReferences
        self.logger.name = self.__class__.__name__


class AutoBackupDirToDirComparer(_ComparerNewBase, DirectoryToDirectoryComparer):
    ...
