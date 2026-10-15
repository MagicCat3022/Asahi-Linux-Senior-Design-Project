# F-003: Black screen because requested swing/pre-emphasis isn't applied

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | Link training |
| Hardware | Not recorded in our notes; not yet tried on `MAC-01` |
| Setup | Depends on monitor, cable, and DP version |
| Rate | Not measured |
| Upstream | Issue [#611](https://github.com/AsahiLinux/linux/issues/611) |
| Owner | Unassigned |

## Symptom

Fairydust detects and configures the monitor (EDID read, modes listed, DP
link configured, DCP modeset complete, DRM connector `connected`), but the
monitor stays black.

## Reproduction

Not yet reproduced by the team. Reported effects: one monitor or cable works
while another doesn't; DP 1.2 works while DP 1.4 fails; lower resolutions are
more stable than higher-bandwidth modes. A test matrix over monitors and
cables from [the hardware inventory](../reference/hardware.md) should show it.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Suspected (upstream analysis).** The DP sink requests a voltage swing and
pre-emphasis. Fairydust stores the requested values but doesn't fully apply
them to the ATC PHY, so the physical signal may not meet the monitor's needs.

## Fix

None yet.

## History

- 2026-10-14: entry created from the fairydust research notes.
