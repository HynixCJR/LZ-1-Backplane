# TPS65987D USB-C PD 3.0 Controller
## Preamble
The USB-C PD controller chosen for the LAZARUS-1 PCB is actually labelled as Not Recommended for New Designs (NRND), and has relatively low stock on LCSC. However, it was still chosen for the following reasons:
1. As of the time of writing, it is the only *readily available* PD controller that supports 100W PD, DRP, DisplayPort alt-mode, and an integrated power path from TI.
2. As of the time of writing, it is also the only *well documented* PD controller that supports these features, from any company.
3. It can still be purchased for relatively cheap on LCSC, albeit with low stock. Get them while you can, I guess.

Point number 1 relies heavily on the "readily available" part because I started this project literally *just as* TI released the TPS26743E-Q1 (single port) and the TPS26744E-Q1 (dual port) PD controllers, which support up to 240W EPR and DisplayPort. However, they don't have an integrated power path, so they would still require a bunch of extra MOSFETs that the TPS65987D would not need. As of the time of writing, there is no direct replacement for the TPS65987D from TI.

From other vendors (specifically VIA Labs), there are comparable alternatives to the TPS65987D (VL103/VL105, some chips from Infineon). However, they are much less documented (no official reference designs, poor/unofficial documentation) and harder to procure (out of stock on LCSC). And they're not even cheaper really, so I didn't see much of a point in going with those over the TPS65987D.

All that said, the only main drawback to the TPS65987D is its NRND status; it fulfills all the requirements of this design, and plays nicely with the TUSB1064 and TPS55288.

## Description
The TPS65987D is a stand-alone USB Type-C PD controller with DisplayPort alt-mode support that detects cable orientation and negotiates PD through the USB-C CC pins. It communicates a power profile over I2C to an external boost/buck converter (TPS55288) and feeds power through its integrated power path. It supports 20V 5A PD as a USB-C PD source.

## Revision Progress

| Stages                               |   TPS65987D   |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-06 |
| Basic Function Review/Documentation  | ✅ 2026-08-07 |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |

