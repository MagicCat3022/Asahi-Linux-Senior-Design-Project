# F-002: USB-C controller can't re-enter DP Alt Mode after a USB failure

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | PD controller state (CD321x) |
| Hardware | Reported on M1 Pro; not yet tried on `MAC-01` |
| Setup | Not recorded upstream in our notes |
| Rate | Not measured |
| Upstream | Issue [#634](https://github.com/AsahiLinux/linux/issues/634) (cause 2) |
| Owner | Unassigned |

## Symptom

After certain USB failures, power and USB may still partly work, but the port
never negotiates DisplayPort again: there is no DP connection and no HPD
sequence.

## Reproduction

Not yet reproduced by the team. The triggering "USB failures" are not yet
characterized; the upstream issue title mentions a second USB-C dock.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Unknown.** Still under investigation upstream. This is directly related to
the TIPD driver the team has been testing; see
[2026-10-14-tipd-oob-fixes](../experiments/2026-10-14-tipd-oob-fixes/).

## Fix

None yet.

## History

- 2026-10-14: entry created from the fairydust research notes.
