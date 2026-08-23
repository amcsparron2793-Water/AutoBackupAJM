from typing import Any

from MultiHasherMatchAJM.MatchAndRecord import ComparerFactory


class AutoBackupComparerFactory(ComparerFactory):
    @classmethod
    def inst_comparer_class(cls, source: Any, target: Any, **kwargs):
        if not source.exists():
            raise FileNotFoundError(f"source file {source} does not exist")
        return super().inst_comparer_class(source, target, **kwargs)
