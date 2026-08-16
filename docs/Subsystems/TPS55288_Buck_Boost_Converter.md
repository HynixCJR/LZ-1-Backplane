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

The second function of the MODE pin is to select if the TPS55288 operates in PFM (Pulse Frequency Modulation) or PWM (Pulse Width Modulation). Per the datasheet, PFM decreases the switching frequency to decrease switching loss and achieve much higher low-current efficiency (~90% at 12V input with 0.01A @ 20V output vs. ~30%), with the tradeoff of less-predictable EMI/noise. On the other hand, PWM (or rather, forced-PWM) keeps the switching frequency constant during light loads, which leads to no low-frequency noise, but worse efficiency. For this application, PFM is selected for its higher efficiency; low-frequency noise is not as detrimental to this system, as are not really any particularly noise-sensitive parts (e.g. RF, audio, etc.) on this PCB.

To set PFM, the MODE pin is floated in this design. This is chosen over the other options in the datasheet, which all use a pull up or pull down resistor, as this still achieves PFM while using one less component.

That said, the actual mode used for this system is decided entirely based on the value written to the `6h` register, after the system has received programming over I2C. 

### DITH/SYNC Pin
> *Pin: DITH/SYNC (7)*

The TPS55288 operates at a fixed PWM frequency, and as a result, has significant EMI concentrated at that frequency (known as narrowband). This can pose challenges for testing and certification (which is not really all that important for this application), but also just makes the voltage rails and surrounding areas on the PCB noisier at the specific frequency that the TPS55288 operates at. Aside from specific layout considerations to reduce noise, bypass filtering, snubbers, and shielding, dithering — which wobbles the switching frequency over time to spread out EMI over a wider band (i.e., broadband) — can help handle large EMI spikes.

The TPS55288 enables and adjusts dithering through its DITH/SYNC pin. By adding a capacitor between this pin and ground, the TPS55288 can charge and discharge the capacitor to create a triangular voltage waveform that modulates the TPS55288's fixed PWM frequency by ±7%. The capacitance of the dithering can be set by the value of the capacitor, the equation for which is provided by:
```
C_DITH = (2.8 × R_FSW × F_MOD)^-1 [F]
```

...where `R_FSW` is the resistor value at the FSW pin, and `F_MOD` is the desired modulation frequency.

For the purposes of this application, a 10nF capacitor is used, which matches the EVM. Matching the EVM here is helpful because it permits replicating the same COMP resistor/capacitor network.

