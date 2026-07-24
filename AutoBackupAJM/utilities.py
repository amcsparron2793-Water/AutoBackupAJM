from enum import Enum
from pathlib import Path
from typing import Union

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


class _ValidHasherCodes(Enum):
    JJ = "jj"
    JA = "ja"
    AA = "aa"
    JD = "jd"


class _QuickTest:
    test_backup_json = Path(MISC_PROJECT_DIR, "HostedFeatureStorage.json")
    test_new_zip = Path(MISC_PROJECT_DIR, "HostedFeatureStorage.zip")
    test_other_zip = Path(MISC_PROJECT_DIR, "HostedFeatureStorage_Other.zip")
    test_new_json = Path(MISC_PROJECT_DIR, "ArcMap and Pro Projects.json")
    test_dir_json = Path(MISC_PROJECT_DIR, "ArcMap_and_Pro_Projects_Backup.json")
    test_big_dir_json = Path(MISC_PROJECT_DIR, "Desktop_Backup.json")
    test_target_dir = Path("~/Desktop/ArcMap and Pro Projects").expanduser()
    test_big_target_dir = Path("~/Desktop").expanduser()

    HASHER_CLASS_MAP = {}
    VALID_HASHER_CODES = _ValidHasherCodes

    def __init__(self, hasher_type_code: str, **kwargs):
        # TODO: get rid of these and use the valid hasher codes directly
        self._jj = False
        self._ja = False
        self._aa = False
        self._jd = False

        self._class_to_use = None
        self.hc = None

        self._use_big = kwargs.get('use_big', False)
        self.hasher_type_code = hasher_type_code
        self._activate_type_code()

        self.class_to_use = self.hasher_type_code

    def __new__(cls, *args, **kwargs):
        if len(cls.HASHER_CLASS_MAP.items()) > 0:
            pass
        else:
            raise ValueError("HASHER_CLASS_MAP must be set before instantiating _QuickTest")
        return super().__new__(cls)

    @classmethod
    def _get_class_from_map(cls, value: Union[str, type]) -> type:
        if value in cls.HASHER_CLASS_MAP:
            value = cls.HASHER_CLASS_MAP[value]
        if hasattr(value, "__mro__") and isinstance(value, type):
            return value
        else:
            raise TypeError(f"value must be a class, not {value.__class__.__name__}")

    def _activate_type_code(self):
        setattr(self, f"_{self.hasher_type_code.lower()}", True)
        activated_type_codes = [getattr(self, f"_{x.value}")
                                for x in self.__class__.VALID_HASHER_CODES
                                if getattr(self, f"_{x.value}")]
        if len(activated_type_codes) > 1:
            raise ValueError("Only one type_code can be active at a time")
        elif not activated_type_codes:
            raise ValueError("No valid type_code is active (must be one of: "
                             f"{', '.join([x.value for x in self.__class__.VALID_HASHER_CODES])}")

    @property
    def class_to_use(self):
        return self._class_to_use

    @class_to_use.setter
    def class_to_use(self, value):
        if value == getattr(self, "_class_to_use", None):
            return
        value = self._get_class_from_map(value)

        val_is_comparer = any([x for x in value.__mro__[1:] if x.__name__ == '_BaseHashComparer'])
        if not val_is_comparer:
            raise TypeError(f"class_to_use must be a subclass of _BaseHashComparer, not {value}")
        self._class_to_use = value

    def get_hc(self, **kwargs):
        self.class_to_use = kwargs.pop("class_to_use", self.class_to_use)
        if self._jj:
            self.hc = self.class_to_use(source_json=self.test_backup_json,
                                        target_json=self.test_new_json,
                                        # FIXME: setting source name like this doesnt seem to work?
                                        # source_name="totally_not_the_real_name",
                                        **kwargs)
        elif self._ja:
            self.hc = self.class_to_use(source_json=self.test_backup_json,
                                        archive_file=self.test_new_zip,
                                        **kwargs)
        elif self._aa:
            self.hc = self.class_to_use(source_archive_file=self.test_new_zip,
                                        target_archive_file=self.test_other_zip,
                                        **kwargs)
        elif self._jd:
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
