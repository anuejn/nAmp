from nmigen import *


class Pwm(Elaboratable):
    def __init__(self, value, bits=8):
        self.bits = bits
        self.value = value

        self.output = Signal()

    def elaborate(self, platform):
        m = Module()

        counter = Signal(self.bits)
        m.d.sync += counter.eq(counter + 1)

        m.d.comb += self.output.eq(counter > self.value)

        return m
