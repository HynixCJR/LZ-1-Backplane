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

| Stages                               |   USB7205C   |   LX7167A    |
| ------------------------------------ | :----------: | :----------: |
| Initial Design                       | ✅ 2026-07-29 | ✅ 2026-07-25 |
| Basic Function Review/Documentation  | ✅ 2026-07-31 | ✅ 2026-07-30 |
| Extended Design Review/Documentation |              |              |
| Initial PCB layout                   |              |              |

## Port Layout
The USB7205C has four USB 3.2 Gen 2 downstream ports and one USB 2.0 downstream port. The LAZARUS-1 PCB has five devices connected to this hub, and so PortSplit is not used. The following is the port layout:


| Downstream Port Number | Configuration                             | Connected Device                         |
| ---------------------- | ----------------------------------------- | ---------------------------------------- |
| 1                      | USB 3.2 Gen 2 + USB 2.0 enabled           | RTL9210B_0 (for NVMe SSD 0)              |
| 2                      | USB 3.2 Gen 2 + USB 2.0 enabled           | RTL9210B_1 (for NVMe SSD 1)              |
| 3                      | Only USB 2.0 enabled                      | USB2244i SD card circuit                 |
| 4                      | Only USB 2.0 enabled                      | USB-A port (to LicheeRV Nano)            |
| 5                      | USB 2.0 enabled (no USB 3.2 Gen 2 option) | USB-A port (to external front panel hub) |

## Design

### Power
The USB7205C uses two supply rails:  VCORE and VDD33. VDD33 has an operating range of +3.0V to +3.6V per the datasheet, so +3.3V is directly supplied by the ATX PSU to this rail. This gives ample headroom. In case the voltage drops slightly. VCORE, on the other hand, has an operating range of +1.09V to +1.21V. The EVB uses +1.1V for this rail, which technically fits within the specification, but is only 0.01V away from the minimum recommended operating voltage. Hence, +1.15V is chosen. This is achieved using an LX7167 buck converter, using the configuration specified in its datasheet (but with R1 and R2 modified to satisfy VOUT of +1.15V).

Additional 100nF decoupling capacitors are placed on each VCORE and VDD33 pin, per the EVB.

---
### Configuration Straps
The USB7205C can be configured through its CFG pins, which control behaviours such as battery charging and non-removable ports when the chip is being reset (and before the SPI flash chip, OTP, or MCU can be read). The following are the strap configurations:

| Pin # | Pin name    | Configuration   | Description                            |
| ----- | ----------- | --------------- | -------------------------------------- |
| 69    | CFG_NON_REM | 10kΩ pull up    | Ports 1, 2, 3 non-removable            |
| 70    | CFG_BC_EN   | 200kΩ pull down | Battery charging disabled on all ports |
| 21    | CFG_STRAP1  | 10kΩ pull down  | Enables Config 3 (only config option)  |
| 22    | CFG_STRAP2  | 200kΩ pull down | Enables Config 3 (only config option)  |
| 23    | CFG_STRAP3  | 200kΩ pull down | Pin unused, so must be pulled down     |

Additionally, these are the configurations for power enable/overcurrent sense for the downstream ports and PortSplit:

| Pin # | Pin name    | Configuration        | Description                                                                                        |
| ----- | ----------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| 51    | PRT_CTL3_U3 | Float                | PortSplit on port 3; disabled by floating pin                                                      |
| 52    | PRT_CTL4_U3 | Float                | PortSplit on port 4; disabled by floating pin                                                      |
| 60    | PRT_CTL1    | 10kΩ pull up         | Power enable on port 1 (SSD_0): permanently enabled because this downstream device is embedded.    |
| 59    | PRT_CTL2    | 10kΩ pull up         | Power enable on port 2 (SSD_1): permanently enabled because this downstream device is embedded.    |
| 58    | PRT_CTL3    | 10kΩ pull up         | Power enable on port 3 (USB2244i): permanently enabled because this downstream device is embedded. |
| 57    | PRT_CTL4    | Connected to UCS2113 | Power enable on port 4 (USB Port 4): connected to UCS2113 to enable overcurrent protection.        |
| 77    | PRT_CTL5    | Connected to UCS2113 | Power enable on port 5 (USB Port 5): connected to UCS2113 to enable overcurrent protection.        |

> Note: PortSplit is a feature that splits the USB 3.2 Gen 2 TX/RX lanes from the USB 2.0 lanes, allowing you to support two embedded devices from a single downstream port. However, it is not used in this application because there aren't enough downstream USB devices to warrant splitting. Connecting each embedded device to its own downstream USB lane uses slightly less components, since otherwise the PortSplit pins need a pull up resistor.

