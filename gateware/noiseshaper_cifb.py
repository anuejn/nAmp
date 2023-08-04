from deltasigma import synthesizeNTF, realizeNTF, scaleABCD, stuffABCD, mapABCD
from amaranth import *
from fixed_point import *
from yosys import get_size
import numpy as np
from pathlib import Path


class Noiseshaper(Elaboratable):
    def __init__(self, input: FixedPointValue, osr=32, order=4, n_lev=2, fmt=None):
        self.input = input
        self.fmt = input.fmt if fmt is None else fmt

        self.h = synthesizeNTF(order, osr, 1)
        a, g, b, c = realizeNTF(self.h, form='CIFB')
        abcd = stuffABCD(a, g, b, c)
        abcd_scaled, umax, s = scaleABCD(abcd, n_lev)
        self.parameters = mapABCD(abcd_scaled)

        self.umax = umax
        self.order = order
        self.osr = osr

        assert n_lev > 1
        self.n_lev = n_lev
        self.quantization_values = [i * 2 - (n_lev / 2) for i in range(n_lev)]
        self.output = Signal(range(0, len(self.quantization_values)), name="out")

    def elaborate(self, platform):
        m = Module()
        a_list, g_list, b_list, c_list = [np.atleast_1d(x) for x in self.parameters]

        fmt = self.fmt
        input = self.fmt.Signal(name='input_internal_fmt')
        m.d.comb += input.eq(self.input.cast(fmt, allow_precision_loss=1))

        self.quantized_value = fmt.Signal(reset=self.quantization_values[0], decode=True)
        self.stages = [fmt.Signal(name="stage_{}".format(n)) for n in range(self.order + 1)]

        for i, _ in enumerate(self.stages):
            summands = [input * b_list[i]]
            if i < self.order:
                summands += [self.stages[i]]
                summands += [self.quantized_value * (-a_list[i])]
            if i != 0:
                summands += [self.stages[i - 1] * c_list[i - 1]]
            if (i + self.order) % 2 == 0 and i + 1 < self.order:
                summands += [self.stages[i + 1] * (-g_list[i // 2])]

            domain = m.d.sync if i < self.order else m.d.comb
            domain += self.stages[i].eq(
                sum(summands).cast(fmt, allow_precision_loss=True, allow_clamp=True)
            )

        last_stage = self.stages[-1]
        for i, q in enumerate(self.quantization_values[1:]):
            tipping_point = (q + self.quantization_values[i]) / 2
            with m.If(last_stage > tipping_point):
                m.d.comb += self.quantized_value.eq(fmt.Const(q, allow_clamp=True))
                m.d.comb += self.output.eq(i + 1)

        return m


if __name__ == "__main__":
    fmt = Q(1, 15)
    noiseshaper = Noiseshaper(fmt.Signal(name="input"), order=3, osr=200, fmt=Q(2, 17))
    print(f"{noiseshaper.umax=}")

    from amaranth.back.verilog import convert
    verilog = convert(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
    (Path(__file__).parent / "noiseshaper.v").write_text(verilog)
    print("verilog lines: ", len(verilog.split("\n")))

    size = get_size(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
    print("area: ", size)
