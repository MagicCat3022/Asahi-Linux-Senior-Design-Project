# Fairydust status and upstream issues

**Snapshot:** late September 2026, converted from *Fairydust Research &
Current Status.docx*. Issue and PR states rechecked on 2026-10-14. The
per-issue details now live in the [failure catalogue](../failures/).

## Current fairydust status

- Fairydust is the experimental Asahi Linux kernel branch for USB-C
  DisplayPort Alt Mode on Apple Silicon.
- Basic USB-C external display output works in some configurations.
- It is still work in progress and not production-ready. Development is now
  about reliability, compatibility, and feature parity rather than first-time
  display output.
- Main remaining areas: DP Alt Mode negotiation, hot-plug and reconnect
  reliability, link training, monitor and adapter compatibility,
  suspend/resume, display routing, DCP firmware handling, USB4/Thunderbolt,
  and PCIe tunneling.
- The last branch update before this snapshot was on 2026-09-08. It included
  an M1 SIO device-tree fix that enabled DisplayPort audio.

## Upstream issues

All are in [AsahiLinux/linux](https://github.com/AsahiLinux/linux/issues).

| Issue | Summary | State (2026-10-14) | Catalogue |
| --- | --- | --- | --- |
| [#634](https://github.com/AsahiLinux/linux/issues/634) | Hot-plug stops working until reboot (M1 Pro); two causes | Open | [F-001](../failures/F-001-dcp-false-crash-on-poweroff.md), [F-002](../failures/F-002-cd321x-no-dp-after-usb-failure.md) |
| [#611](https://github.com/AsahiLinux/linux/issues/611) | Sink's swing/pre-emphasis requests never applied to ATC PHY | Open | [F-003](../failures/F-003-link-training-swing-not-applied.md) |
| [#571](https://github.com/AsahiLinux/linux/issues/571) | Link bounces with a VIA Labs hub (M2 Air) | Open | [F-004](../failures/F-004-via-labs-hub-link-bounce.md) |
| [#579](https://github.com/AsahiLinux/linux/issues/579) | Studio Display: unhandled `INACTIVE_SINK_DETECTED` | Open | [F-005](../failures/F-005-studio-display-inactive-sink.md) |
| [#474](https://github.com/AsahiLinux/linux/issues/474) | Monitor identification and layout don't update | Open | [F-006](../failures/F-006-stale-monitor-identification.md) |
| [#637](https://github.com/AsahiLinux/linux/issues/637) | DP output on any port, not one "blessed" port | Closed, not planned | [F-007](../failures/F-007-single-blessed-dp-port.md) |
| PR [#510](https://github.com/AsahiLinux/linux/pull/510) | Suspend/resume with DP active | Open | [F-008](../failures/F-008-dp-suspend-resume.md) |

## USB4 / Thunderbolt

- Sven Peter posted version 2 of an Apple Silicon USB4/Thunderbolt driver
  series in September 2026: 22 patches targeting M1, M2, and M3 SoCs.
- Hardware involved: the Apple ACIO block, the USB4 router, an internal
  Cortex-M3 coprocessor, DART (IOMMU), and the Native Host Interface.
- Working: USB4 infrastructure, the Linux Thunderbolt software connection
  manager talking to Apple hardware, initial XDomain support, and USB3
  tunneling over USB4.
- Still incomplete: full DisplayPort tunneling, PCIe tunneling, complete
  Thunderbolt feature parity, hot-plug and device compatibility, and
  performance.
- For the project, this means much less USB4 groundwork to build from
  scratch for the later goals.

## PCIe tunneling (stretch goal)

Target path: Thunderbolt NVMe enclosure → USB4 host/router → Thunderbolt
connection → PCIe tunnel → external NVMe controller → Linux PCI enumeration →
NVMe driver → usable storage.

Ways to validate it: the device appears in `lspci`, the NVMe driver binds,
the drive appears in Linux, and read/write, hot-plug, throughput, and
stability tests pass. It isn't complete in current Apple Silicon USB4 support,
so it remains a stretch goal.

## Remaining areas for project work

USB-C DP negotiation failures; hot-plug and reconnect reliability; CD321x
controller recovery; DisplayPort link training, including voltage swing and
pre-emphasis; monitor, adapter, and dock compatibility; DCP firmware event
handling; suspend/resume; Mac mini display behavior; validating future
multi-port routing; USB4 integration; PCIe tunneling; performance and
reliability testing.
