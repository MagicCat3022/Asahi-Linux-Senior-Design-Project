# F-001: DCP marked as crashed after a slow display power-off

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | DCP timeout |
| Hardware | Reported on M1 Pro; not yet tried on `MAC-01` |
| Setup | Not recorded upstream in our notes |
| Rate | Not measured |
| Upstream | Issue [#634](https://github.com/AsahiLinux/linux/issues/634) (cause 1); PR [#582](https://github.com/AsahiLinux/linux/pull/582) (open), PR [#635](https://github.com/AsahiLinux/linux/pull/635) (closed, not merged) |
| Owner | Unassigned |

## Symptom

The external display works at first. After unplugging and replugging it, the
display stays black until reboot. The monitor is still detected, but no mode
is applied.

## Reproduction

Not yet reproduced by the team. Upstream: connect a display over USB-C DP,
unplug it, replug it.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Suspected (upstream analysis).** `iomfb_poweroff()` waits 50 ms for the
display shutdown clear-swap; the hardware was observed taking about 53 ms.
The driver treats the timeout as a DCP crash and sets `dcp->crashed`
permanently, so later display commits return `-EINVAL`.

## Fix

PR #582 stops latching `crashed` on this timeout and was tested on M1
hardware. PR #635 took a similar approach and was closed without merge.

## History

- 2026-10-14: entry created from the fairydust research notes.
