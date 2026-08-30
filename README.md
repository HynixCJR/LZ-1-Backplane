# LAZARUS-1 Backplane PCB
LAZARUS-1 is a 2U rackmount server designed to support decommissioned laptops and SFF (Mini-ITX) desktop/server motherboards. The system consists of the following main components:
1. Sheet metal + 3D-printed chassis (TBD)
2. Backplane PCB (here)
3. [Front-panel breakout PCB](https://github.com/HynixCJR/serverv2_front_panel_breakout)

> [!WARNING]
> This PCB design is currently a work in progress. The initial schematic design has been created, and revisions have been made to most of the schematic; however, the PCB remains incomplete as of this time.

> [!TIP]
> I did not use any AI to write this documentation! All words you see here are written entirely by me (Matthew Kong).

This repository contains all files relevant to the LAZARUS-1 backplane PCB. The PCB supports the following features:
1. 12 x SATA HDDs/SSDs (3.5 inch, hot-swappable, 12V and 5V current monitoring/protection)
2. Internal USB-C to the laptop/desktop motherboard that provides PD 3.0 up to 100W, supports DP alt mode, as well as USB 3.2 Gen 2 data transfer to USB hub; branches off to:
    1. Internal 2 x USB 3.2 Gen 2 (10Gbps) RTL9210b NVMe/SATA M.2 SSD slots
    2. Internal SDXC MicroSD card slot
    3. 2 x downstream USB 2.0 ports
    4. MIPI CSI port; for video input to LicheeRV Nano
3. LicheeRV Nano for a custom NanoKVM implementation; takes video input from USB-C port and emulates USB HID keyboard and mouse to provide full IPKVM support through a single USB-C port
4. Temperature monitoring
5. 4 x 4-pin PWM fan headers
6. External touchscreen display support through a dedicated display SPI header
7. Real-time current/voltage monitoring for all subsystems
8. 3 x RP2354B microcontrollers for telemetry, subsystem control, and IC programming
9. 24 pin ATX PSU power input, supports standard full-sized ATX PSUs
10. External power on breakout board with LED indication and external USB hub (see: [front panel breakout](https://github.com/HynixCJR/serverv2_front_panel_breakout))

The system is designed to have low power draw while providing extensive enterprise-level feature sets to what would otherwise be e-waste laptop computers.

## Subsystems
Documentation has been written for most of the subsystems present on this PCB, and they can be found in the [docs/Subsystems](/docs/Subsystems).

### USB-C Data
- [TUSB1064 USB Switch Subsystem](docs/Subsystems/TUSB1064_USB_Switch.md): The subsystem that flips the TX/RX lines of the USB-C connector based on cable orientation
- [USB7205C USB 3.2 Gen 2 Hub](docs/Subsystems/USB7205C_USB3_Hub.md): The USB 3.2 Gen 2 Hub IC that allows 5 USB devices to be connected to the single USB-C port
- [USB2244i USB2.0->SDXC MicroSD](docs/Subsystems/USB2244i_USB_to_SD.md): The subsystem that converts the USB 2.0 signal from the USB7205C USB hub to SDXC for the MicroSD card slot
- RTL9210b: The subsystem that converts a USB3.2 Gen 2 signal to a PCIe Gen 3 lane, for use in the M.2 NVMe/SATA slots on this board
- UCS2113 & Downstream USB 2.0 ports: The subsystem that splits off the USB 2.0 lanes from the USB7205C hub into physical USB 2.0 ports, with port power protection

### Power Delivery
- [TPS65987D PD Controller Subsystem](docs/Subsystems/TPS65987D_PD_Controller.md): The subsystem that controls USB-C PD 3.0 and communicates configuration to the connected device
- [TPS55288 Buck-Boost Converter](docs/Subsystems/TPS55288_Buck_Boost_Converter.md): The buck-boost converter that converts the +12V ATX PSU rail to the voltage/current needed for USB-C PD 3.0

### IPKVM
- [PS176 DP->HDMI Converter](docs/Subsystems/PS176_DP_to_HDMI.md): The subsystem that converts the DisplayPort signal (from the USB-C connector, through DP alt mode) to HDMI
- [LT6911C HDMI to MIPI CSI Converter](docs/Subsystems/LT6911C_HDMI_to_CSI.md): The subsystem that converts the HDMI signal from the PS176 to a MIPI CSI signal, which goes off to the LicheeRV Nano

### SATA Subsystem
- TPS259540 and TPS259530: eFuses for the SATA 12V and 5V rails, preventing the power rails from sagging upon SATA drive hotswap events
- MCP6002: Operational amplifier that magnifies the analog current signal from the TPS2595x0 eFuses, so that the RP2354 MCUs can read the current drawn

### Telemetry
- [RP2354B MCU Subsystem](docs/Subsystems/LT6911C_HDMI_to_CSI.md): The MCU that performs telemetry, programs the PD controller and USB hub, and coordinates various system events (e.g., power on)
- [PAC1954 Power Monitoring](docs/Subsystems/PAC1954_Power_Monitor.md): The subsystem that monitors accumulated voltages and currents across the power rails for most components on this board, and outputs power data over I2C to the LicheeRV Nano
- [MCP9808 Temperature Monitoring](docs/Subsystems/MCP9808_Temperature_Monitor.md): The subsystem that monitors chassis temperature and outputs data over I2C to the LicheeRV Nano

### Front Panel I/O
- Display header
- Power LED and switch header