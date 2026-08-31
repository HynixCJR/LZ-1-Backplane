# PAC1954 Current Monitor Subsystem
## Preamble
LAZARUS-1 is designed to be a power efficient and power conscious server system. Part of being power conscious is actually knowing *how much* power the entire system and its subcomponents are drawing at any given time. Placing power monitors on all major subsystems is especially important because it allows for far greater granularity in the telemetry of the system; unlike conventional means of measuring power (i.e., a simple power meter between a wall outlet and the server), this setup enables the user to identify which specific components are drawing the most current, which can inform them of possible inefficiencies in their setup. For example, if IPKVM functionality is not needed, this monitoring setup can provide simple metrics on how much power is being wasted for that component, and thereby how much power can be saved by disabling it.

There are several ways of monitoring power, such as by measuring the voltage drop across a shunt resistor, by using a hall effect sensor, and by using a current transformer. The shunt resistor design is inherently wasteful, as it forces the resistor to dissipate power as heat when stepping down the voltage. However, it is significantly more accurate that any other method, while being less bulky and costly. Moreover, the wasted power can be minimized by using smaller current sense resistors (and thus, current monitors that support this functionality).

The PAC1954 was mainly chosen for this purpose because:
1. It is a four channel shunt resistor voltage/current monitor, meaning fewer ICs are actually required for power monitoring.
2. It can technically support smaller current sense resistor values than calculated, at the expense of resolution and higher error - for high current rails, the lower dissipated power is more important than this downside.
3. It performs power calculations and accumulation automatically, and sends this pre-calculated value over I2C, which is nice since this device interfaces with the LicheeRV Nano directly (thus requiring less programming on the LicheeRV Nano).
4. It's a Microchip product, so I can source it for free from Microchip's free sample program. <3

## Description
The PAC1954 is a four-channel current-sense and voltage monitor IC from Microchip that outputs over I2C. It performs power calculations automatically, and accumulates values to calculate a rolling average. It comes in a small 3x3mm VQFN package, and requires external current sense resistors to function. The PAC1954-1 variant can only measure high-side power (between voltage source and load), while the PAC1954-2 can also measure low-side (between load and GND). For this application, only high-side is used, and so either variant is useable.


## Revision Progress

| Stages                               | PAC1954_PSU_PD | PAC1954_FANS | PAC1954_IPKVM | PAC1954_HUB  |
| ------------------------------------ | :------------: | ------------ | ------------- | ------------ |
| Initial Design                       |  ✅ 2026-07-10  | ✅ 2026-07-12 | ✅ 2026-07-11  | ✅ 2026-07-12 |
| Basic Function Review/Documentation  |  ✅ 2026-08-25  | ✅ 2026-08-19 | ✅ 2026-08-30  |              |
| Extended Design Review/Documentation |                |              |               |              |
| Initial PCB layout                   |                |              |               |              |

## Design

