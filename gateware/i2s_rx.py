from naps import BasicStream, delay_by, StreamBuffer
from nmigen import *


class I2S_RX(Elaboratable):
    def __init__(self, i2s_resource, output_bit_depth=16, i2s_domain="i2s"):
        self.output_bit_depth = output_bit_depth
        self.i2s_resource = i2s_resource
        self.i2s_domain = i2s_domain

        self.l_output = BasicStream(output_bit_depth)
        self.r_output = BasicStream(output_bit_depth)

    def elaborate(self, platform):
        m = Module()

        i2s_domain = ClockDomain(self.i2s_domain)
        m.domains += i2s_domain
        m.d.comb += i2s_domain.clk.eq(self.i2s_resource.sck)

        l_buffer_input = BasicStream(self.output_bit_depth)
        r_buffer_input = BasicStream(self.output_bit_depth)

        delayed_ws = delay_by(self.i2s_resource.ws, 1, m)
        with m.FSM():
            for i in range(self.output_bit_depth + 1):
                with m.State(f'bit_{i}'):
                    with m.If(delayed_ws != self.i2s_resource.ws):
                        m.next = "bit_0"
                    with m.Else():
                        if i < self.output_bit_depth:
                            m.next = f"bit_{i + 1}"
                    if i < self.output_bit_depth:
                        with m.If(delayed_ws):
                            m.d.sync += r_buffer_input.payload[self.output_bit_depth - i - 1].eq(self.i2s_resource.sd)
                        with m.Else():
                            m.d.sync += l_buffer_input.payload[self.output_bit_depth - i - 1].eq(self.i2s_resource.sd)
                    if i == 0:
                        with m.If(delayed_ws):
                            m.d.comb += r_buffer_input.valid.eq(1)
                        with m.Else():
                            m.d.comb += l_buffer_input.valid.eq(1)

        l_buffer = m.submodules.buffer_l = StreamBuffer(l_buffer_input)
        m.d.comb += self.l_output.connect_upstream(l_buffer.output)
        r_buffer = m.submodules.buffer_r = StreamBuffer(r_buffer_input)
        m.d.comb += self.r_output.connect_upstream(r_buffer.output)

        return DomainRenamer(self.i2s_domain)(m)
