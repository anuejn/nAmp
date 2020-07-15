from numba import jit
import numpy as np
from scipy.signal import resample


def modulate(input, *, n_bits, oversampling_ratio):
    resampled = resample(input, len(input) * oversampling_ratio)

    quantized_samples = np.array(np.round(resampled * 2 ** n_bits), dtype=int)

    @jit(nopython=True, parallel=True)
    def loop():
        output = np.zeros(len(resampled) * 2 ** n_bits)
        for i, sample in enumerate(quantized_samples):
            for j in range(sample):
                output[(i * 2 ** n_bits) + j] = True
        return output

    return loop()
