# nAmp
research & experiments for outputting analog audio using digital IO pins.

Most notably, this repository contains an [amaranth-lang](https://github.com/amaranth-lang/amaranth)
[fixed-point library](gateware/fixed_point.py) and an implementation of a 
[delta-sigma noiseshaper](gateware/noiseshaper_cifb.py) that can be used to output
analog audio from FPGAs or ASICs.

The noiseshaper will (hopefully) be taped out as part of the
[FPGA-Ignite Summer School](https://fpga-ignite.github.io/) hackathon ASIC. For the details of the
physical implementation, see [the openlane folder](./openlane/).

Originally, this repository contained ideas and research for building a fully digital class D 
amplifier using an FPGA (thus the name), however that effort stalled a bit. If you are interested 
in pursuing this further, feel free to contact me :).
