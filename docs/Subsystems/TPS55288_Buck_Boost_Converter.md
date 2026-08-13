# TPS55288 Buck Boost Converter Subsystem
## Preamble
The TPS65987D controls an external buck/boost converter to provide up to 5A @ 20V to the VBUS rail of the USB-C connector. In the TI's reference TPS65987D designs, an LM3489 buck controller is paired with a series of MOSFETs that adjust the resistance values to provide this power; however, this uses a significant amount of PCB space. A solution who's output voltage is controlled over I2C uses far fewer external components.

The TPS55288 was chosen mainly because it can be controlled over I2C, and has a relatively detailed official software configuration guide published by TI themselves that integrates the TPS55288 with the TPS65987D. This makes setup easier, while also reserving PCB space for other subsystems.

The TPS55288 also achieves mid-to-high 90% efficiencies at all output voltages, which is ideal for a home server application, where power usage is of high concern. It is by far the most efficient buck converter used on the entire board.

## Description
The TPS55288 is a four-switch buck-boost converter that can output 0.8V to 22V from a 2.7V to 36V supply input with up to 97% efficiency (with 12V input to 20V 3A output). It supports up to 6.35A output in 50mV increments. The output voltage can be configured over I2C, allowing the TPS55288 to be used for USB-C PD applications. It comes in a tiny 4x3.5mm QFN package, and is readily available on LCSC for only $2.79 USD.

## Revision Progress

