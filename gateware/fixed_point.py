from math import floor

from amaranth import *

__all__ = ["FixedPointValue", "Q"]


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
        return -(2 ** (len(self) - 1))

    @property
    def max(self):
        return (2 ** (len(self) - 1)) - 1

    def cast(self, value):
        if isinstance(value, FixedPointValue):
            return value.cast(self)
        elif isinstance(value, Value):
            return Q(len(value), 0).Value(value)
        elif isinstance(value, (int, float)):
            return self.Const(value)
        else:
            raise ValueError("{!r} cant be turned into a fixed point value".format(value))

    def Value(self, value):
        return FixedPointValue(self, value)

    def Const(self, value, src_loc_at=0, allow_clamp=False):
        if self.to_int(value) > self.max:
            if allow_clamp:
                i_val = self.max
            else:
                raise ValueError("{} is too big for the format {!r}. maximum is {}".format(value, self, self.to_float(self.max)))
        elif self.to_int(value) < self.min:
            if allow_clamp:
                i_val = self.min
            else:
                raise ValueError("{} is too small for the format {!r}. minimum is {}".format(value, self, self.to_float(self.min)))
        else:
            i_val = self.to_int(value)
        return self.ConstRaw(i_val, src_loc_at)

    def ConstRaw(self, i_val, src_loc_at=0):
        return self.Value(Const(i_val, signed(len(self)), src_loc_at=src_loc_at + 1))

    def Signal(self, reset=0, src_loc_at=0, decode=False, **kwargs):
        if decode:
            kwargs = {"decoder": lambda i: str(self.to_float(i)), **kwargs}

        return self.Value(Signal(
            signed(len(self)),
            src_loc_at=src_loc_at + 1,
            reset=self.to_int(reset),
            **kwargs
        ))


def Q(bits_before_point, bits_after_point):
    return FixedPointFormat(bits_before_point, bits_after_point)


class FixedPointValue:
    def __init__(self, fmt: FixedPointFormat, value: Value):
        assert isinstance(value, Value)
        assert len(value) == len(fmt), "{} vs {}".format(len(value), len(fmt))
        super().__init__()
        self.value = value
        self.fmt = fmt

    def cast(self, fmt: FixedPointFormat, allow_clamp=False, allow_precision_loss=False):
        if fmt == self.fmt:
            return self

        bits_after_point: Value = self.value[:self.fmt.bits_after_point]
        assert len(bits_after_point) == self.fmt.bits_after_point
        if len(bits_after_point) < fmt.bits_after_point:
            new_bits_after_point = Cat(
                Const(0, unsigned(fmt.bits_after_point - len(bits_after_point))),
                bits_after_point
            )
        elif len(bits_after_point) > fmt.bits_after_point:
            assert allow_precision_loss
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
            assert allow_clamp
            new_bits_before_point = Cat(bits_before_point[:fmt.bits_before_point - 1], bits_before_point[-1])
        else:
            new_bits_before_point = bits_before_point

        # implement clamping math
        value = Cat(new_bits_after_point, new_bits_before_point).as_signed()
        min = fmt.ConstRaw(fmt.min)
        max = fmt.ConstRaw(fmt.max)
        if len(bits_before_point) > fmt.bits_before_point:
            value = Mux(self < min,
                        min.value,
                        Mux(self > max,
                            max.value,
                            value)
                        )

        return FixedPointValue(fmt, value)

    def eq(self, other):
        other = self.fmt.cast(other)

        return self.value.eq(other.value)

    def _make_same_fmt(self, other):
        new_fmt = Q(
            max(self.fmt.bits_before_point, other.fmt.bits_before_point if isinstance(other, FixedPointValue) else 0),
            max(self.fmt.bits_after_point, other.fmt.bits_after_point if isinstance(other, FixedPointValue) else 0)
        )
        return new_fmt.cast(self), new_fmt.cast(other)

    def __add__(self, other):
        a, b = self._make_same_fmt(other)

        return_value = a.value + b.value
        return FixedPointValue(FixedPointFormat(len(return_value) - a.fmt.bits_after_point, a.fmt.bits_after_point),
                               return_value)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        a, b = self._make_same_fmt(other)

        return_value = a.value - b.value
        return FixedPointValue(FixedPointFormat(len(return_value) - a.fmt.bits_after_point, a.fmt.bits_after_point),
                               return_value)

    def __mul__(self, other):
        if isinstance(other, (int, float)) and other == 1:
            return self

        other = self.fmt.cast(other)

        return FixedPointValue(
            FixedPointFormat(
                self.fmt.bits_before_point + other.fmt.bits_before_point,
                self.fmt.bits_after_point + other.fmt.bits_after_point
            ),
            self.value * other.value
        )

    def __gt__(self, other):
        a, b = self._make_same_fmt(other)
        return a.value > b.value

    def __ge__(self, other):
        a, b = self._make_same_fmt(other)
        return a.value >= b.value

    def __lt__(self, other):
        a, b = self._make_same_fmt(other)
        return a.value < b.value

    def __le__(self, other):
        a, b = self._make_same_fmt(other)
        return a.value <= b.value

    def __eq__(self, other):
        a, b = self._make_same_fmt(other)
        return a.value == b.value
