# RP2354B Microcontroller Subsystem

## Preamble
The LAZARUS-1 PCB implements three RP2354B MCUs to control pretty much all other components on the board. This includes: PWM fans, SATA ports (port enabling, fault detection, current sensing, and DSS pin enabling), power sequencing/LED control for the host laptop, SSD enabling, PS176 enabling, downstream USB 2.0 port fault detection, and programming for the USB7205C, TPS65987D, and TPS55288. Dedicated MCUs to control all of these components are used instead of GPIO expanders because:
1. Dedicated ADCs are needed to read the analog signals from the SATA eFuses for current monitoring (the RP2354B is chosen over the smaller RP2354A because it has 8 ADC channels exposed vs. 4, and 24 are needed in total). The LicheeRV Nano only has one exposed ADC channel, and so dedicated MCUs are needed.
2. Power sequencing ideally occurs on a bare metal system instead of an SBC for reliability purposes, thus requiring an MCU.
3. Base functionality of the entire system (other than IPKVM and temperature/current monitoring) should be available in absence of an SBC, in case a failure occurs on it. The USB7205C and TPS65987D (and by extension, the TPS55288) require programming over I2C because external flash chips are omitted in this design, and so MCUs are preferred for this purpose.
4. Since the RP2354B's can be implemented fairly minimally (requiring only a crystal oscillator and some decoupling capacitors), and so it does not take substantially more board space than a GPIO expander.

The RP2354B was specifically chosen for the following reasons:
1. It's fairly cheap ($1.62 USD per chip on LCSC).
2. It's easy to program because it's a Raspberry Pi product
3. It has an integrated 2MB flash, omitting the need for an external SPI flash chip.
4. It has enough GPIO to fulfill the needs of this PCB.
5. It has a relatively high number of ADC channels, which are needed for current monitoring through the SATA eFuses.

This design is largely based on the official [RP2350 Hardware Design Guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-1-hardware-design-with-rp2350.pdf), which implements a minimal design example of the RP2350 (which is pin compatible with the RP2354). However, the design removes the physical RESET button, replacing it with a single pad that can be shorted to GND with a wire if needed. Moreover, the USB port, along with the BOOTSEL button, are replaced with a 3-pin header for SWD; this will require an external SWD programmer, but provides a substantial PCB space savings. Additionally, a single UART TX/RX lane, along with GND, are exposed as pads on the PCB. Other than those modifications (and the lack of an external SPI flash, since the RP2354 has an internal flash), the design is very similar to the linked design guide.

## Description
The RP2354B is a microcontroller from Raspberry Pi that is pin compatible with the RP2350. It features 48 GPIO pins, 8 of which are connected to its 8 ADCs. In the LAZARUS-1 Backplane PCB, it is used to control the PWM fans, SATA ports (port enabling, fault detection, current sensing, and DSS pin enabling), power sequencing/LED control for the host laptop, SSD enabling, PS176 enabling, downstream USB 2.0 port fault detection, and programming for the USB7205C, TPS65987D, and TPS55288.

## Revision Progress

| Stages                               |   RP2354B    |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-12 |
| Basic Function Review/Documentation  | ✅ 2026-07-31 |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |

## Design
The design of this subsystem is largely based on the official [RP2350 Hardware Design Guide](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-1-hardware-design-with-rp2350.pdf).

---
### USB, SWDIO, and UART
The RP2350 ordinarily uses USB for programming or booting. However, to save valuable PCB space, the USB connector has been removed, along with the BOOTSEL button that enables USB booting. Instead, the SWDIO pins (which are exposed to a 3-pin header) are used for programming, which requires a SWD programmer.

As a backup, UART is also exposed on GPIO28 and GPIO29 (UART0 TX and RX) as pads on the PCB.

---
### Input Power Supply
The official design guide supplies power to the RP2350 using a Micro USB connector, with an LDO to step down the voltage from +5V to +3.3V. However, since the LAZARUS-1 PCB has a dedicated +3.3V rail from its ATX PSU, +3.3V is simply siphoned from that rail to the RP2354B.

It's worth noting that the *source* of the +3.3V varies depending on which RP2354B is examined. Specifically, RP2354B_1 and RP2354B_2 source their +3.3V power from the regular +3V3DC pins of the ATX PSU connector, whereas RP2354B_0 sources its +3.3V power from the +5VSB (a +5V rail that is on even when the PS_ON# has not been grounded). This is because RP2354B_0 is responsible for power sequencing and hence must be on at all times.

Following the design guide, 100nF decoupling capacitors are placed on each +3.3V input pin. The design guide mentions that some decoupling capacitors are necessarily shared due to routing complexity (they use a 2 layer board), but this design can avoid those complexities by using a 4 or 6 layer PCB and by routing components on the bottom side of the PCB (if needed). These decoupling capacitors must be placed as close as possible to the input power pins.

---
### Internal Regulator
> *Pins: VREG_VIN (64), VREG_LX (63), VREG_FB (65), VREG_PGND (62), VREG_AVDD (61)*

