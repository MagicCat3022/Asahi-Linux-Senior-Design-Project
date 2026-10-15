# F-005: Studio Display torn down after an unhandled firmware event

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | DCP firmware event handling |
| Hardware | Not recorded in our notes; requires an Apple Studio Display |
| Setup | Apple Studio Display over USB-C |
| Rate | Not measured |
| Upstream | Issue [#579](https://github.com/AsahiLinux/linux/issues/579) |
| Owner | Unassigned |

## Symptom

Most of the USB-C/DP path comes up, then DCP tears down the display
connection.

## Reproduction

Not yet reproduced by the team; needs a Studio Display.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Suspected (upstream analysis).** DCP firmware sends
`DPTX_APCALL_INACTIVE_SINK_DETECTED` (call 20). Fairydust acknowledges it
without the correct response, so DCP tears the connection down. The display
probably needs a sink activation or wake-up sequence that macOS performs.
Investigate with m1n1 tracing under macOS and compare with fairydust.

## Fix

None yet.

## History

- 2026-10-14: entry created from the fairydust research notes.
