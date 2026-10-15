# Overview of `atc.c`, `core.c`

This document regards the files located at `drivers/phy/apple/atc.c` and `drivers/usb/typec/tipd/core.c` on the [main asahi kernel tree](https://github.com/AsahiLinux/linux). These files were created by Sven Peter <sven@kernel.org>, and Heikki Krogerus <heikki.krogerus@linux.intel.com>
respectively.

Particularly we are concerned with providing a high-level overview of the file structure, and explaining what functionality they implement.

---

## Overview of `drivers/phy/apple/atc.c`

This is the Apple Type C PHY (`ATCPHY`) driver. For the unitiatied, `ATCPHY` is physical layer hardware located in Apple Silicon chips,
its job is to allow connectivity from `USB 2.0`, `USB 3.x`,
`USB4/Thunderbolt`, and `DisplayPort` connectivity via its `Type-C` ports.

Specifically, `ATCPHY` multiplexes the various protocols and provides the reset controller for the attached DWC3 USB controller.



## Overview of `drivers/phy/apple/atc.c`

This is the driver for `TI TPS6598x` USB Power Delivery controller family. These consists of stand-alone USB Type-C and USB Power Delivery (PD) controllers designed to manage cable orientation,-orientation detection, power-path switching, and protocol negotiations