# F-008: Suspend/resume with DisplayPort active is incomplete

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | Suspend/resume |
| Hardware | All fairydust machines; PR #510 tested on J313 |
| Setup | External display active, then system suspend |
| Rate | Not measured |
| Upstream | PR [#510](https://github.com/AsahiLinux/linux/pull/510) (open); `ps_atc1_common` always-on commits listed in [USB-C display commits](../research/usb-c-display-commits.md#power-workaround-4) |
| Owner | Unassigned |

## Symptom

DP suspend/resume handling is incomplete. As a workaround, the device tree
marks some ATC PHY power domains `apple,always-on`, so that hardware never
fully powers down during suspend.

## Reproduction

Not yet reproduced by the team. Desired behavior to test against: display
active → suspend → hardware powers down → resume → PHY and display path
reinitialize → the external monitor reconnects by itself.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Known gap.** The ATC PHY lacks suspend/resume handling for DP Alt Mode, and
inactive DCPs aren't quiesced on suspend.

## Fix

PR #510 quiesces inactive DCPs on suspend and tries to prevent resume crashes;
it still needs stress testing.

## History

- 2026-10-14: entry created from the fairydust research notes.
