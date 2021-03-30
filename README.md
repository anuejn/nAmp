# class-d-igital
A fully digital class d amp using an FPGA

## Modulator research
Finding a well suited modulator to implement in the FPGA is one of the most important issues.
There are several approaches that could be taken: 

| modulator                    | pros                                   | cons                                                                  |
| ---------------------------- | -------------------------------------- | --------------------------------------------------------------------- |
| PWM (Pulse Width Modulation) | + very constant switching frequency    | - Only 8bit (48dB SNR) resolution is practical (600kHz * 2^8 = 153Mhz) |
| PPM (Pulse Pause Modulation) | + better dynamic range than PWM        | - Many Switching Processes for high amplitudes                        |
|                              |                                        | - Not garantueed to be out of audio band                              |
| Delta-Sigma                  | + Very high dynamic range is achivable | - Many Switching Processes (Poor Power Performance)                   |

-> A custom modulator needs to be created to meet the requirements of high SNR, low switching frequency (-> power efficiency)   
    and moderate internal clock (-> implementability in the fpga)
-> Simulation is needed!

