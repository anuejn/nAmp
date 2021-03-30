import unittest
from nmigen import *
from nmigen.sim import Passive
from naps import SimPlatform, read_from_stream

from i2s_rx import I2S_RX


class TestI2SRX(unittest.TestCase):
    def test_basic(self):
        platform = SimPlatform()

        class I2SFakeResource:
            ws = Signal()
            sd = Signal()
            sck = Signal()

        m = Module()
        res = I2SFakeResource()
        dut = m.submodules.dut = I2S_RX(res, output_bit_depth=16)

        a = Signal()
        m.d.sync += a.eq(1)

        testdata = [0b1111000011110011, 100, 1000, 23344, 123]

        def writer():
            for word in [*testdata, 0, 0]:
                for bit in range(16):
                    yield res.sck.eq(0)
                    yield
                    if bit == 15:
                        yield res.ws.eq(not (yield res.ws))
                    yield res.sd.eq(int(f'{word:016b}'[bit]))
                    yield res.sck.eq(1)
                    yield
            yield Passive()
            while True:
                yield
        platform.add_process(writer, "sync")

        recv = []
        def l_reader():
            while len(recv) < len(testdata) + 1:
                recv.append((yield from read_from_stream(dut.l_output)))
                print("l", recv[-1])
        platform.add_process(l_reader, "i2s")

        def r_reader():
            while len(recv) < len(testdata) + 1:
                recv.append((yield from read_from_stream(dut.r_output)))
                print("r", recv[-1])
        platform.add_process(r_reader, "i2s")

        platform.add_sim_clock("sync", 100e6)
        platform.sim(m)
