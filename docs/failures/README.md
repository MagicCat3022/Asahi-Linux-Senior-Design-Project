# Failure catalogue

One file per failure class, `F-NNN-slug.md`, from
[the template](../templates/failure.md). This catalogue feeds the failure
catalogue and diagnosis reports in `deliverables/`.

**Status values:** `upstream-reported` → `reproduced` → `diagnosed` →
`fix-in-progress` → `fixed`, or `wont-fix` / `out-of-scope`. An entry moves
to `reproduced` only when one of our experiments shows it, with a rate
(n failures in m attempts).

When you change an entry's status, update this table in the same commit.

| ID | Failure | Class | Status | Reported on | Upstream |
| --- | --- | --- | --- | --- | --- |
| [F-001](F-001-dcp-false-crash-on-poweroff.md) | DCP marked crashed after slow power-off | DCP timeout | upstream-reported | M1 Pro | [#634](https://github.com/AsahiLinux/linux/issues/634) |
| [F-002](F-002-cd321x-no-dp-after-usb-failure.md) | Controller can't re-enter DP Alt Mode | PD controller state | upstream-reported | M1 Pro | [#634](https://github.com/AsahiLinux/linux/issues/634) |
| [F-003](F-003-link-training-swing-not-applied.md) | Swing/pre-emphasis not applied; black screen | Link training | upstream-reported | — | [#611](https://github.com/AsahiLinux/linux/issues/611) |
| [F-004](F-004-via-labs-hub-link-bounce.md) | Link bounces through VIA Labs hub | Adapter interoperability | upstream-reported | **M2 Air** | [#571](https://github.com/AsahiLinux/linux/issues/571) |
| [F-005](F-005-studio-display-inactive-sink.md) | Studio Display torn down | DCP firmware events | upstream-reported | — | [#579](https://github.com/AsahiLinux/linux/issues/579) |
| [F-006](F-006-stale-monitor-identification.md) | Stale monitor identification/layout | Monitor identification | upstream-reported | — | [#474](https://github.com/AsahiLinux/linux/issues/474) |
| [F-007](F-007-single-blessed-dp-port.md) | DP only on one blessed port | Display routing | upstream-reported | all | [#637](https://github.com/AsahiLinux/linux/issues/637) |
| [F-008](F-008-dp-suspend-resume.md) | Suspend/resume with DP active | Suspend/resume | upstream-reported | all | PR [#510](https://github.com/AsahiLinux/linux/pull/510) |

Next free ID: **F-009**.
