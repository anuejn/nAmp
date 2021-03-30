import tempfile
from pathlib import Path

from liteeth.common import *
from naps import PacketizedStream, DOWNWARDS

from liteeth import phy as liteeth_phys
from litex.build.lattice.platform import LatticePlatform
import liteeth.gen as gen
from litex.soc.integration.builder import Builder

from nmigen import *


class UDPStream(PacketizedStream):
    def __init__(self, name=None, src_loc_at=1):
        super().__init__(32, name, src_loc_at=1 + src_loc_at)
        self.src_port = Signal(16) @ DOWNWARDS
        self.dst_port = Signal(16) @ DOWNWARDS
        self.ip_address = Signal(32) @ DOWNWARDS
        self.length = Signal(16) @ DOWNWARDS
        self.error = Signal(4) @ DOWNWARDS


class LiteEth(Elaboratable):
    """A simple wrapper for the LiteEth udp core. generates verilog using migen and then treats it as a Blackbox"""

    def __init__(self, rgmii_resource, rgmii_clocks_resource):
        self.rgmii_resource = rgmii_resource
        self.rgmii_clocks_resource = rgmii_clocks_resource

        self.udp_sink_stream = UDPStream()
        self.udp_source_stream = UDPStream()

    def elaborate(self, platform):
        m = Module()

        verilog = generate_verilog()
        platform.add_file("liteeth.v", verilog)
        instance = m.submodules.instance = Instance(
            "liteeth_core",

            i_sys_clock=ClockSignal(),
            i_sys_reset=ResetSignal(),

            o_rgmii_eth_clocks_tx=self.rgmii_clocks_resource.tx,
            i_rgmii_eth_clocks_rx=self.rgmii_clocks_resource.rx,
            o_rgmii_eth_rst_n=self.rgmii_resource.rst_n,
            i_rgmii_eth_int_n=Signal(),
            o_rgmii_eth_mdc=self.rgmii_resource.mdc,
            io_rgmii_eth_mdio=self.rgmii_resource.mdio,
            i_rgmii_eth_rx_ctl=self.rgmii_resource.rx_ctl,
            i_rgmii_eth_rx_data=self.rgmii_resource.rx_data,
            o_rgmii_eth_tx_ctl=self.rgmii_resource.tx_ctl,
            o_rgmii_eth_tx_data=self.rgmii_resource.tx_data,

            i_udp_sink_valid=self.udp_sink_stream.valid,
            i_udp_sink_last=self.udp_sink_stream.last,
            o_udp_sink_ready=self.udp_sink_stream.ready,
            i_udp_sink_src_port=self.udp_sink_stream.src_port,
            i_udp_sink_dst_port=self.udp_sink_stream.dst_port,
            i_udp_sink_ip_address=self.udp_sink_stream.ip_address,
            i_udp_sink_length=self.udp_sink_stream.length,
            i_udp_sink_data=self.udp_sink_stream.payload,
            i_udp_sink_error=self.udp_sink_stream.error,

            o_udp_source_valid=self.udp_source_stream.valid,
            o_udp_source_last=self.udp_source_stream.last,
            i_udp_source_ready=self.udp_source_stream.ready,
            o_udp_source_src_port=self.udp_source_stream.src_port,
            o_udp_source_dst_port=self.udp_source_stream.dst_port,
            o_udp_source_ip_address=self.udp_source_stream.ip_address,
            o_udp_source_length=self.udp_source_stream.length,
            o_udp_source_data=self.udp_source_stream.payload,
            o_udp_source_error=self.udp_source_stream.error,
        )

        return m


def generate_verilog():
    platform = LatticePlatform("", io=[], toolchain="diamond")
    platform.add_extension(gen._io)

    core_config = {
        "clk_freq": int(125e6),
        "phy": liteeth_phys.LiteEthECP5PHYRGMII,

        "mac_address": 0xAA040000CFCF,
        "ip_address": "192.168.178.50",
        "port": 1710,
    }

    soc = gen.UDPCore(platform, core_config)
    with tempfile.TemporaryDirectory() as tmpdirname:
        builder = Builder(soc, compile_gateware=False, output_dir=tmpdirname)
        builder.build(build_name="liteeth_core")
        return (Path(tmpdirname) / "gateware" / "liteeth_core.v").read_bytes()


if __name__ == "__main__":
    print(generate_verilog())
