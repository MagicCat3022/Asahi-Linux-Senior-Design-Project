# Notes on Asahi progress reports

**Written:** October 2026 · Summaries of the USB and DisplayPort parts of
Asahi's public progress updates.

## [USB3 progress update notes](https://gist.github.com/marcan/a04dbffc4ed29abd5e39c4651f980d5d)


The missing piece used to be the `PHY driver`, which is for hardware (specifically `Apple Type-C PHY (ATCPHY))` that supports USB3, DisplayPort, and TB3/USB4.

The `PHY driver` configures physical hardware with settings, which includes variable data, "magic" register pokes and so on. Very complex piece of software. Sven has been working on reverse engineering this.

The `PHY driver` also very carefully coordinates with the USB controller driver `dwc3` and the Type C port controller driver `tipd`. When devices are connected or disconnected information has to reach PHY which then routes everything appropriately. Finally, hardware is picky and will lock up if there is anything wrong with the controller.

USB3 mode should be pretty solid, but expect glitches when hotplugging devices quickly.

---

## [Progress Report 6.19](https://asahilinux.org/2026/02/progress-report-6-19/#fnref:3)

In December 2025, the `fairydust` branch was pushed to the asahi linux downstream tree. Getting usb to work involves four distinct hardware blocks; `DCP1`(Display Coprocessor), `DPXBAR2` (Display Crossbar), `ATCPHY`(Apple Type-C PHY), and `ACE` (USB-C Power Delivery Controller).
Each of them was reverse engineered, and required a unique linux driver.

Currently the `fairydust` branch “blesses” a specific USB-C port on a machine for use with DisplayPort, meaning that multiple USB-C displays is still not possible. There are also some quirks regarding both cold and hot plug of displays. Finally, the DCP does not work well with some monitor
setups and ends up not displaying the correct colors or misses timing modes.

The `fairydust` branch is still not deemed ready for general use, and is 
intended for developers who can help iron out the functionality with minimal support from the asahi team.

---

## [Progress Report 7.2](https://asahilinux.org/2026/08/progress-report-7-2/)

All M1 through base M3 series devices used an Apple-specific Texas Instruments USB port controller called `CD3217` (or ACE2). This sits on the I²C bus and negotiates with USB devices when they are plugged in. Starting with M3 Pro/Max, Apple has switched to ACE3. ACE3 instead uses the SPMI bus, which required some more reverse engineering. ACE3 has pretty much the same register set as CD3217, only wrapped in a SPMI interface instead of addressed over I2C. Both the SPMI interface and ACE3 itself are now working in Asahi Linux, bringing USB 3.0 and Thunderbolt support to all M3 series devices.

---

