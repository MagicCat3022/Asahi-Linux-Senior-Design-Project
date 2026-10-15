# Experiments

One folder per hardware run you might cite later:
`YYYY-MM-DD-slug/README.md` plus an `evidence/` folder. The date is the UTC
date of the first run, matching the run IDs. Start from
[the template](../templates/experiment.md) and follow
[Record an experiment](../guides/recording-an-experiment.md).

Reports are frozen once merged. Fix mistakes with a dated entry in the
report's *Corrections* section.

| Date | Experiment | Kernel | Outcome |
| --- | --- | --- | --- |
| 2026-10-14 | [Installed baseline under m1n1 HV](2026-10-14-baseline-hv/) | `7.1.13-fairydust+` | HV boot PASS; DP drivers not ready with proxy on ATC1 |
| 2026-10-14 | [tipd-oob-fixes candidate under m1n1 HV](2026-10-14-tipd-oob-fixes/) | `301e2ba4` | HV boot and DP driver readiness PASS; hot-plug NOT TESTED |
