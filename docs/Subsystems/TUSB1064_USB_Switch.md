# TUSB1064 USB Switch Subsystem

# Description
The TUSB1064 is a USB-C redriving switch supporting up to 10Gbps data rates and DP 1.4. In other words, it connects to the TX and RX pins of the upstream USB-C port, and flips them depending on the orientation of the USB-C cable, as controlled by the TPS65987D PD controller over I2C. This ensures that the devices further down the USB data and DP paths do not need to account for orientation.

# Revision Progress

| Stages                               |    TUSB1064     |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-09 |
| Basic Function Review/Documentation  | ✅ 2026-07-22 |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |

# Design

### Power
The power circuitry for the TUSB1064 is pretty simple; it only uses 3.3V to power itself and for all the logic. So, the 3.3V ATX PSU rail is used, with the appropriate bypass capacitors (per the datasheet) included. One 100nF capacitor is included for each of the three VCC pins.

---
### TX Input Pins
The USB-C port routes transmit (TX) traces to the TUSB1064. Per the USB specification, the TX traces should have an AC coupling capacitor of 75nF to 265nF. 100nF is the recommended value on the TX traces, per the TUSB1064's hardware design checklist, but 220nF still falls within the specification, and is more commonly used on newer USB redriver and switch ICs (e.g., [TUSB1104](https://www.ti.com/lit/ds/symlink/tusb1104.pdf?ts=1784735179859)). So, 220nF AC coupling capacitors are placed on all TX traces in this design.
> Note that per the USB 3.2 specification, the polarity of the TX traces can be reversed in the PCB design without issue, as this is automatically corrected.

---
### RX Input Pins
The USB-C port routes receive (RX) traces to the TUSB1064. Per the USB specification, the RX traces do not *need* coupling capacitors, as they are supposed to already be there on the TX traces of the connected device. However, they can be optionally added on the RX side, per a [revision to the USB 3.1 Specification](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/138/USB-3.1-ECN-Rx-AC-Coupling-Capacitor-Option.pdf). Since the tolerances are generally quite large on ceramic  capacitors (±20%), it's safer to use a 470nF capacitor over 330nF; if the TX side uses 100nF and the RX side uses 330nF, the net coupling capacitance is just 76.7nF, which is very close to the minimum.
> Note that per the USB 3.2 specification, the polarity of the RX traces can be reversed in the PCB design without issue, as this is automatically corrected.

---
### EQ Configuration Pins
> *Pins: CTL1 (23), EQ0 (11), EQ1 (14), SSEQ0 (38), SSEQ1 (3), DPEQ0 (35), DPEQ1 (2)*

The TUSB1064 can apply equalization to the signal traces to reverse attenuation and improve signal integrity. To configure the equalization applied, several pins can be used, *or* the TUSB1064 can be configured over I2C. In this design, the TUSB1064 uses I2C to communicate with the TPS65987D PD controller, and hence I2C is used to configure EQ. According to the datasheet:
> the configuration pin CTL1 and all of the equalization pins (EQ[1:0], SSEQ[1:0], and DPEQ[1:0]) can be left unconnected. If these pins are left unconnected, the TUSB1064 7-bit I2C slave address will be 0x12 because both DPEQ/A1 and SSEQ0/A0 will be at pin level "F". If a different I2C slave address is desired, DPEQ/A1 and SSEQ0/A0 pins should be set to a level which produces the desired I2C slave address.

Floating DPEQ0 and SSEQ0 is likely safe, however grounding both pins does not use significantly more board space since there is a dedicated ground plane, and grounding the pins may possibly be slightly safer, so they are grounded in this design. This leads to a slave I2C address of 0x88 (write) and 0x89 (read) for the TUSB1064. This will not interfere with any other I2C devices, since the TPS65987D's third I2C line is dedicated solely to the TUSB1064.

The rest of the EQ configuration pins are left floating, as they do not control anything if I2C is used for EQ.

---
### Hot Plug Detect Input (HPDIN) Pin
> *Pin: HPDIN (32)*

HPDIN is an input that is high when a DisplayPort sink (e.g., monitor) is connected. Per the datasheet, when HPDIN is low for ≥2ms, all DisplayPort lanes are disabled. This pin connects to the HPDIN pin of the TPS65987D and is controlled by the HPD output pin of the PS176.

A 100k pull down is added on the HPD trace to ensure that the default state of the HPD line is no monitor connected.

---
### DisplayPort Output Pins
DisplayPort consists of four differential data pairs, as well as a single AUX differential pair communication between devices. The DisplayPort specification requires 100nF AC coupling capacitors placed close to the transmitter side, and since they aren't included in the PS176 subsystem, they are included in this system.

---
### USB 3.2 Gen 2 Output Pins
> *Pins: SSRX+ (5), SSRX- (4), SSTX+ (8), SSTX- (7)*

The USB 3.2 specification requires AC coupling of 75nF to 265nF on the transmit side (TX); however, this is an embedded system without external ports, and the USB 3.2 output pins go directly to the USB7206C USB hub, and so the AC coupling capacitors in this design are also placed on the RX channel. Thus, each trace gets its own coupling capacitor. The capacitor used on these traces are 220nF capacitors, which fit comfortably in the specification. 100nF capacitors are used in the datasheet; however, 220nF is still safe, and more modern USB-C redrivers tend to recommend 220nF over 100nF.

---
### I2C Pins
> *Pins: CTL0/SDA (22), FLIP/SCL (21)*

I2C is used on the TUSB1064 to configure equalization and communicate USB-C cable orientation. In this system, the TUSB1064 is connected to the TPS65987D's third I2C bus, and is the only device on this bus. Since it is the only device on the bus, 10kΩ pull up resistors are used.

---
### SBU Pins
> Pins: SBU1 (24), SBU2 (25)

The SBU pins on the USB-C connector connect directly to the SBU pins of the TUSB1064. Per the USB-C specification, the SBU pins are used for alternate modes (such as DP alt mode, as in this system) or auxiliary communication (i.e., audio). In accordance with the datasheet, 2MΩ pull down resistors are attached to both SBU traces.

---
### AUX Pins
> *Pins: AUX+ (26), AUX- (27)*

These pins are bidirectional pins for DisplayPort, used to communicate device config and link management. As mandated by the TUSB1064 datasheet a 1MΩ pull down resistor is placed on AUX-, and a 1MΩ pull up resistor is placed on AUX+. Also mandated by the datasheet is a 100nF AC coupling capacitor, which is placed on both traces. On the side of the capacitors facing the PS176, 1kΩ pull up resistors are included in the PS176 subsystem.