| Stages                               |   RP2354B    |
| ------------------------------------ | :----------: |
| Initial Design                       | ✅ 2026-07-06 |
| Basic Function Review/Documentation  |              |
| Extended Design Review/Documentation |              |
| Initial PCB layout                   |              |
## Relevant Docs
- [USB-C PD Source with TPS65987D and TPS55288](https://www.ti.com/lit/ab/slvaeq7/slvaeq7.pdf?ts=1786370541378)
- [TPS55288 Datasheet](https://www.ti.com/lit/ds/symlink/tps55288.pdf)
- [TPS55288 EVM](https://www.ti.com/lit/ug/slvubo4b/slvubo4b.pdf)
# Design
This design is largely based on the TPS55288 EVM and datasheet.

### Power path
The overall power path of the TPS65987D and TPS55288 is as follows:
- Setting power profile: TPS65987D I2C master -> TPS55288 I2C slave
- Power path: `+12V` ATX PSU rail -> TPS55288 `V_IN` pin -> TPS55288 `V_OUT` pin -> TPS65987D `PP_HV1` and `PP_HV2` pins -> TPS65987D VBUS pin -> VBUS pin of USB-C port

In essence, the TPS65987D communicates to the TPS55288 over I2C to control its voltage output, and then the TPS55288 converts the 12V from the ATX PSU rail to whatever voltage is needed for USB-C PD, and outputs that back to the TPS65987D's internal power path, which is connected to the VBUS pin of the UBS-C port.

### Gate Drivers

### Output Current Limit Pin
> *Pin: ISP (12), ISN (13)*

The TPS55288 uses the ISP and ISN pins to sense current through a current sense resistor; when the voltage across the current sense resistor exceeds the rated maximum (specified in a register in software), a slow constant current control loop between ISP and ISN regulates the voltage between the two pins, thus clamping the current. The value of the current sense resistor determines the current at which overcurrent protection is tripped, and this value is calculated by: `R_SNS = V_SNS / I_OUT_LIM`

Per the datasheet, `V_SNS` is 50mV by default, and so for `I_OUT_LIM` to be 5A, `R_SNS` must be 10mΩ. This ensures that the current does not surpass the 5A PD specification. Tolerances in the current sense resistor could lead to the actual current being lower than 5A, but this is an average inductor current limit, and so transient spikes may not necessarily trip the OCP. Furthermore, the downstream TPS65987D is limited to 5A per its datasheet, and so a lower current sense resistor value is not used; slightly lower sustained current than 5A is still acceptable for most applications.

The datasheet also mentions that the current sense resistor mentioned should be rated for the power dissipation expected across it. In this case, with an inductor voltage of 50mV and a max current of 5A, the maximum power dissipated is 250mW. The resistor chosen is rated for 1W, and is therefore well within specification.

An additional 100nF capacitor is placed between the two pins to filter noise.

### V_IN Pin
> *Pin: VIN (3)*

The V_IN pin takes in an input voltage between 2.7V and 36V; however, for this application, VIN=12V is used to match the ATX PSU main supply rail. Substantial filtering is applied to this pin using bypass capacitors; in accordance with the EVM, a 1uF capacitor is placed close to the pin itself, with an additional 1uF, 2 x 10uF, and 68uF placed nearby.

All capacitors chosen on this line are rated for 25V or higher.

### EN/UVLO Pin
> *Pin: EN/UVLO (4)*

The EN/UVLO pin enables the function of the TPS55288; logic high enables the device, whereas logic low disables it and turns it into shutdown mode. The pin (enable) reads high at 1.15V, but the UVLO (minimum voltage before it shuts down the device) is 1.20V to 1.26V, with 1.23V typical. This is achieved through a resistor divider between V_IN and GND; when V_IN reaches undervoltage, the resistor divider should trigger this pin and disable the device.

To ensure that the EN/UVLO pin is not triggered prematurely (i.e., within tolerance of +12V ATX spec), the absolute worst-case scenario in which voltage output is still allowed is considered. The +12V ATX rail has a ±5% tolerance per the ATX v2.2 specification, which means that the worst case allowable voltage on the rail, for the purposes of this task, is +11.4V. Moreover, UVLO's maximum voltage is considered part of the worst case scenario, and so UVLO = 1.26V is considered as well. Hence, a resistor divider between 11.4V and GND that achieves an intermediary 1.26V is considered.

When considering the resistor tolerances, the effective worst-case resistor tolerance would be if the resistor between V_IN and EN/UVLO was at its highest value, and the resistor between EN/UVLO and GND was at its lowest value. Thus, the worst-case resistor divider value ratio should be `1.26 / 11.4V = 0.1105`. By choosing a top resistor of 220kΩ±1% and a bottom resistor of 28kΩ±1%, the lowest possible resistor divider ratio becomes 1.264, which is above the maximum UVLO voltage of 1.26V.

These calculations are very important, as the TPS55288 shutting down in high current scenarios is catastrophic to the operation of the LAZARUS-1 server; for example, when performing a critical render or other important computationally intensive operation on the laptop connected to the device, any drop out in power would be highly detrimental. To further aid this, and in accordance with the EVM, a 100nF capacitor is added between EN/UVLO and GND to filter noise.

### I2C Pins
>*Pins: SCL (5), SDA (6)*

The I2C channel of the TPS55288 connects directly to the TPS65987D, with 10kΩ pull up resistors on both SCL and SDA; the pull up resistance is very straightforward to choose because there are no other devices on this channel. This is an I2C slave interface on the TPS55288 side, which allows the TPS65987D to set the output voltage of the TPS55288, along with configuring any of its internal registers.

### MODE Pin: I2C Address Selection and Operating Mode at Light Load
> *Pin: MODE (15)*

Per the datasheet, the MODE pin serves two functions, based on the resistor value between it and VCC (either internal or external). Internal VCC is provided by an internal regulator to the VCC pin (19), and external VCC is +5V provided by the +5V ATX PSU rail. However, to minimize power dissipation, +5V is applied to the VCC pin of the TPS55288 in this application, and so only external VCC can be used for the MODE pin.

The first function of the MODE pin is to select the slave address of the TPS55288. The exact address chosen does not really matter for this application, since the TPS55288 is the only device on the TPS65987D's I2C1 interface; it matters only for programming the TPS65987D, where the exact address that the TPS65987D must target on startup is important to pinpoint.

The second function of the MODE pin is to select if the TPS55288 operates in PFM (Pulse Frequency Modulation) or PWM (Pulse Width Modulation). Per the datasheet, PFM has much higher low current efficiency (~90% at 12V input with 0.01A @ 20V output vs. ~30%) but increased switching frequency, 