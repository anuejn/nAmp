from util.db import db
import numpy as np

from util.plot_utils import plot_function


def get_performance(x):
    SAMPLERATE = 44100  # Hz
    SAMPLES = 2 ** 14
    FREQ = 10000  # Hz
    AMPLITUDE = 1e-3

    DURATION = SAMPLES / SAMPLERATE
    print("simulation duration: {:.2f}s".format(DURATION))

    t = np.linspace(0, DURATION, SAMPLES)
    sin = np.sin(t * 2 * np.pi * FREQ) * AMPLITUDE
    input_samples = (sin + 1) / 2

    from modulators.pwm import modulate
    modulated = modulate(input_samples, n_bits=x, oversampling_ratio=2)

    oversampled_rate = len(modulated) / DURATION
    print("oversampled rate is {:.2f}Mhz. oversampling factor is {}".format((oversampled_rate / 10e6),
                                                                            oversampled_rate // SAMPLERATE))

    changes = np.sum(modulated[:-1] != modulated[1:]) / 2
    switching_rate = changes / DURATION
    print("average switching frequency is {:.2f}kHz".format(switching_rate / 1000))

    from scipy.signal import decimate
    to_decimate = int(oversampled_rate / SAMPLERATE)
    decimated = modulated
    while to_decimate > 1:
        if to_decimate % 2 == 0:
            decimated = decimate(decimated, 2, ftype="iir", zero_phase=True)
            to_decimate /= 2
        else:
            decimated = decimate(decimated, int(to_decimate), ftype="iir", zero_phase=True)
            to_decimate = 1

    noise = decimated - input_samples
    noise_level = np.abs(np.average(noise))
    return db(noise_level), db(np.average(input_samples) / noise_level)

plot_function(get_performance, range(1, 12), ("noise level [db]", "SNR [db]"))