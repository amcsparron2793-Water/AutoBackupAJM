import pytest
from AutoBackupAJM.utilities import Counter

class TestCounter:
    def test_init(self):
        c = Counter()
        assert c.value == 0
        assert c.counter_name == "counter"

        c2 = Counter(start=10, counter_name="my_counter")
        assert c2.value == 10
        assert c2.counter_name == "my_counter"

    def test_increment(self):
        c = Counter()
        assert c.increment() == 1
        assert c.value == 1
        assert c.increment(5) == 6
        assert c.value == 6

    def test_increment_invalid_amount(self):
        c = Counter()
        with pytest.raises(TypeError):
            c.increment("1")
        with pytest.raises(ValueError):
            c.increment(-1)

    def test_value_deleter(self):
        c = Counter(start=10)
        del c.value
        assert c.value == 0

    def test_repr_str(self):
        c = Counter(start=1000, counter_name="test")
        assert repr(c) == "test: 1000"
        # str(c) uses formatting {self.value: ,} which adds thousands separator
        assert str(c) == " 1,000" or str(c) == "1,000" # depending on locale/implementation, usually it's " 1,000" due to the space before comma in format

    def test_invalid_value_type(self):
        c = Counter()
        c._value = "not an int"
        with pytest.raises(TypeError):
            _ = c.value
