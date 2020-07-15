# class-d-igital
A fully digital class d amp using an FPGA

## General Architecture
![Architecture Diagram](https://g.gravizo.com/source/custom_mark10?https%3A%2F%2Fraw.githubusercontent.com%2FTLmaK0%2Fgravizo%2Fmaster%2FREADME.md)
<details> 
<summary></summary>
custom_mark10
  digraph {
    node [shape=box];
    rankdir=LR;
    usb [shape=none];
    usb -> stm32
    
    i2s [shape=none];
    
    i2s -> fpga [label=pcm]
    stm32 -> fpga [label=pcm]
    
    fpga -> mosfet [label="1 bit stream"]
    mosfet [shape=none];
    
  }
custom_mark10
</details>


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

## Modulator Simulation