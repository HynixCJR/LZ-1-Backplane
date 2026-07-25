# PS176 DP to HDMI Subsystem
## Preamble
The PS176 is used in the pathway between the laptop and the IPKVM; it converts the DisplayPort signal (from the USB-C port, through DP Alt-mode) to HDMI, which is then converted by the LT6911C to MIPI CSI to be interpreted by the LicheeRV Nano SBC. DisplayPort to MIPI CSI ICs do exist, and would theoretically use significantly less board space and consume slightly less power; however, these ICs would require substantial software configuration. The LT6911C is used in the official NanoKVM, so the same device tree and firmware can be used, whereas chips like the ITE IT6510 or LT7911D would require custom firmware (that is not publicly available). Hence, the PS176 is required as an additional step to convert the DisplayPort to HDMI.

This specific chip was chosen for the following reasons:
1. There is already a pre-existing open source design by lemon_wifi on [OSHWHub](https://oshwhub.com/lemon_wifi/PS176), which does not require significant modification to work in this embedded system.
2. Unlike the TI SN65DP159, which is a passive retimer that requires dual-mode DisplayPort (DP++), the PS176 is an active chip that works with any native DisplayPort port. This is important because USB-C DP Alt-mode generally does not support dual mode operation, and hence the SN65DP159 would not function in this case. This is rather unfortunate because TI's documentation and openness is unmatched by any of the other chips contending for use in this step.
3. The PS176 is rather cheap; it is available for <$2 CAD + shipping on Aliexpress, and does not require any expensive external components.
4. Despite the PS196 being newer and more advanced (supporting higher resolutions, using less power), the PS176 was still chosen because it is more purchasable in individual quantities. Additionally, the PS176 uses a smaller footprint.

## Description
The [PS176](https://github.com/HynixCJR/serverv2_backplane/blob/main/datasheets/PS176_DP_to_HDMI_System/PS176_DP_to_HDMI_Datasheet.pdf) is a native DisplayPort 1.2a to HDMI 2.0 converter IC that does not rely on DP++ support. In this backplane PCB, it's used to convert the DP signal from the TUSB1064 switch (and thus from the upstream USB-C port, connected to the laptop) to a native HDMI signal, which is then converted to a CSI to be used as an input to the Lichee RV Nano for IPKVM purposes.

This design is largely based on the [reference design](https://github.com/HynixCJR/serverv2_backplane/blob/main/datasheets/PS176_DP_to_HDMI_System/PS176_Reference_Schematic.pdf), which is an open source design created by [lemon_wifi on OSHWHUB](https://oshwhub.com/lemon_wifi/PS176). However, changes were made to suit the embedded design (i.e., no ports) of this subsystem.

## Revision Progress

| Stages                               |    PS176     |   MCP1602    |
| ------------------------------------ | :----------: | :----------: |
| Initial Design                       | ✅ 2026-05-02 | ✅ 2026-07-21 |
| Basic Function Review/Documentation  | ✅ 2026-07-21 | ✅ 2026-07-21 |
| Extended Design Review/Documentation |              |              |
| Initial PCB layout                   |              |              |

## Design

### Power
The PS176 uses three voltage rails: 5V, 3.3V, and 1.2V. However, it draws most of its current (per the datasheet) from the 1.2V rail. Since this system is embedded onto the backplane PCB, no additional power connectors are needed for the 3.3V rail or 5V rail; the PS176 can simply draw from the main 3.3V or 5V ATX PSU rails. However, 1.2V is supplied using a simple 3.3V->1.2V buck converter. 5V is only used for HDMI I2C pull up voltages.

To supply 1.2V, the `MCP1602-120I_MF`, which is a fixed 1.2V output variant of the [MCP1602](https://github.com/HynixCJR/serverv2_backplane/blob/main/datasheets/PS176_DP_to_HDMI_System/MCP1602_Buck_Converter.pdf), steps down the 3.3V rail to 1.2V. The circuit implementation is essentially unchanged from Figure 6-3 in its datasheet, since the total current consumption of the PS176 is ~350mA @ 1.2V, which is less than the design's 1.2V @ 500mA spec. The PG pin is pulled up to 3.3V by a 10k resistor, but isn't tied to any MCU GPIO pin to make routing easier. To ensure that the buck converter is only active when the PS176 is in use, the SHDN# pin is tied to pin 37 (VDD12_ON) of the PS176.

In accordance with the reference design, each (pair of) voltage input pins on the PS176 has a 330Ω@100MHz ferrite bead in series. This is used to further filter high frequency noise. 

In accordance with the reference design, all voltage rails (including those outputted by the PS176 itself) have bypass capacitors to filter noise.

---
### DP Input Pins
DisplayPort uses 4 differential data transfer lanes (DPx+ and DPx-), 1 bidirectional differential AUX lane for config/EDID/DPCD communication (AUX+ and AUX-), 1 single HPD signal to signal connection (DP_HPD), and GND/3.3V pins. Since the subsystem is embedded, the GND and 3.3V pins are supplied by the main ATX PSU voltage rails.

Per the DisplayPort specification, 100nF capacitors are required in series on each differential data transfer wire (DPx, AUX) for AC coupling. As they are included in the TUSB1064 subsystem, they are not needed in the PS176 subsystem.

Pull up resistors are included, per the reference design, on the AUX and HPD wires. However, since the 100nF capacitors are included in the TUSB1064 subsystem, the 1M pull down/pull up resistors on AUX+ and AUX- respectively are also included in that subsystem, and are thus not represented on the PS176 schematic.

A 1kΩ resistor is included in series on the DP_HPD pin for power sequencing protection, in accordance with the reference design. If this is not needed, or if the resistor value is incorrect, it can be swapped for a 0Ω or other resistance value, as the HPD pin is not high speed.

---
### HDMI Output Pins
HDMI uses 3 TMDS data lanes (HDMI_xP and HDMI_xN), 1 TMDS clock lane (HDMI_CP and HDMI_CN), 1 CEC pin for control (CEC), 1 HPD pin to signal connection (HDMI_HPD), 1 I2C line (HDMI_SCL and HDMI_SDA), and 5V/GND pins. Since the subsystem is embedded, the GND and 5V pins are supplied by the main ATX PSU voltage rails. However 2kΩ pull up resistors (to 5V) on the I2C line are still required per the HDMI specification. This is paired with a 33kΩ pull up resistor in the LT6911C subsystem, which receives the HDMI output of the PS176.

The TMDS data lanes do not require additional components, such as clamps/diodes or other ESD protection, as forfeiting the physical HDMI port makes them largely unnecessary. The reference design only includes diodes on the 5V line; however, they are excluded from this design since there is no physical HDMI port.

The CEC pin is not used by the LT6911C, and so it is left floating.

---
### Control I2C
> *Pins: CSCL (29), CSDA (28), I2C_ADDR (3)*

These pins are for the control I2C slave line, which is used for debugging. The pins are pulled up to 3.3V by a 4.7k pull up resistor, with no further connection to an MCU to simplify routing (they aren't necessary for functionality). Pads may be included on these traces for debugging purposes.

The I2C_ADDR pin is pulled high by a 4.7kΩ resistor to 3.3V, which sets the I2C address of the CSCL and CSDA line to `90h – 9Fh, D0h – DFh`, per the datasheet.

---
### Crystal Oscillator
> *Pins: XTLI (26), XTLO (25)*

A 27MHz crystal oscillator is used in this subsystem to control timing. The datasheet does not mention what frequency or other specifications are required for the crystal, so this design decision is based on the reference design. Below is a comparison table of the oscillator used in this design vs. the one used in the reference design.

| LCSC Part Number | Used by:                | Load Capacitance | Frequency Stability | Frequency Tolerance | ESR |
| ---------------- | ----------------------- | ---------------- | ------------------- | ------------------- | --- |
| C156249          | Reference design        | 8pF              | ±30ppm              | ±20ppm              | 50Ω |
| C37635384        | LAZARUS-1 Backplane PCB | 9pF              | ±10ppm              | ±10ppm              | 30Ω |

For frequency stability, frequency tolerance, and ESR, lower values are generally better. the oscillator used in this design is therefore a good choice. However, the load capacitance is not the same, and so different capacitor values are used.

The reference design also omits the usual 1MΩ resistor between the oscillator pins, though the datasheet does not mention anything about internal resistance between the two pins. So, a 1MΩ resistor footprint is added, but labelled as Do Not Populate (DNP).

> Note: the reference design uses 15pF capacitors, which seems to imply that there is only ~0.5pF stray board capacitance. This seems too low, so 10pF capacitors are used in this design, which nets a stray board capacitance of 4pF.

---
### AUXDCx
> *Pins: AUXDCP (32), AUXDCN (31)*

These two pins are labelled as "DP source detection" in the datasheet, with no further elaboration. The reference design simply pulls up AUXDCN to 3.3V and pulls down AUXDCP to GND through 100k resistors, with no further connection, and thus this design does the same.

---
### PDB
> *Pin: PDB (4)*

Active low power down pin for the PS176. It is pulled up to 3.3V by a 10k resistor and connected to RP2350B_2 GPIO to allow the user to disable the PS176 in software to ensure lower power consumption, though the PS176 only consumes 70uA of current in Auto Power Down mode. In the reference design, it is not connected to an MCU.

---
### Additional Pins
> *Pins: REXT (36), RESETB (35), GPIO3 (10)

- REXT: Pulled down to GND (per datasheet) by 5.1k resistor with no further connection.
- RESETB: Active low reset, pulled up to 3.3V by 10k resistor to prevent reset with 1uF bypass capacitor to avoid noise causing PS176 to reset. 
- GPIO3: Has an internal pull-up at ~80k, but reference design has it pulled *down* by a 4.7k resistor. The datasheet does not mention if this pin is particularly notable, and the reference design does not explain why it's pulled down, but the pull down resistor is kept regardless. Can be desoldered if necessary.

---
### Disconnected Pins
> *Pins: TESTMODEB (2), GPIO1 (5), GPIO4 (12), GPIO2 (27)*

- TESTMODEB: "Test mode control, NC for normal operation" per datasheet, hence the pin is left floating in the design.
- GPIO1, GPIO2, GPIO4: Has internal pull-ups at ~80k, and reference design floats these pins because they are not used, so they are floating in this design too.