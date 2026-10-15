# F-004: DP link repeatedly bounces through a VIA Labs hub

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | Adapter interoperability |
| Hardware | Reported on M2 MacBook Air, the same model as `MAC-01` |
| Setup | VIA Labs-based hub (PS186 per the issue title); a UGREEN adapter on the same machine, monitor, and port works |
| Rate | Not measured |
| Upstream | Issue [#571](https://github.com/AsahiLinux/linux/issues/571) |
| Owner | Unassigned |

## Symptom

With the VIA Labs hub, the display is detected, EDID is read, and modes are
found, then the link drops and reconnects in a loop: connected → HPD asserted
→ modes found → link drops → reconnect.

## Reproduction

Not yet reproduced by the team. Because it was reported on our Mac model,
this is a good first reproduction target once the team has a VIA Labs-based
hub. Record the hub and adapter in [the hardware inventory](../reference/hardware.md).

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Unknown.**

## Fix

None yet.

## History

- 2026-10-14: entry created from the fairydust research notes.
