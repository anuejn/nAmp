from deltasigma import synthesizeNTF, realizeNTF
from nmigen import *
from fixed_point import *


class Noiseshaper(Elaboratable):
    def __init__(self, input: FixedPointValue, osr=32, order=4, n_lev=2):
        self.input = input
        self.fmt = input.fmt

        self.h = synthesizeNTF(order, osr, 1)
        self.parameters = realizeNTF(self.h, form='CIFB')
        self.order = order
        self.osr = osr

        assert n_lev > 1
        self.quantization_values = [(i / (n_lev - 1)) * 2 - 1 for i in range(n_lev)]
        self.output = Signal(range(0, len(self.quantization_values)))

    def elaborate(self, platform):
        m = Module()
        a_list, g_list, b_list, c_list = self.parameters

        fmt = self.fmt

        self.quantized_value = fmt.Signal(reset=self.quantization_values[0], decode=True)
        self.integrators = [fmt.Signal(name="integrator_{}".format(n)) for n in range(self.order + 1)]
        self.integrators_last = [fmt.Signal(name="integrator_last_{}".format(n)) for n in range(self.order + 1)]
        for i, _ in enumerate(self.integrators):
            summands = [self.input * b_list[i]]
            if i != self.order:
                summands += [self.quantized_value * (-a_list[i])]
            if i % 2 == 1 and (i + 2 <= self.order):
                summands += [self.integrators_last[i + 2] * (-g_list[i // 2])]
            if i > 0:
                summands += [self.integrators_last[i - 1] * c_list[i - 1]]
            summands += [self.integrators_last[i] * (1 / self.osr)]
            m.d.comb += self.integrators[i].eq(sum(summands).cast(fmt, allow_clamp=True, allow_precision_loss=True))

        for i, _ in enumerate(self.integrators):
            m.d.sync += self.integrators_last[i].eq(self.integrators[i])

        last_stage = self.integrators_last[-1]
        for i, q in enumerate(self.quantization_values[1:]):
            tipping_point = (q + self.quantization_values[i]) / 2
            with m.If(last_stage > tipping_point):
                m.d.comb += self.quantized_value.eq(fmt.Const(q, allow_clamp=True))
                m.d.comb += self.output.eq(i + 1)

        return m


if __name__ == "__main__":
    fmt = Q(1, 24)
    noiseshaper = Noiseshaper(fmt.Signal())

    from nmigen.back.verilog import convert
    verilog = convert(noiseshaper)
    print(len(verilog.split("\n")))