### Input Power
The PAC1954 can operate with an input supply of +2.7V to +5V. For the LAZARUS-1 PCB, +3.3V is chosen for this subsystem because it lands comfortably in the middle of that range, and can be easily supplied by the ATX PSU +3.3V rail. Per the [PAC1954 Click reference design schematic](https://download.mikroe.com/documents/add-on-boards/click/pac1954_click/pac1954-click-schematic-v100.pdf), a 4.7uF and 100nF decoupling capacitor are placed near the VDD pin to filter noise.

### SLOW/ALERT1 Pin
> *Pin: SLOW/ALERT (1)*

By default, if Pin 1 is forced high, the PAC1954 enters slow sampling mode, where it only samples the current 8 times per second. Otherwise, if it's pulled low, it samples at 1024 samples per second. This pin can also be programmed as ALERT1, which is a programmable GPIO output pin. ALERT1 is not really necessary, since there are already pre-existing functions for each subsystem to prevent overcurrent where necessary; the system will only gather telemetry through polling over I2C.

Slow mode is used in this design because the fast sampling rate is simply not necessary; the power monitoring is not tied to any critical system functions, and so very brief (<1/8th second) transients aren't that important to capture. Moreover, slow mode consumes 3% the typical current of default mode. This amounts to a mere 1.26mW power savings per PAC1954, which is basically nothing in the grand scheme of things, but is still somewhat meaningful (in spirit!). It also brings the typical power consumption down to a measly 0.0396mW, which is kinda cool.

### I2C Pins
> *Pins: SCL (4), SDA (5), ADDRSEL (6)*

The four PAC1954's on the LAZARUS-1 PCB are connected to the LicheeRV Nano's I2C1 interface, along with the MCP9808 temperature sensor, as I2C slaves. This is just a standard I2C interface, and so 49.9kΩ pull up resistors are added for every PAC1954 on the PCB. This amounts to a total effective resistance of 12.5kΩ, which is a relatively standard resistance.

The slaves addresses of the PAC1954's must be adjusted to ensure that multiple PAC1954's don't interfere with each other over I2C. Luckily, there are 16 possible slave addresses that can be chosen from, and they can be chosen through a pull down resistor between the ADDRSEL pin and GND. Below are the addresses and pull down resistor values chosen for this design:

|          | PAC1954_PSU_PD   | PAC1954_FANS     | PAC1954_IPKVM    | PAC1954_HUB      |
| -------- | ---------------- | ---------------- | ---------------- | ---------------- |
| Resistor | Tied to GND      | Tied to +3.3V    | 499Ω ± 1%        | 806Ω ± 1%        |
| Address  | `0010 000 (R/W)` | `0011 111 (R/W)` | `0010 001 (R/W)` | `0010 010 (R/W)` |

This shouldn't collide with the single MCP9808, which has an I2C address of `0011000`. PAC1954_PSU_PD is tied to GND, and PAC1954_FANS to +3.3V, to save space on the PCB.

### PWRDN# 
> *Pin: PWRDN# (16)*

The PWRDN# pin is an active low disable (or alternatively, an active high enable). The PAC1954 barely consumes any power, and shuts off along with the PSU's +3.3V rail, so there isn't really a reason to tie this to any GPIO pin of an MCU. So, it is simply permanently pulled high by a 10kΩ resistor.

### GPIO/ALERT2 Pin
> *Pin: GPIO/ALERT2 (15)*

The PAC1954 has a GPIO input or ALERT output pin on pin 16, which can be programmed over I2C. However, as detailed in [SLOW/ALERT1 Pin](#slow/alert1-pin) description, additional GPIO is not needed for this application, so it is simply tied to GND through a 10kΩ resistor.

### SENSE Pins and Current Sense Resistors
> *Pins: SENSEx+, SENSEx-*

On the PAC1954, there are four current/voltage sense channels, which equates to eight SENSE pins (four `+`, four `-`). In a high-side configuration, which is used in this design, the `+` pin is connected directly to the input supply, the `-` pin is connected to the load, and a current sense resistor bridges the `+` and `-` pins together.

The value of the current sense resistor can be calculated by:
```
R_SENSE = FSR / I_MAX
```

...where `I_MAX` is the maximum current drawn by the subsystem, and `FSR` is 100mV.
> Note: `FSR` is set to 100mV unidirectional by default, and that is used on the LAZARUS-1 PCB.

However, `I_MAX` for certain subsystems may be far greater than what is typically drawn; for example, `I_MAX` for the +12V, +5V, and +3.3V rails is calculated for the absolute worst-case possible scenario, where USB-C PD is sustained at 100W, all 12 SATA ports are connected to HDDs that are actively being spun up, and all other subsystems are completely maxxed out. Realistically this will never happen, but `I_MAX` is still used, as a lower `I_MAX` would result in a larger current sense resistor (and thereby higher power dissipation). Moreover, it is still safe; the only downside would be lower precision, but with 16 total bits the actual precision still remains good enough for this application. For example, for the worst case scenario for the +12V rail (32A), the measurement is still precise down to 0.5mA (or 5.9mW). This is largely negligible for basic telemetry.

The specific subsystems monitored by the PAC1954's, and which PAC1954 they are monitored by, are detailed in the table below.

| PAC1954 number | Subsystem/voltage | Max current | Typical Current | Sense Resistor | Power wasted (typ) |
| -------------- | ----------------- | ----------- | --------------- | -------------- | ------------------ |
| 0              | Fans/+12V         | 500mA       | ~50mA           | 200mΩ ±1%      | ~0.5mW             |
| 0              | PSU/+5V           | 40A         | ~4.8A           | 5mΩ ±5%        | ~24mW              |
| 0              | PSU/+12V          | 20A         | ~8A             | 2.5mΩ ±1%      | ~20mW              |
| 0              | PSU/+3V3          | 1.47A       | ~0.5A           | 68mΩ ±1%       | ~34mW              |
| 1              | PS176/+3V3        | 196mA       | 30uA            | 510mΩ ±5%      | ~15.3uW            |
| 1              | LT6911C/+3V3      | 196mA       | 196mA           | 510mΩ ±5%      | ~100mW             |
| 1              | Display/+3V3      | 47mA        | 24mA            | 2Ω ±1%         | ~48mW              |
| 1              | LicheeRV Nano/+5V | 1.1A        | 200mA           | 90mΩ ±1%       | ~18mW              |
| 2              |                   |             |                 |                |                    |
| 2              |                   |             |                 |                |                    |
| 2              |                   |             |                 |                |                    |
| 2              |                   |             |                 |                |                    |
| 3              | Fans/+12V         | 500mA       | ~50mA           | 200mΩ ±1%      | ~0.5mW             |
| 3              | Fans/+12V         | 500mA       | ~50mA           | 200mΩ ±1%      | ~0.5mW             |
| 3              | Fans/+12V         | 500mA       | ~50mA           | 200mΩ ±1%      | ~0.5mW             |
| 3              | Fans/+12V         | 500mA       | ~50mA           | 200mΩ ±1%      | ~0.5mW             |

> *Note: 0 = PAC1954_PSU_PD, 1 = PAC1954_IPKVM, 2 = PAC1954_HUB, 3 = PAC1954_FANS*

#### Subsystem Current Calculations
##### 1. Global +12V rail:
- `(12 HDDs × 2.0A) + 9.2A (PD) + (5 fans × 0.5A) = 35.7A`
- With 10% safety margin: `35.7A * 1.10 = ~39.27A`
- Sense resistor: `100mV / 39.27A = ~2.5mΩ`
- Actual max current: **~40A**
- Realistic typical current (active use, 12 HDDs, 50W laptop): `(12 HDDs × 0.25A) + 4.2A (PD) + (5 fans × 0.16A) = 8A`
##### 2. Global +5V rail:
- `(12 HDDs × 1.0A) + 0.6A (PD CTRL) + 3 × 1.5A (Panel) = 17.1A`
- With 10% safety margin: `17.1A × 1.10 = ~18.81A`
- Sense resistor: `100mV / 18.81A = ~5mΩ`
- Actual max current: **~20A**
- Realistic typical current (active use, 12 HDDs, no panel use, no active PD cable): `12 HDDs × 0.4A = 4.8A`

##### 3. Global +3V3 rail:
- `0.008A (PD CTRL) + (3 flash × 0.025A) + (3 RP2354 × 0.025A) + 0.18A (MUX) + 0.2A (HUB) + 0.15A (SD) + 0.173A (PS176) + 0.188A (LT6911C) + 0.3A (DISP) = 1.349A`
- With 10% safety margin: `1.349A × 1.10 = ~1.48A`
- Sense resistor: `100mV / 1.48A = ~68mΩ`
- Actual max current: **1.47A**
- Realistic typical current (active use, display off, IPKVM off): ~0.5A

##### 4. PS176
- Per datasheet, at HDMI output 5.94Gbps, there is a normal supply current of `18.5mA` at `+3.3V`, and `432.2mA` at `1.2V`.
- This system uses an MCP1602 buck converter, which has ~80% efficiency with `432.2mA` drawn at `1.2V` output.
- So, total current is: `1.2 × 432.2mA × 1.2V / 3.3V + 18.5mA = 144.2mA`
- With 10% margin, that comes out to `144.2mA × 1.10 = 158.62mA`
- Sense resistor: `100mV / 158.62mA = ~625mΩ`
- But `510mΩ` is much cheaper! So we get actual max current: **196mA**
- When shut down by RP2354, current drawn is `30uA`

##### 4. LT6911C
- Per datasheet, at 1080p 60Hz, the LT6911C draws: `56mA` at `+3.3V`, and `306mA` at `+1.2V`.
- This subsystem uses the same MCP1602 as the PS176, so assuming 80% efficiency, the total current drawn is `1.2 × 306mA × 1.2V / 3.3V + 56mA = 189.5mA`
- With 10% margin: `189.5 × 1.10 = 208.5mA`
- Sense resistor: `100mV / 208.5mA = ~480mΩ`
- But `510mΩ` is already being used, so we get actual max current: **196mA**
- The system does not have a power down mode specified in the datasheet, so assume that max current draw is equal to the typical current draw.

