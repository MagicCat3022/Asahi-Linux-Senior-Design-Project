# Glossary

Words used across the docs and tools, in alphabetical order. For how the
pieces fit together, see the [overview](../overview.md).

| Term | Meaning |
| --- | --- |
| **ADT** | Apple Device Tree. Apple's description of the hardware, which m1n1 reads and converts into a Linux device tree. Never commit ADT dumps; they contain serial numbers. |
| **Alt mode (DP alt mode)** | A USB-C feature that carries DisplayPort video over some of the cable's wires. This is what the project is fixing. |
| **ATC0, ATC1** | The Mac's two USB-C port blocks (Apple Type-C). On the MacBook Air M2, ATC0 is the rear port next to MagSafe and ATC1 is the front port. See [hardware](hardware.md). |
| **ATCPHY** | The PHY driver for an ATC port. It switches the port's lanes between USB and DisplayPort. |
| **Baseline** | The kernel installed on the Mac, captured as a bundle with `./tools/asahi capture`. Test results are compared against it. |
| **Bundle** | Everything the PC needs to boot one kernel under the hypervisor: kernel `Image`, device tree (`.dtb`), initramfs, `.config`, and a checksum manifest. Kept in `.asahi/bundles/`. `./tools/asahi bundles` lists them. |
| **BUSID** | The number usbipd-win gives a USB device on Windows, like `3-6`. It stays the same as long as the cable stays in the same PC port. |
| **Controller PC** | The PC that runs `./tools/asahi`. Ours is Windows with Ubuntu in WSL2. |
| **DCP** | Display Coprocessor. Apple's firmware-driven display controller, driven by the `apple-dcp`/`appledrm` drivers. "External DCP" (`dcpext`) drives the USB-C display. |
| **Device tree (DTB)** | A file describing the hardware to Linux. Built with the kernel; the J413 one is `t8112-j413.dtb`. Always boot a kernel with the device tree from the same build. |
| **Driver profile** | A file in `tools/profiles/` listing the config options, modules, and devices a test needs, and which port the proxy cable must use. `j413-usbc-dp` is the only one so far. |
| **fairydust** | The Asahi kernel branch with the newest USB-C display work. Our work branches start from it. |
| **Guest** | The kernel running under the m1n1 hypervisor. |
| **HPD** | Hot-plug detect: the signal that a display was connected or removed. |
| **HV (hypervisor)** | m1n1's mode that runs a Linux kernel as a guest while watching and logging it. "HV shell" is the Python prompt you get by interrupting the guest. |
| **initramfs** | A small file system the kernel loads first, holding the drivers it needs to mount the real disk. `stage` builds one for each test kernel. |
| **iodev** | m1n1's number for the connection it is using to talk to the PC. On the J413, iodev 4 is ATC0 and iodev 5 is ATC1. |
| **J413** | Apple's board name for the MacBook Air M2 (2022). Its device-tree name is `apple,j413`. |
| **m1n1** | Asahi's first-stage bootloader. It can also act as a proxy and a hypervisor. |
| **Proxy mode** | m1n1 waiting on USB for commands from the PC instead of booting Linux. You reach it from a separate m1n1 boot entry. |
| **Release** | A kernel's version string, as in `uname -r`. Every test build gets a new one (for example `7.1.13-fairydust-sdp-20261014…`) so its modules never overwrite another kernel's. |
| **Run** | One boot attempt. Its logs and records are in `.asahi/runs/RUN_ID/`, where the run ID is the UTC start time. |
| **Session** | The tmux session (`asahi-hv`) with two windows, `serial` and `hv`, that `./tools/asahi session start` opens for a run. It keeps going if you close your terminal. |
| **Stage** | Install a build's modules on the Mac, build its initramfs, and copy the result to the PC as a bundle. |
| **Tethered boot** | Booting the Mac with m1n1 controlled from another computer over USB, which is what proxy mode does. |
| **TIPD** | The TI USB-C power delivery controller (TPS6598x) on each port, and its Linux driver. It negotiates alt mode and reports plug events. |
| **usbipd-win** | A Windows program that passes a USB device through to WSL. We use it for the Mac's m1n1 connection. |
| **WSL** | Windows Subsystem for Linux, which runs Ubuntu on the controller PC. |
