from pathlib import Path

from AutoBackupAJM import MISC_PROJECT_DIR


class Counter:
    def __init__(self, start: int = 0, **kwargs):
        self.counter_name = kwargs.get("counter_name", "counter")
        self._value = start

    @property
    def value(self) -> int:
        if isinstance(self._value, int):
            return self._value
        else:
            raise TypeError(f"value must be an integer, not {type(self._value)}")

    @value.deleter
    def value(self):
        self._value = 0

    def increment(self, amount: int = 1) -> int:
        if not isinstance(amount, int):
            raise TypeError(f"amount must be an integer, not {type(amount)}")
        if amount < 0:
            raise ValueError("amount cannot be negative")
        self._value += amount
        return self._value

    def __repr__(self):
        return f"{self.counter_name}: {self.value}"

    def __str__(self):
        return f"{self.value: ,}"


class _QuickTest:
    test_backup_json = Path(MISC_PROJECT_DIR, "HostedFeatureStorage.json")
    test_new_zip = Path(MISC_PROJECT_DIR, "HostedFeatureStorage.zip")
    test_other_zip = Path(MISC_PROJECT_DIR, "HostedFeatureStorage_Other.zip")
    test_new_json = Path(MISC_PROJECT_DIR, "ArcMap and Pro Projects.json")
    test_dir_json = Path(MISC_PROJECT_DIR, "ArcMap_and_Pro_Projects_Backup.json")
    test_big_dir_json = Path(MISC_PROJECT_DIR, "Desktop_Backup.json")
    test_target_dir = Path("~/Desktop/ArcMap and Pro Projects").expanduser()
    test_big_target_dir = Path("~/Desktop").expanduser()

    # TODO: HASHER_CLASS_MAP = dict()
    # test_target_dir = Path(MISC_PROJECT_DIR)

    def __init__(self, class_to_use: type, jj=False, ja=False, aa=False, jd=False, **kwargs):
        self._use_big = kwargs.get('use_big', False)
        self._class_to_use = None

        self.class_to_use = class_to_use
        self.hc = None
        self.jj = jj
        self.ja = ja
        self.aa = aa
        self.jd = jd

        self.comparer_to_use = [x for x in [self.jj, self.ja, self.aa, self.jd] if x]

        if len(self.comparer_to_use) > 1:
            raise ValueError("Only one hasher can be used at a time")

    @property
    def class_to_use(self):
        return self._class_to_use

    @class_to_use.setter
    def class_to_use(self, value):
        if value == getattr(self, "_class_to_use", None):
            return

        val_is_comparer = any([x for x in value.__mro__[1:] if x.__name__ == '_BaseHashComparer'])
        if not val_is_comparer:
            raise TypeError(f"class_to_use must be a subclass of _BaseHashComparer, not {value}")
        self._class_to_use = value

    def get_hc(self, **kwargs):
        self.class_to_use = kwargs.pop("class_to_use", self.class_to_use)
        if self.jj:
            self.hc = self.class_to_use(source_json=self.test_backup_json,
                                        target_json=self.test_new_json,
                                        # FIXME: setting source name like this doesnt seem to work?
                                        # source_name="totally_not_the_real_name",
                                        **kwargs)
        elif self.ja:
            self.hc = self.class_to_use(source_json=self.test_backup_json,
                                        archive_file=self.test_new_zip,
                                        **kwargs)
        elif self.aa:
            self.hc = self.class_to_use(source_archive_file=self.test_new_zip,
                                        target_archive_file=self.test_other_zip,
                                        **kwargs)
        elif self.jd:
            src_json = self.test_dir_json if not self._use_big else self.test_big_dir_json
            target_dir = self.test_target_dir if not self._use_big else self.test_big_target_dir
            self.hc = self.class_to_use(source_json=src_json,
                                        target_dir=target_dir,
                                        **kwargs)

    def compare_test(self):
        if self.hc:
            self.hc.compare()
        else:
            raise AttributeError("No hasher initialized")
