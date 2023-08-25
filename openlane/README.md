# openlane ASIC tapeout

this folder contains files that can be used for taping out a noiseshaper as part of an ASIC.
the [noiseshaper.v](./noiseshaper.v) file is auto-generated using nmigen from  the [noiseshaper_cifb.py](../gateware/noiseshaper_cifb.py) script and thus not very readable.
It contains a module named `top` that has `clk` and `rst` inputs (the clk should be ~10Mhz). Data is fed in using the `in` port as 16bit signed values centred around 0. The `out` port is a 1bit signal that should be 50% of the time high when the input is 0.

The design is tested to be buildable using openlane2.
