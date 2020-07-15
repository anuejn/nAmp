import numpy as np
import matplotlib.pylab as plt
from tqdm import tqdm
from scipy.fftpack import fft
from scipy.signal.windows import hamming

duration, freq, samplerate = None, None, None


def init_plot(d, f, s):
    global duration, freq, samplerate
    duration, freq, samplerate = d, f, s


def plot_one_wave(**signals):
    plt.title("Signal in time domain")
    plt.xlabel('time [samples]')
    plt.ylabel('amplitude')
    for name, s in signals.items():
        to_plot = s[len(s) // 2: len(s) // 2 + int(len(s) / duration / freq) * 2]
        plt.plot(to_plot, label=name)
    plt.legend()
    plt.show()


def plot_spectrum(*, log=True, **signals):
    plt.title('Spectrum')
    plt.grid()
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude')
    if log:
        plt.yscale("log")
    plt.figure(1, (20, 10))

    for name, s in signals.items():
        N = int(samplerate * duration)
        window = hamming(len(s))
        yf = fft((s - np.average(s)) * window)
        tf = np.linspace(.0, (len(s) / duration / 2), int(N / 2))
        spectrum = 2. / N * np.abs(yf[0:N // 2])
        plt.plot(tf, spectrum, label=name)

    plt.legend()
    plt.show()


def plot_signals(**signals):
    plot_one_wave(**signals)
    plot_spectrum(**signals)


def plot_function(f, xx, legend):
    plt.grid()
    plt.figure(1, (20, 10))
    yy = []
    for x in tqdm(xx):
        yy.append(f(x))

    for i, series in enumerate(np.transpose(yy)):
        plt.plot(xx, series, label=legend[i])
    plt.legend()
    plt.show()
