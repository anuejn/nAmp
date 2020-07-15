from dataclasses import dataclass
from math import floor

from nmigen import *

__all__ = ["FixedPointFormat", "FixedPointValue"]


class FixedPointFormat:
    def __init__(self, bits_before_point, bits_after_point):
        assert bits_before_point > 0, "at least one bit (sign bit) is required before the point"
        self.bits_before_point = bits_before_point
        self.bits_after_point = bits_after_point

    def to_int(self, f: float):
        whole = floor(f) * (2 ** self.bits_after_point)
        fractional = round((f % 1) * (2 ** self.bits_after_point))
        return whole + fractional

    def to_float(self, i: int):
        whole = (i >> self.bits_after_point)
        fractional = ((i - (whole << self.bits_after_point)) / (2 ** self.bits_after_point))
        return whole + fractional

    def __eq__(self, other):
        assert isinstance(other, FixedPointFormat)
        return (self.bits_before_point == other.bits_before_point) \
               and (self.bits_after_point == other.bits_after_point)

    def __repr__(self):
        return "Q{}.{}".format(self.bits_before_point, self.bits_after_point)

    def __len__(self):
        return self.bits_before_point + self.bits_after_point

    @property
    def min(self):
        return FixedPointValue(self, Const(-(2 ** (len(self) - 1)), signed(len(self))))

    @property
    def max(self):
        return FixedPointValue(self, Const((2 ** (len(self) - 1)) - 1, signed(len(self))))

    def Const(self, value, src_loc_at=0):
        assert value < (2 ** (self.bits_before_point - 1))
        return FixedPointValue(self, Const(self.to_int(value), signed(len(self)), src_loc_at=src_loc_at + 1))

    def Signal(self, reset=0, src_loc_at=0, **kwargs):
        return FixedPointValue(self, Signal(
            signed(len(self)),
            src_loc_at=src_loc_at + 1,
            reset=self.to_int(reset),
            decoder=lambda i: str(self.to_float(i)),
            **kwargs
        ))


class FixedPointValue:
    def __init__(self, fmt: FixedPointFormat, value: Value):
        assert isinstance(value, Value)
        assert len(value) == len(fmt), "{} vs {}".format(len(value), len(fmt))
        super().__init__()
        self.value = value
        self.fmt = fmt

    def convert(self, fmt: FixedPointFormat):
        bits_after_point: Value = self.value[:self.fmt.bits_after_point]
        assert len(bits_after_point) == self.fmt.bits_after_point
        if len(bits_after_point) < fmt.bits_after_point:
            new_bits_after_point = Cat(
                Const(0, unsigned(fmt.bits_after_point - len(bits_after_point))),
                bits_after_point
            )
        elif len(bits_after_point) > fmt.bits_after_point:
            new_bits_after_point = bits_after_point[len(bits_after_point) - fmt.bits_after_point:]
        else:
            new_bits_after_point = bits_after_point

        bits_before_point: Value = self.value[self.fmt.bits_after_point:]
        assert len(bits_before_point) == self.fmt.bits_before_point
        if len(bits_before_point) < fmt.bits_before_point:
            new_bits_before_point = Cat(
                bits_before_point,
                Repl(bits_before_point[-1], fmt.bits_before_point - len(bits_before_point))
            )
        elif len(bits_before_point) > fmt.bits_before_point:
            new_bits_before_point = Cat(bits_before_point[:fmt.bits_before_point - 1], bits_before_point[-1])
        else:
            new_bits_before_point = bits_before_point

        # implement clamping math
        value = Cat(new_bits_after_point, new_bits_before_point).as_signed()
        if len(bits_before_point) > fmt.bits_before_point:
            value = Mux(self < fmt.min.convert(self.fmt),
                        fmt.min.value,
                        Mux(self > fmt.max.convert(self.fmt),
                            fmt.max.value,
                            value)
                        )

        return FixedPointValue(fmt, value)

    def __add__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt

        return_value = self.value + other.value
        return FixedPointValue(
            FixedPointFormat(len(return_value) - self.fmt.bits_after_point, self.fmt.bits_after_point), return_value)

    def __sub__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt

        return_value = self.value - other.value
        return FixedPointValue(
            FixedPointFormat(len(return_value) - self.fmt.bits_after_point, self.fmt.bits_after_point), return_value)

    def __mul__(self, other):
        assert isinstance(other, FixedPointValue)

        return FixedPointValue(
            FixedPointFormat(
                self.fmt.bits_before_point + other.fmt.bits_before_point,
                self.fmt.bits_after_point + other.fmt.bits_after_point
            ),
            self.value * other.value
        )

    def __gt__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt
        return self.value > other.value

    def __ge__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt
        return self.value >= other.value

    def __lt__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt
        return self.value < other.value

    def __le__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt
        return self.value <= other.value

    def __eq__(self, other):
        assert isinstance(other, FixedPointValue)
        assert other.fmt == self.fmt
        return self.value == other.value
