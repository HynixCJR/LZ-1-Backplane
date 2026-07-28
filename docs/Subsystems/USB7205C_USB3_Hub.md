# USB7205C USB 3.2 Gen 2 5-port Hub Subsystem

## Preamble
The LAZARUS-1 Backplane PCB has several downstream USB devices (two SSDs, an SD card, a USB port for the LicheeRV Nano to emulate keyboard/mouse input, and a USB port to go to the external front panel USB hub). To ensure that they can all communicate with the host laptop device through a single USB-C port, and to ensure that data transfer speeds can be efficiently negotiated between each device, a USB hub is needed. The upstream USB-C port operates at USB 3.2 Gen 2 (10Gbps) speeds, with five downstream USB devices connected, and hence a 5-port USB 3.2 Gen 2 hub IC is needed.

The USB7205C was chosen for this purpose, for the following reasons:
1. Microchip has excellent student support (they give free samples for a lot of their products to students), and hence a hub IC from Microchip will not add to the BOM cost.
2. Of Microchip's offerings, the USB7205C is the only hub listed on their site that meets the requirements with no more than 5 ports. The other options include:
	1. USB7206C (the original chip used in this design), which is a higher binned variant of the USB7205C that has 6 ports instead of 5. However, since only 5 ports are needed, the extra 6th port is wasted and must have its traces tied to 3.3V, which increases routing complexity slightly. the USB7206 (non C) is also an option, however this is just an older revision of the same chip.
	2. USB7216C, which is similar to the USB7206C in that it has 6 downstream ports. However, it has USB Type-C support on downstream port 1, which introduces a few extra traces needed for USB Type-C (CC, SBU, etc.) - and these are not needed, as there are no downstream USB-C ports on this device. It also uses more power to run.

## Description
The USB7205C is a 5 port USB 3.2 Gen 2 Hub IC. It has one upstream USB 3.2 Gen 2 port (with both USB 3 and USB 2 lanes routed), and exposes four standard USB 3.2 Gen 2 downstream ports + one USB 2.0 downstream port. It supports FlexConnect (which allows any port to act as the upstream port), USB Bridging (converts USB to I2C, SPI, I2S, and GPIO), PortSwap (allows the differential USB 2.0 traces to be swapped in firmware), PHYBoost (USB redriving), VariSense (sensitivity tuning), and PortSplit (splitting USB 3 lanes from USB 2 lanes). All of these require custom programming through Microchip's MPLab software, which requires One-Time-Programming (OTP), external SPI flash memory, or SMBus (which requires an external MCU). To save on PCB space, an external SPI flash memory chip is not used. Instead, SMBus is used, connecting the USB7205C to an RP2350b MCU for configuration.

## Revision Progress

| Stages                               | USB7205C |   LX7167A    |
| ------------------------------------ | :------: | :----------: |
| Initial Design                       |          | ✅ 2026-07-25 |
| Basic Function Review/Documentation  |          |              |
| Extended Design Review/Documentation |          |              |
| Initial PCB layout                   |          |              |

## Design

### Power

### Configuration Straps
The USB7205C can be configured through its CFG pins, which control behaviours such as battery charging and non-removable ports when the chip is being reset (and before the SPI flash chip, OTP, or MCU can be read). The following are the 


| Pin # | Pin name    | Configuration   | Description                            |
| ----- | ----------- | --------------- | -------------------------------------- |
| 69    | CFG_NON_REM | 10kΩ pull up    | Ports 1, 2, 3 non-removable            |
| 70    | CFG_BC_EN   | 200kΩ pull down | Battery charging disabled on all ports |
| 21    | CFG_STRAP1  | 10kΩ pull down  | Enables Config 3 (only config option)  |
| 22    | CFG_STRAP2  | 200kΩ pull down | Enables Config 3 (only config option)  |
| 23    | CFG_STRAP3  | 200kΩ pull down | Pin unused, so must be pulled down     |
|       |             |                 |                                        |
