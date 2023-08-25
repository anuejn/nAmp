from amaranth import *
from fixed_point import *
from design_space import get_snr
from noiseshaper_cifb import Noiseshaper
from yosys import get_size
from pathlib import Path

if __name__ == "__main__":
    fmt = Q(1, 15)
    input = fmt.Signal()
    noiseshaper = Noiseshaper(input, order=3, n_lev=2, osr=200, fmt=Q(2, 17))
    print(f"{noiseshaper.umax=}")

    from amaranth.back.verilog import convert
    verilog = convert(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
    (Path(__file__).parent / "noiseshaper.v").write_text(verilog)
    print("verilog lines: ", len(verilog.split("\n")))

    snr = get_snr(fmt, input, noiseshaper)
    print(f"{snr=}db")

    size = get_size(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
    print("area: ", size)