The DITH/SYNC pin also disables dithering if the voltage at that pin is below 0.4V or above 1.2V, or when an external synchronous clock is used (which it isn't, in this application). If dithering must be disabled, the 100nF capacitor can simply be shorted to GND to achieve this.

### FSW Pin
> *Pin: FSW (8)*

The FSW pin sets the frequency at which the TPS55288 switches at in PWM mode. The value of the resistor between this pin and GND dictates this frequency, and is calculated using the following formula:
```
f_FSW = 1000 / (0.05 × R_FSW + 20) [MHz]
```

...where `R_FSW` is the resistor value, and `f_FSW` is the frequency that results from it. The EVM and datasheet's example circuit both use a 49.9kΩ resistor, and so that is what is used in this application. This results in a 400 kHz switching frequency.

### PGND and AGND
> *Pins: PGND (9, 24), AGND (10)*

PGND is Power Ground, and AGND is Analog Ground. The tl;dr is that PGND and AGND should be separated except at the terminal of the capacitor at VCC, to prevent the noise from the MOSFETs switching and parasitic inductance to affect the sensitive analog pins of the TPS55288.

### VOUT Bypass Capacitors
> *Pin: VOUT (11)*

The VOUT pin is, as the name suggests, the voltage output of the TPS55288. It is connected directly to the 10mΩ sense resistor and the ISP pin for current sensing, which then connects to the VBUS pin of the USB-C connector to power the laptop. This pin has several bypass capacitors attached to it, which must all be rated for 25V or higher (ideally >35V), as the voltage can be as high as 20V sustained at this pin.

The EVM has more capacitors on this pin than the datasheet, and the LAZARUS-1 PCB follows the EVM (for this specific pin). So, 4x10uF, 1x1uF, 1x100nF,  and 1x220uF capacitors are placed between this pin and PGND, placed close to the pin itself. Note that the 220uF capacitor used here is an aluminum electrolytic capacitor, which has polarity; the positive end *must* be connected to VOUT for proper functionality.

Additionally, in accordance with the EVM, a 1uF bypass capacitor is placed immediately following the current sense resistor.

### SWx and BOOTx Pins
> *Pins: SW1 (23), SW2 (21, 25), BOOT1 (22), BOOT2 (20)*

Per the datasheet, the SW1 is the switching node of the buck side of the TPS55288, and it connects to the drain of the external low-side power MOSFET, as well as the source of the external high-side power MOSFET. On the other hand, SW2 is the switching node of the boost side of the TPS55288, which means that it connects to the drain of the *internal* low-side power MOSFET and the source of the *internal* high-side power MOSFET. For layout purposes, only SW1 has to be routed to anything else; SW2 only connects to an inductor between it and SW1. 

An inductor is placed between SW1 and SW2. The EVM and datasheet both recommend the `XAL1010-472ME` 4.7uH inductor, but this inductor is far too expensive and is not in stock at LCSC. The datasheet also lists two other alternatives, one of which is the Sumida `125CDMCCDS-4R7MC`. This is available on LCSC, and has an alternative part (the XR `XR XR1265-4R7M`) that is substantially cheaper and has lower DCR, higher I_SAT, and is otherwise the exact same. That is the inductor used for this application.

BOOT1 and BOOT2 are the power supply pins for the high-side gate driver on the buck and boost sides respectively. A 100nF capacitor connects this pin to SW1 (for BOOT1) and SW2 (for BOOT2).

### COMP Pin
> *Pin: COMP (18)*

The COMP pin, per the datasheet, is the output of the internal voltage amplifier. Unfortunately, the datasheet does not comprehensively detail what that is, but it does provide formulae for calculating the values of the resistor/capacitor network attached to this pin. However, since this application uses the same general configuration for everything (output voltage/current, switching frequency, dithering frequency), the same resistor/capacitor network can be used.
> [!WARNING]
> This needs to be verified...

### ILIM Pin
> *Pin: ILIM (17)*

The TPS55288 supports average current limiting through the external 4.7uH inductor; this is performed through the ISP and ISN pins, which sense the average voltage across the inductor and calculate the current. However, momentary spikes in current that are far above the average current occur during switching, and the TPS55288 also supports sensing this current. This peak current is set using the ILIM pin. Per the datasheet, a 20kΩ pull down resistor is recommended here (which is also used in the EVM), and hence that is what is implemented in this design.

### CDC Pin
> *Pin: CDC (16)*

On the CDC pin, the TPS55288 outputs a voltage equal to `20 × (V_ISP - V_ISN)`, which can be used for current monitoring. In this application, this pin is connected to the LicheeRV Nano's ADC pin to perform current monitoring, which is preferred over using a PAC1954 because the PAC1954 presents a (small) amount of loss across its own current sense resistor. Note that because of the `20×` multiplication of the voltage, a separate operational amplifier circuit (like what the ADCs use for the 12V/5V rails of each SATA port in this design) is not needed; the voltage is high enough that the voltage sensed by the LicheeRV Nano is sufficiently accurate.

In addition to current sensing, this pin can be used for droop compensation. The USB-C cable that is connected to this PCB presents some amount of resistance, which leads to the actual voltage presented to the connected laptop being slightly lower than at the output of the TPS55288. To compensate for this, the output voltage can be increased slightly through droop compensation, which occurs through the pull down resistors on the CDC and FB/INT pins. This is for *external* compensation; however, *internal* compensation, which does not require resistors on either of these pins, can be used instead, and uses an internal voltage divider to achieve the same thing. Internal compensation is controlled by writing the intended voltage compensation into the CDC[2:0] bits in register `05h` of the TPS55288. This is what is used in the LAZARUS-1 PCB, as it requires fewer resisters. As a result, the CDC pin is not connected to a pull down resistor, and is instead only connected to 

### FB/INT Pin
> *Pin: FB/INT (14)*

In external compensation mode, the FB/INT pin must be wired to the middle of a voltage divider (through a single external resistor) to configure droop compensation. However, in internal mode (which is what is used in this design), the FB/INT pin just acts as a fault indicator. It is thus pulled up to 3.3V by a 10kΩ resistor, and is connected to an RP2354B for fault detection.