# A simple experiment that demonstrates basic CSR / SOC functionality
import os
from nmigen import *
from nmigen.build import Resource, Pins, Attrs
from naps.vendor.lattice_ecp5 import Pll
from naps import *

from liteeth_nmigen import LiteEth
from pwm import Pwm


class Top(Elaboratable):
    def elaborate(self, platform):
        platform.add_resources([Resource("speaker", 0, Pins("1 2", dir='o', conn=("j", "1")), Attrs(IO_TYPE="LVCMOS33"))])
        speaker = platform.request("speaker", 0)
        led = platform.request("led", 0)

        m = Module()

        pll = m.submodules.pll = Pll(25e6, 20, 1, reset_less_input=True)
        pll.output_domain("eth", 4)

        os.environ["NMIGEN_nextpnr_opts"] = "--timing-allow-fail"
        eth = m.submodules.eth = DomainRenamer("eth")(
            LiteEth(
                platform.request("eth", 0, dir={io.name: "-" for io in platform.lookup("eth", 0).ios}),
                platform.request("eth_clocks", 0, dir={io.name: "-" for io in platform.lookup("eth_clocks", 0).ios})
            )
        )

        pwm = m.submodules.pwm = Pwm(0)
        m.d.comb += speaker.o[0].eq(pwm.output)
        m.d.comb += speaker.o[1].eq(~pwm.output)

        m.submodules.clocking_i2s = ClockDebug("eth")
        m.submodules.clocking_sync = ClockDebug("sync", reset_less=True)

        return m


if __name__ == "__main__":
    cli(
        Top,
        runs_on=(Colorlight5a75b70Platform,),
        possible_socs=(JTAGSocPlatform,)
    )
