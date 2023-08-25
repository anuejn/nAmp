# FPGA-Ignite ASIC tapeout

This folder contains files that can be used for taping out a noiseshaper as part of an ASIC using the openroad flow.
The [noiseshaper.v](./noiseshaper.v) file is auto-generated using amaranth-lang from the [noiseshaper_cifb.py](../gateware/noiseshaper_cifb.py) script and thus not very readable.
It contains a module named `top` that has `clk` and `rst` inputs (the `clk` should be ~10Mhz). Data is fed in using the `in` port as 16bit signed values centred around 0. The `out` port is a 1bit signal that should be 50% of the time high when the input is 0.

In case of the FPGA-Ignite eFPGA, all ports except `clk` should be connected to the FPGA-fabric. `clk` should be connected to the main clock tree.

## building
The design is tested to be buildable using openlane2:

```sh
# replace ~/tmp/openlane2/shell.nix with the actual path to your openlane2 checkout
# probably it is also possible to build using openlane1 with different commands.
nix-shell ~/tmp/openlane2/shell.nix --run "openlane openlane.json"
```

And the resulting hardened design can be viewed using:

```sh
nix-shell ~/tmp/openlane2/shell.nix --last-run --flow OpenInOpenRoad openlane.json
```