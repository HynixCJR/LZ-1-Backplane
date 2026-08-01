# USB2244i USB to SD Card Subsystem
## Preamble
A simple, 480Mbps SD card reader is included on the LAZARUS-1 backplane PCB simply to allow easy "permanent" storage for things like ISOs, so that the laptop can boot into a live linux environment (or something else like Windows, if you're crazy) in case a new OS image needs to be flashed. It's intended to be exposed as a regular SD card reader to the OS, and so it's basically just another USB storage device. Hence, it's connected through the USB7205C hub to the laptop, and not to the LicheeRV Nano or RP2350's on the board. This unfortunately prevents the user from loading ISOs directly to the SD card when the host machine is off. However, the LicheeRV Nano itself also has an SD card slot, so this purpose is already fulfilled.

The USB2244i is the industrial version (higher rated temperature range) of the USB2244, which is a standard single chip USB 2.0 to SD card conversion IC. it supports many different flash media standards other than just SD, but for this purpose, only SD is used. This chip was mainly chosen because it is a Microchip IC, meaning it can be sourced for free from Microchip's free sample program for students.

## Description
The USB2244i is a dedicated, fully integrated single chip USB 2.0 to SD card controller, supporting (theoretical) 480Mbps SD card read/write speeds. It supports several flash media card specifications, but the one relevant to this application is SDHC/SDXC. It comes in a smaller 36-QFN package, as compared to more modern Microchip ICs like the USB2642, while consuming the same current when active. In suspend mode, it consumes only 350uA at +3.3V (~1mW), whereas it consumes 135mA at +3.3V (~0.5W) when active. It also supplies up to 200mA of current to the attached SD card through an integrated Power FET, allowing for better control of the SD card's power draw during suspend states.

## Revision Progress

| Stages                               |   USB2244i   |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-12 |
| Basic Function Review/Documentation  | ✅ 2026-08-01 |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |

## Design

### Power
There are four power rails used by the USB2244i, as described in the table below.

| Power rail | Pin numbers   | Description                          | Configuration                                                                                                          |
| ---------- | ------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| VDD33      | 6, 14, 22, 36 | Main 3.3 V power and regulator input | Each pin has its own 100nF decoupling capacitor, per the USB2244 design checklist. Connected to the ATX PSU 3.3V rail. |
| VDDA33     | 36            | Analog 3.3 V power input             | Connected to the ATX PSU 3.3V rail, with a 100nF decoupling capacitor, per the USB2244 design checklist.               |
| VDD18      | 13            | 1.8V core regulator output           | Connected to a 1uF decoupling capacitor, per the datasheet.                                                            |
| VDD18PLL   | 34            | 1.8V PLL regulator output            | Connected to a 1uF decoupling capacitor, per the datasheet.                                                            |

> Note: VDD18 and VDD18PLL are not supposed to power external components, as they are intended to only power internal circuitry.

---
### USB 2.0 Pins
> *Pins: USB+ (2), USB- (3)*

Per the USB2244 Hardware Design Checklist, the USB2244i helpfully includes all the necessary terminations and resistors for USB on-chip, and so the USB 2.0 pins can be directly connected to the USB 2.0 pins of the USB7205C.

---
### SD Pins
> *Pins: SD_D0 (5), SD_D1 (1), SD_D2, (25), SD_D3 (23), SD_D4 (20), SD_D5 (10), SD_D6 (8), SD_D7 (7), SD_CLK (9), SD_CMD (11), SD_nCD (26)*

Because the USB2244i supports so many flash media card standards, there are more SD data pins than necessary for this application. SDXC only uses four data pins, and so SD_D4 to SD_D7 are left floating, which follows the USB2244 Hardware Design Checklist's recommendation. For SD_D0 to SD_D3, SD_CMD, and SD_CLK, series resistors are labelled as optional in the Hardware Design Checklist, and are thus not included in this design. They are therefore connected directly to their corresponding pins on the MicroSD card slot.

 SD_nCD (card detect) is connected directly to the corresponding pin on the MicroSD card slot, per the design guide. SD_WP (write protect) must be pulled down for MicroSD card functionality per the datasheet, but a specific pull down resistance is not specified. So, a standard 10kΩ resistor is used; if the value is incorrect, it can be swapped with another resistance value.

---
### Card Power Pins
> *Pin: CRD_PWR (21)*

The USB2244i can provide up to 200mA through the CRD_PWR pin to a connected MicroSD card. Routing power to the MicroSD through this pin is beneficial because the USB2244i has an internal power switch that disables power if more than 200mA is drawn. Per the design guide, a 4.7uF decoupling capacitor is added to this rail.

---
### Crystal Oscillator
> *Pins: XTAL1 (33), XTAL2 (32)*

The USB2244i requires a parallel resonant, fundamental mode 24 MHz reference clock to function, with a maximum tolerance of ±350 ppm. The crystal chosen for this design is 24 MHz and has a frequency stability of ±10 ppm, which is way lower than the maximum.

The design guide specifies that the stray capacitance can be assumed to be 1-2pF. However, since 10pF capacitors are used elsewhere on the PCB, 10pF capacitors are used for this design - which, when combined with the 8pF load capacitance of the crystal oscillator, leads to 3pF stray capacitance. This is still realistic for the PCB, but the capacitors can be replaced if needed.

---
### EEPROM Pins
> *Pins: TXD/SCK (31), RXD_SDA (27)*

The USB2244i supports an (optional) external EEPROM to program various configurations. However, this design does not implement the EEPROM, since it uses only the default configuration. Per the Hardware Design Checklist, if an EEPROM is not included, pull up resistors are still required. So, on both pins, 10kΩ pull up resistors are added, with no further connection to an EEPROM.

---
### Other Pins
> *Pins: RBIAS (35), LED (1), TEST (28), RESET_N (18)*

- RBIAS: Per the datasheet, this pin is pulled down by a 12kΩ±1% resistor to set up bias currents for internal circuitry. It must be placed as close as possible to the RBIAS pin, with a direct low impedance path to the ground plane.
- LED: The USB2244i has a pin to indicate media insertion/access to an LED. Since the MicroSD card is hidden internally in this application, an LED is not needed, and thus this pin is left floating.
- TEST: Per the datasheet, this pin must be tied to ground for normal operation.
- RESET_N: An active low reset signal to the USB2244i. Per the Hardware Design Guide, this pin should be pulled up by a 10kΩ resistor, with a 1uF decoupling capacitor to filter noise, if the reset is intended to be triggered by the power supply.