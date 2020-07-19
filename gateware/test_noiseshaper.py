import unittest

from nmigen import *
from nmigen.sim.pysim import Simulator
import numpy as np

from fixed_point import *
from noiseshaper import Noiseshaper


class TestNoiseshaper(unittest.TestCase):
    def test_sim_noiseshaper(self):
        fmt = Q(8, 64)
        input = fmt.Signal()
        dut = Noiseshaper(input, order=4, n_lev=2)

        sim = Simulator(dut)
        sim.add_clock(1 / 100e6)

        input_hist = []
        output_hist = []
        integrators_hist = [[] for _ in dut.integrators]

        n = 8192
        f_nyquist = int(np.ceil(n/(2.*dut.osr)))
        f_test = np.floor(2./3.*f_nyquist)
        u = 0.5 * np.sin(2 * np.pi * f_test / n * np.arange(n))

        def testbench():
            for x in u:
                yield input.eq(x)

                input_hist.append(fmt.to_float((yield input.value)))
                output_hist.append(fmt.to_float((yield dut.quantized_value.value)))
                for i, integrator in enumerate(dut.integrators):
                    integrators_hist[i].append(fmt.to_float((yield integrator.value)))

                yield
        sim.add_sync_process(testbench)

        sim.run()

        from matplotlib import pyplot as plt
        plt.plot(np.arange(n), output_hist, linewidth=1, label="output")
        plt.plot(np.arange(n), input_hist, label="input")
        plt.legend()
        plt.show()
        for i, integrator_hist in reversed(list(enumerate(integrators_hist))):
            plt.plot(np.arange(n), integrator_hist, linewidth=1, label="integrator {}".format(i))
        plt.legend()
        plt.show()

        import deltasigma as ds
        f = np.linspace(0, 0.5, int(n / 2. + 1))
        spec = np.fft.fft(output_hist * ds.ds_hann(n)) / (n / 4)
        plt.plot(f, ds.dbv(spec[:int(n / 2. + 1)]), 'b', label='Simulation')
        ds.figureMagic([0, 0.5], 0.05, None, [-160, 0], 20, None, (16, 6), 'Output Spectrum')
        plt.xlabel('Normalized Frequency')
        plt.ylabel('dBFS')
        snr = ds.calculateSNR(spec[2:f_nyquist + 1], f_test - 2)
        plt.text(0.05, -10, 'SNR = %4.1fdB @ OSR = %d' % (snr, dut.osr), verticalalignment='center')
        NBW = 1.5 / n
        Sqq = 4 * ds.evalTF(dut.h, np.exp(2j * np.pi * f)) ** 2 / 3.
        plt.plot(f, ds.dbp(Sqq * NBW), 'm', linewidth=2, label='Expected PSD')
        plt.text(0.49, -90, 'NBW = %4.1E x $f_s$' % NBW, horizontalalignment='right')
        plt.legend(loc=4)
        plt.show()