The RP2354B has an internal switching regulator that steps down the +3.3V supplied by the PSU to +1.1V, which is used for DVDD. Following the design guide:
- a 4.7uF decoupling capacitor is placed on VREG_AVDD, with a 33Ω resistor between it and +3.3V;
- VREG_VIN is directly connected to +3.3V;
- VREG_FB is directly connected to +1.1V with a 4.7uF decoupling capacitor;
- VREG_LX is connected to +1.1V through a 3.3uH inductor, and;
- VREG_PGND is connected to GND.

The 3.3uH inductor chosen for this design is similar to the one used in the design guide, with similar saturation current. lower DCR, and a slightly larger package.

Similar to the +3.3V rail, decoupling 100nF capacitors are included for each pin, with the exception of DVDD (pin 10), which has a 4.7uF decoupling capacitor in accordance with the design guide.

---
### SPI Flash Pins
> *Pins: QSPI_SD3 (70), QSPI_SCLK (71), QSPI_SD0 (72), QSPI_SD2 (73), QSPI_SD1 (74), QSPI_SS# (75)*

The RP2354B has an internal 2MB flash, and so an external SPI flash chip is not needed. Per the datasheet, the internal flash's pins are shorted to the same QSPI output pins of the QFN package, and so the same functionalities may be used with the QSPI pins as the RP2350. This includes using QSPI_SS as a BOOTSEL button, though this is not included in this design because USB is omitted. However, additional resistors As such, all of the QSPI pins are left floating. However, the QSPI_IOVDD pin is still kept at +3.3V.

---
### Crystal Oscillator
> *Pins: XIN (30), XOUT (31)*

The crystal oscillator configuration used in the design guide is very specific and likely only works with that specific oscillator. Unfortunately, that oscillator is rather expensive to purchase. So, this design replaces it with an oscillator that has the exact same load capacitance and frequency stability, but 10Ω higher ESR. This is not *too* far off from the design guide, so the same 1kΩ resistor is used, but it can be replaced if necessary. Otherwise, the 15pF capacitors are the same.

---
### I2C Pins
> *Pins: GPIO0/SDA0 (77), GPIO1/SCL0 (78), GPIO38/SDA1 (47), GPIO39/SCL1 (48), GPIO37/IRQ1 (46)*

Both I2C0 and I2C1 channels are used in this design. I2C0 is a slave interface that is connected to the LicheeRV Nano's I2C1 (master) channel, and this is true for all three RP2354B's used in this design. This allows the LicheeRV Nano to request telemetry data (or send control signals) to the RP2350B. Since there are multiple devices using this interface, the 10kΩ pull up resistors are included in the LicheeRV Nano schematic page, and no where else.

The I2C1 channel of the RP2354B is a master interface to allow the RP2354B to program any connected devices, namely the TPS65987D and the USB7205C. On the I2C1 channel, 10kΩ pull up resistors are included for the SDA, SCL, and IRQ traces, which is fine since there is only ever one device on each channel. Note that RP2354B_2 does not have any device connected to its I2C1 channel, and so those pins are left floating.

---
### ADC Pins
> *Pins: GPIO40 to GPIO47*

The RP2354B has eight ADC channels. In this design, each ADC channel reads the analog current monitor reading from the eFuse of either the 5V or 12V rail of each SATA port. Since there are 12 SATA ports, and two voltage rails each, a total of 24 ADC channels are needed, hence the use of three RP2354Bs. Therefore, all three RP2354Bs have each of their ADCs occupied by one of the eFuse current monitor outputs. Below is the table detailing which voltage rail and SATA port number correspond to the ADCs of each RP2354B.

| RP2354B Number | Pin name    | Voltage Rail Monitored | SATA Port Number |
| -------------- | ----------- | ---------------------- | ---------------- |
| 0              | GPIO40/ADC0 | 12V                    | 0                |
| 0              | GPIO41/ADC1 | 5V                     | 0                |
| 0              | GPIO42/ADC2 | 12V                    | 1                |
| 0              | GPIO43/ADC3 | 5V                     | 1                |
| 0              | GPIO44/ADC4 | 12V                    | 2                |
| 0              | GPIO45/ADC5 | 5V                     | 2                |
| 0              | GPIO46/ADC6 | 12V                    | 3                |
| 0              | GPIO47/ADC7 | 5V                     | 3                |
| 1              | GPIO40/ADC0 | 12V                    | 4                |
| 1              | GPIO41/ADC1 | 5V                     | 4                |
| 1              | GPIO42/ADC2 | 12V                    | 5                |
| 1              | GPIO43/ADC3 | 5V                     | 5                |
| 1              | GPIO44/ADC4 | 12V                    | 6                |
| 1              | GPIO45/ADC5 | 5V                     | 6                |
| 1              | GPIO46/ADC6 | 12V                    | 7                |
| 1              | GPIO47/ADC7 | 5V                     | 7                |
| 2              | GPIO40/ADC0 | 12V                    | 8                |
| 2              | GPIO41/ADC1 | 5V                     | 8                |
| 2              | GPIO42/ADC2 | 12V                    | 9                |
| 2              | GPIO43/ADC3 | 5V                     | 9                |
| 2              | GPIO44/ADC4 | 12V                    | 10               |
| 2              | GPIO45/ADC5 | 5V                     | 10               |
| 2              | GPIO46/ADC6 | 12V                    | 11               |
| 2              | GPIO47/ADC7 | 5V                     | 11               |
