# MCP9808 Temperature Sensor Subsystem
## Preamble
A simple temperature sensor is helpful to include on the board to track chassis temperatures during operation. This can help inform the user if the chassis is overheating, which is important because the LAZARUS-1 PCB is designed to supply up to 100W to the laptop and up to ~120W to HDDs. The MCP9808 is a good choice for this mainly because it is very easy to source (thanks Microchip!), communicates over a simple I2C interface, has a small DFN package, and requires very few external components to function. In fact, this design literally only uses one bypass capacitor; it doesn't even need pull up resistors on the I2C traces because it shares an I2C bus with the PAC1954 current monitors, which each have their own pull ups.

## Description
The MCP9808 is a digital temperature sensor. It reads temperatures from -40°C to 100°C with a typical accuracy of just ±0.25°C, and outputs the temperature readings digitally over I2C. It consumes very little current during operation (200uA typical), and operates on +2.7V to +5.5V.

## Revision Progress

| Stages                               |   MCP9808   |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-09 |
| Basic Function Review/Documentation  | ✅ 2026-08-16 |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |

## Design

### Power
> *Pin: VDD (8)*

The VDD pin takes in any voltage input from +2.7V to +5.5V, with no typical or recommended value specified in the datasheet. So, this design uses the +3.3V rail from the ATX PSU; this fits comfortably within that range. Per the datasheet, a 100nF bypass capacitor is placed on this pin.

### I2C Interface
> *Pins: SDA (1), SCL (2), A0 (7), A1 (6), A2 (5)*

The MCP9808 communicates directly to the LicheeRV Nano through its I2C1 interface as a slave device. The I2C1 channel is shared between the MCP9808 temperature sensor and the PAC1954 current monitors. This presents a few slight complications.
1. Pull up resistors: SDA and SCL pins for the PAC1954 all have 49.9kΩ pull up resistors to enable functionality. This approach is used over a single pull up system because the sensors are placed all over the board, and not close to each other, causing the trace length to be quite long. Since there are four PAC1954's on the board, the total effective resistance is 12.5kΩ, which leads to 264uA current being drawn for logic. This can lead to self-heating, though the datasheet mentions that at 500uA max current draw, the self heating is only +0.2°C for the DFN package. This is fairly negligible for the purposes of the LAZARUS-1 PCB.
2. I2C slave addresses: Since there are already four other slaves devices (PAC1954) on the same I2C channel, the I2C address of the MCP9808 must not collide with any of the other devices. Luckily, the address can be set by the A0, A1, and A2 pins; when they are all grounded, the address is `0011000` or `0x18`. This will almost certainly not collide with any of the PAC1954's, as their addresses are all `0010xxx`.

### ALERT Pin
> *Pin: Alert (3)*

The MCP9808 has an open-drain temperature alert pin to signal when the temperature sensed reaches or surpasses a user-programmable limit. This is not used for the LAZARUS-1 PCB, as this subsystem is only intended for basic telemetry. So, this pin is floated.