> Note: PRT_CTLx is Power enable / overcurrent sense for downstream USB ports 1 to 5. When pulled low, the power supplied to the port is disabled, and when pulled high, the power is enabled. For ports 4 and 5 (the ones connected to physical USB ports), the PRT_CTLx pin is connected to a USB current monitor (UCS2113) that pulls the PRT_CTLx pin low upon overcurrent detection. For ports 1, 2, and 3 (the ones connected to the embedded RTL9210B SSD circuits, and the one connected to the SD card circuit), the PRT_CTLx pins are permanently pulled high to ensure power is never disabled.

Additionally, there are PF pins that are labelled as NC in the datasheet:

| Pin number | Pin name | Connection |
| ---------- | -------- | ---------- |
| 49         | PF8      | NC         |
| 50         | PF9      | NC         |
| 54         | PF12     | NC         |
| 56         | PF13     | NC         |

Other PF pins are listed below:

| Pin # | Pin name | Configuration | Description                                                                                                                                                                                                                                                                                               |
| ----- | -------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2     | VBUS_DET | 100k pull up  | Per the datasheet, the USB7205C monitors VBUS_DET to assert the D+ pull up resistor to signal a connection event.<br><br>"For self-powered applications with a permanently attached host, this pin should be pulled up, typically to VDD33."<br><br>Since the hub is self-powered, this pin is pulled up. |

---
### Crystal Oscillator
> *Pins: XTALO (97), XTALI (98)*

The USB7205C accepts a 25MHz crystal oscillator input with the following specifications, per the datasheet:

| Parameter                     | Nominal      | Maximum |
| ----------------------------- | ------------ | ------- |
| Frequency                     | 25.000 MHz   | -       |
| Frequency tolerance @ 25C     | -            | ±50 PPM |
| Frequency Deviation Over Time | ±3 to ±5 PPM | -       |
| Load Capacitance              | 20 pF        | -       |
| ESR                           | -            | 60Ω     |

The oscillator ([SOSET 25M 10PF 50PPM](https://www.lcsc.com/product-detail/C4944018.html?s_z=n_q_C4944018&globalKeyword=C4944018)) meets all of these specifications, with the exception of the load capacitance, which is 10pF instead of 20pF. However, the [EVB](https://www.microchip.com/en-us/development-tool/evb-usb7206) also uses a 10pF crystal as well, and so it is likely that the load capacitance can feasibly vary (with the support of the right capacitors). Hence, this design uses the same crystal implementation as the EVB; however, the EVB designs it for 5pF stray capacitance, which is quite high. This design halves the estimated stray capacitance, as the crystal will be placed very close to the USB7205C. So, the capacitor values are 15pF.

---
### I2S Pins
> *Pins: I2S_SDI (44), I2S_SDO (45), I2S_SCK (46), I2S_LRCK (47), I2S_MCLK (48), MIC_DET (66)*

I2S is used by the USB7205C as audio output; however, the LAZARUS-1 backplane is not designed to support audio output (the LicheeRV Nano cannot accept I2S audio through its GPIO pin headers), and so these pins are unused. As specified in the datasheet, they are weakly pulled down by 100kΩ resistors.

---
### Master I2C Pins
> *Pins: MSTR_I2C_CLK (61), MSTR_I2C_DATA (3)*

The master I2C channel is only used to control the UCS2113 USB power switch to configure power limits on downstream USB ports 4 and 5. 10kΩ pull ups are added to ensure that I2C can function reliably.

---
### Slave I2C Pins
> *Pins: SLV_I2C_CLK (75), SLV_I2C_SDA (76)*

The slave I2C channel is used to receive configuration data from an RP2350B. This is used to avoid having to use an external SPI flash chip (or relying on OTP), thus saving on PCB space. In accordance with the datasheet, 10kΩ pull ups are added to ensure that I2C can function reliably.

---
### SPI Pins
> *Pins: SPI_CLK (68), SPI_D0 (70), SPI_D1 (71), SPI_D2 (72), SPI_D3 (73)*

The USB7205C optionally uses SPI for configuration through an external SPI flash memory. In this design, the SPI flash memory is avoided to save on PCB space, instead relying on an RP2350B to send configuration data over I2C. Hence, these SPI pins are unused. Per the datasheet, they must be weakly pulled down to GND, and so they are pulled down by 100kΩ resistors. However, SPI_D0 is shared with CFG_BC_EN, and so it follows the configuration specified in [Configuration Straps](#configuration-straps).

---
### Other pins
> *Pins: TEST[1:3] (63, 64, 65), ATEST (96), TESTEN (24), RBIAS (100), RESET_N (1)*

- TEST[1:3]: The datasheet specifies that all three TEST pins must be pulled up through a 10kΩ resistor at all times.
- ATEST: The datasheet specifies that this pin must be left disconnected at all times.
- TESTEN: The datasheet specifies that this pin must always be shorted to GND.
- RBIAS: The datasheet specifies that this pin must be pulled down to GND through a 12kΩ±1% resistor, with the resistor placed as close as possible to the pin, and dedicated connection to the GND plane.
- RESET_N: Used to reset the device. To match the EVB, this pin is connected to a 10kΩ pull up, with a 100nF decoupling capacitor to ensure stability.