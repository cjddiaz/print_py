"""
core/counters.py
Serial number counter for auto-incrementing labels.
Usage: counter = SerialCounter("LOTE-", 1, 1, 4)
       counter.next() -> "LOTE-0001", "LOTE-0002", ...
Elements with text containing {SERIAL} will be replaced by the counter value.
"""


class SerialCounter:
    def __init__(self, prefix: str = "", start: int = 1, step: int = 1, padding: int = 4, suffix: str = ""):
        self.prefix = prefix
        self.suffix = suffix
        self.current = start
        self.step = step
        self.padding = padding

    def next(self) -> str:
        val = f"{self.prefix}{str(self.current).zfill(self.padding)}{self.suffix}"
        self.current += self.step
        return val

    def peek(self) -> str:
        return f"{self.prefix}{str(self.current).zfill(self.padding)}{self.suffix}"

    def reset(self, start: int = None):
        if start is not None:
            self.current = start

    def to_dict(self) -> dict:
        return {
            "prefix": self.prefix,
            "suffix": self.suffix,
            "current": self.current,
            "step": self.step,
            "padding": self.padding,
        }

    @classmethod
    def from_dict(cls, d: dict):
        obj = cls(
            prefix=d.get("prefix", ""),
            start=d.get("current", 1),
            step=d.get("step", 1),
            padding=d.get("padding", 4),
            suffix=d.get("suffix", ""),
        )
        return obj
