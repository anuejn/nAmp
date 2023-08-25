
from pathlib import Path
from amaranth import Signal
from amaranth.sim import Simulator
import numpy as np
import deltasigma as ds

from fixed_point import Q
from noiseshaper_cifb import Noiseshaper
from yosys import get_size

def get_snr(fmt: Q, input: Signal, dut):
    sim = Simulator(dut)
    sim.add_clock(1 / 100e6)

    input_hist = []
    output_hist = []
    integrators_hist = [[] for _ in dut.stages]

    n = 8192
    f_nyquist = int(np.ceil(n/(2.*dut.osr)))
    f_test = np.floor(2./3.*f_nyquist)
    u = dut.n_lev * 0.5 * 0.5 * np.sin(2 * np.pi * f_test / n * np.arange(n))

    def testbench():
        for x in u:
            yield input.eq(x)

            input_hist.append(fmt.to_float((yield input.value)))
            output_hist.append(fmt.to_float((yield dut.quantized_value.value)))
            for i, integrator in enumerate(dut.stages):
                integrators_hist[i].append(fmt.to_float((yield integrator.value)))

            yield
    sim.add_sync_process(testbench)

    sim.run()

    spec = np.fft.fft(output_hist * ds.ds_hann(n)) / (n / 4)
    snr = ds.calculateSNR(spec[2:f_nyquist + 1], f_test - 2)
    return snr




if __name__ == "__main__":
    file = Path("space_osr_200.csv")
    with file.open("a") as f:
        f.write("# order, bits, bits_before, snr, area\n")
    for order in range(2, 8):
        for bits in range(8, 24):
            print(f"{order=}, {bits=}")
            fmt = Q(1, 15)
            input = fmt.Signal()

            found = False
            for bits_before in range(1, 6):
                try:
                    noiseshaper = Noiseshaper(input, order=order, n_lev=2, osr=200, fmt=Q(bits_before, bits - bits_before))
                    snr = get_snr(fmt, input, noiseshaper)
                    found = True
                    break
                except ValueError as e:
                    print(f"# failed {order=}, {bits=}, {bits_before=}")
            if not found:
                with file.open("a") as f:
                        f.write(f"# failed {order}, {bits}, xxx, xxx\n")
                print(f"# failed finally {order=}, {bits=}")
                continue
            print(f"# found {order=}, {bits=}, {bits_before=}, {snr=}")


            from amaranth.back.verilog import convert
            verilog = convert(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
            area = get_size(noiseshaper, ports=[noiseshaper.input.value, noiseshaper.output])
            print(f"# found {order=}, {bits=}, {bits_before=}, {snr=}, {area=}")

            with file.open("a") as f:
                f.write(f"{order}, {bits}, {bits_before}, {snr}, {area}\n")

