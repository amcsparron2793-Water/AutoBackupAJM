class Counter:
    def __init__(self, start: int = 0):
        self._value = start

    @property
    def value(self) -> int:
        return self._value

    def increment(self, amount: int = 1) -> int:
        if amount < 0:
            raise ValueError("amount cannot be negative")
        self._value += amount
        return self._value
