fs = 44100
nyquist = fs/2

from scipy import signal
import numpy as np
f1, f2, f3 = 50, 120, 400
numtaps = 301
fir_low = signal.firwin(numtaps, [f1, f2], pass_zero=False, fs=fs)
fir_mid = signal.firwin(numtaps, [f2, f3], pass_zero=False, fs=fs)
fir_high = signal.firwin(numtaps, f3, pass_zero=False, fs=fs)


def plot_fir(*firs):
    from pylab import figure, clf, plot, xlabel, ylabel, ylim, title, grid, show
    figure(2)
    clf()
    for fir in firs:
        w, h = signal.freqz(fir, worN=8000)
        plot((w/np.pi)*nyquist, np.absolute(h), linewidth=2)
    xlabel('Frequency (Hz)')
    ylabel('Gain')
    title('Frequency Response')
    ylim(-0.05, 2.05)
    grid(True)
    show()
plot_fir(fir_low, fir_mid, fir_high)

import jack
client = jack.Client("speaker-fx")

bypass = False
last_buffers = []
@client.set_process_callback
def process(frames):
    assert len(client.inports) == len(client.outports)
    assert frames == client.blocksize
    for i, (input, output) in enumerate(zip(client.inports, client.outports)):
        input_buffer = input.get_array()
        low = np.convolve(np.concatenate((last_buffers[i], input_buffer)), fir_low, mode='same')[numtaps:numtaps + frames]
        mid = np.convolve(np.concatenate((last_buffers[i], input_buffer)), fir_low, mode='same')[numtaps:numtaps + frames]
        high = np.convolve(np.concatenate((last_buffers[i], input_buffer)), fir_high, mode='same')[numtaps:numtaps + frames]

        zero_points, = np.where(np.sign(mid[:-1]) != np.sign(mid)[1:])
        for this, next in zip(zero_points, zero_points[1:]):
            mid[this:next] = np.concatenate((mid[this:next], mid[this:next]))[::2]

        if not bypass:
            output.get_array()[:] = low + high
        else:
         last_buffers[i][:] = input_buffer


for channel in 'L', 'R':
    client.inports.register('input_{0}'.format(channel))
    client.outports.register('output_{0}'.format(channel))

with client:
    last_buffers = [np.zeros(client.blocksize) for _ in client.inports]
    capture = client.get_ports(is_physical=False, is_output=True)
    if not capture:
        raise RuntimeError('No capture ports')
    for src, dest in zip([c for c in capture if "Firefox" in c.name] , client.inports):
        client.connect(src, dest)

    playback = client.get_ports(is_physical=True,  is_input=True)
    if not playback:
        raise RuntimeError('No playback ports')
    for src, dest in zip(client.outports, playback):
        client.connect(src, dest)

    try:
        while True:
            input()
            bypass = not bypass
    except KeyboardInterrupt:
        print('\nInterrupted by user')