## Relevant Docs
- [TPS65987D SPI Less Host Programming Over I2C](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/SPI_5F00_Less_5F00_EC_5F00_Based_5F00_Host_5F00_Programming_5F00_Over_5F00_I2C_5F00_slva972a.pdf)
- [TPS65987D Hardware Design Guide](https://www.ti.com/lit/an/slva888c/slva888c.pdf?ts=1785751478359)
- [TPS65987D Datasheet](https://www.ti.com/lit/ds/symlink/tps55288.pdf?ts=1785754959009)
- [TPS65987D PD Source Design](https://www.ti.com/tool/TIDA-050012)
## Design

### Power Path
The TPS65987D has an integrated power path, which means that the 20V 5A (or lower voltage/current) originating from the TPS55288 buck/boost converter can pass through the TPS65987D internally first before reaching the USB-C connector's VBUS pins. Alternatively, an external power path that bypasses the buck/boost converter can be used, which allows 20V to be delivered to the USB-C cable with minimal loss. However, this is only the case if the input supply is 20V (e.g., the TIDA-050012 Power Duo Source reference design), which it is not. So, the external power path is not used. The full power path is therefore as follows:

12V ATX PSU rail -> TPS55288 VIN -> TPS55288 VOUT -> TPS65987D PP_HV -> TPS65987D VBUS -> USB-C VBUS pin

Additionally, PP_HV1 and PP_HV2 are two technically separate power paths. However, in a self-powered dock design such as the LAZARUS-1 PCB, two separate paths are not necessary, so both are used for the same (up to) 20V 5A power path. In accordance with the design guide for systems configured as a source, each PP_HV path has a 10uF decoupling capacitor.

---
### VBUS Protection
Since the VBUS pin of the TPS65987D goes directly to the USB-C connector, which is prone to shorts or voltage surges whenever the USB-C cable is disconnected.

In accordance with the design guide, a TVS2200 TVS diode is placed between GND and VBUS, close to the VBUS pin of the USB-C connector. Furthermore, a 10kΩ resistor paired with a white LED are placed between VBUS and GND to indicate power being transferred. VBUS will vary depending on the voltage required by the system, so the LED will get brighter with higher voltage. However, even at 20V, the LED will not exceed ~2mA of current, which ensures that it won't experience accelerated burn out.

---
### Input Power Supply
> *Pin: VIN_3V3 (5)*

The TPS65987D itself needs its own +3.3V supply to function. In this design, this is sourced from the +3.3V rail of the ATX PSU (and not the +3.3VSB rail, since this chip does not need to be on when the system is shut off). Per the design guidelines, a 10uF decoupling capacitor is placed on this rail.

---
### Internal LDOs
> *Pins: LDO_3V3 (9), LDO_1V8 (35)*

These pins are internal LDO outputs. LDO_3V3 is intended for logic devices connected to the TPS65987D (such as an SPI flash chip or I2C pull up resistors), and LDO_1V8 powers internal digital circuitry. Per the design guide, a 4.7uF decoupling capacitor is placed close to the LDO_1V8 pin. Additionally, a 10uF decoupling capacitor is placed close to the LDO_3V3 pin, matching the EVM.

---
### SPI Flash Pins
> *Pins: SPI_PICO (36), SPI_POCI (37), SPI_CLK (38), SPI_CS (39)*

SPI Flash is not used in this design; instead, the TPS65987D is programmed over I2C by RP2354B_0. Per the datasheet, if unused, the SPI pins should be grounded, which is the configuration implemented in this design.

---
### Boot Configuration
> *Pin: ADCIN1 (6), SPI_POCI (37)*

ADCIN1 is connected to a resistor divider that sets the TPS65987D's boot configuration. Based on the resistor division value, along with the SPI_POCI configuration, the TPS65987D determines its default startup behaviour. This includes dead battery mode and regular device configurations.

Dead battery, in the case of the TPS65987D, simply refers to the state where the device with the PD controller has no power, but is connected to an active VBUS (e.g., laptop battery dead but VBUS providing power), and hence the VIN_3V3 rail is not yet active. This should never happen in this design, since it acts as the power source, not the sink. Moreover, whenever the TPS65987D boots up, there will always be power on the +3V3 rail. Thus, the dead battery mode configuration does not really matter for this application.

ADCIN1 also determines the boot configuration if an SPI flash device with configuration settings or an I2C interface is not found. The following are the configurations:

| Configuration   | Description (from the datasheet)                                                                                                                                                       |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Safe            | Ports disabled, if powered from VBUS operates a legacy sink                                                                                                                            |
| Infinite Wait   | Device infinitely waits in boot state for configuration information                                                                                                                    |
| Configuration 1 | DFP only (Internal Switch)<br>5 V at 3 A Source capability<br>TBT Alternate Modes not enabled<br>DisplayPort Alternate Mode not enabled (DFP_D, C/D/E)                                 |
| Configuration 2 | UFP only (Internal Switch)<br>5 V at 0.9 - 3.0 A Sink capability<br>TBT Alternate Modes not supported<br>DisplayPort Alternate Modes not supported                                     |
| Configuration 3 | UFP only (Internal Switch)<br>5-20 V at 0.9 - 3.0 A Sink capability<br>TBT Alternate Modes not supported<br>DisplayPort Alternate Modes not supported                                  |
| Configuration 4 | UFP only (External Switch)<br>5 V at 0.9-3.0 A Sink capability<br>5 V at 3.0 A Source capability<br>TBT Alternate Modes not supported<br>DisplayPort Alternate Modes not supported     |
| Configuration 5 | UFP only (External Switch))<br>5-20 V at 0.9-3.0 A Sink capability<br>5 V at 3.0 A Source capability<br>TBT Alternate Modes not supported<br>DisplayPort Alternate Modes not supported |

In an ideal case, this configuration never comes into action, because the RP2354B_0 *should* be providing the correct configuration over I2C. Nevertheless, if this doesn't happen, then the device should still act as a *source*, and not as a *sink*, since the PCB is not designed to take *in* power from VBUS. The only option in this table that supports that is Configuration 1, and thus that is chosen for this design.

> Note: technically Infinite Wait is still "safe", but it doesn't really bring any benefit over Config 1, since it just makes the TPS65987D do nothing.

The only boot mode pin strapping listed in the datasheet that supports Configuration 1 has dead battery mode set to `BP_NoResponse`, which states that the device does nothing unitl VIN_3V3 is present (i.e., the chip receives power, which it always should). Per the datasheet, this configuration requires:
- SPI_POCI grounded
- Resistor divider between 0.10 and 0.18

The safest resistor divider value is therefore 0.14, and R1=120kΩ, R2=20kΩ results in DIV=0.143, which is pretty close.
> Note: The datasheet and design guide both mention that tolerances of 1% are required, but the R2 selected has a 5% tolerance. This is likely still fine because the DIV still remains within the correct range with 5% tolerance.

---
### I2C Address
> *Pin: ADCIN2 (10)*

A resistor divider on ADCIN2 determines the I2C address of the TPS65987D. However, since each connected device on I2C is the only device on its bus, the I2C address does not really matter. Hence, the default address is chosen, which is `000b`. This requires a DIV range of 0.00 to 0.18, which can easily be achieved through a simple 100kΩ pull down resistor, as recommended by the design guide.

---
### Reset Pin
> *Pin: HRESET (44)*

The TPS65987D can be reset by pulling the HRESET pin high. This doesn't really need to be done, but just in case, a 0Ω resistor pull down is added. If reset functionality is ever needed, it can be replaced with a 100kΩ resistor, and the pin can be manually driven high.

---
### USB-C Configuration Channel Pins
> *Pins: C_CC1 (24), C_CC2 (26)*

The CC pins of the USB-C connector connect to the corresponding CC pins of the TPS65987D to allow the TPS65987D to negotiate and communicate cable orientation, device roles, and power/data modes with the connected laptop. Depending on the orientation, one of the CC pins gets converted to a VCONN pin, which provides 5V at up to 0.6A to the electronics internal to the connected cable if needed (e.g. for a Thunderbolt cable). This is a high speed connection, and decoupling capacitance is needed to ensure that it functions properly, Per the datasheet, the total capacitance on the CC lines needs to be 300pF, but there already exists ~100pF receiver capacitance. So, in accordance with the typical application schematic (and the EVM), both pins get a 220pF decoupling capacitor. This capacitor must be placed as close to the C_CC pins on the TPS65987D as possible.

---
### PP_Cable
> *Pin: PP_Cable (25)*

The PP_Cable pin on the TPS65987D is used as a power input, which is then fed to the VCONN output to power electronics within a connected USB-C cable (e.g., Thunderbolt controller). Prior to sending power through this pin to VCONN, the TPS65987D monitors the voltage; if it exceeds the safe voltage for that pin, it does not connect VCONN to PP_Cable. Otherwise, it does. The PP_Cable pin gets a 22uF decoupling capacitor in accordance with the datasheet and EVM, placed as close as possible to the PP_Cable pin.

---
### Battery Charger Detection and Advertisement
> *Pins: C_USB_P (50), C_USB_N (53)*

The TPS65987D supports BC1.2, which is a charging specification that allows up to 1.5A at 5V to be supplied to a connected device. Most laptops do not support this standard, as it is far too low power for most devices; it is primarily used in handheld devices. For this functionality to exist in this design, the USB 2.0 lanes of the USB-C connector must be routed to the TPS65987D to perform negotiation; however, the USB 2.0 lanes are already being routed to the USB7205C to be used for regular data transfer. So, BC1.2 is not supported in this design. 

Per the datasheet, when BC1.2 is not used, the C_USB pins are multiplexed as GPIO pins. The datasheet specifies that unused GPIO pins should be left floating, and thus the C_USB pins are left floating in this design.

---
### External Power Path
> *Pins: PP_EXT1 (48), PP_EXT2 (49)*

The TPS65987D supports an external power path, through two GPIO pins that control a series of MOSFETs that change the voltage that the boost/buck converter supplies. However, this power path is not used in this design, as a TPS55288 is used. The TPS55288 can be controlled entirely over I2C without GPIO control, so PP_EXT1 and PP_EXT2 are unused. In accordance with the datasheet, this pin is floated when unused.

---
### Drain Pins
The drain pins are connected to the drains of the internal power transistors for power path 1 and 2. They are *not* intended to be connected to ground, but *must* be connected to each other for thermal dissipation. There are two large drain pads on the QFN package, and this is to aid with thermal dissipation of the drain pins. All drain pins must be connected to their respective drain pads.

---
### HPD Pin
> *Pin: HPD (30)*

The HPD pin is used as a GPIO input pin that detects if a DisplayPort connection has been established, when the TPS65987D is used as a DisplayPort sink. It is connected to the PS176's DP_HPD output; whenever the PS176 signals a DisplayPort connection, the TPS65987D will read that through its HPD pin, and relay that signal to the connected laptop.