# F-006: Monitor identification and layout don't update after switching monitors

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | Monitor identification |
| Hardware | Not recorded in our notes |
| Setup | Switching between two DP Alt Mode monitors under KDE |
| Rate | Not measured |
| Upstream | Issue [#474](https://github.com/AsahiLinux/linux/issues/474) |
| Owner | Unassigned |

## Symptom

After switching external monitors, the make/model can stay stale and the
desktop layout keeps the previous monitor's dimensions, so KDE shows
overlapping screens or gaps.

## Reproduction

Not yet reproduced by the team; needs two different monitors.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Unknown.** Lower priority than kernel-level link problems, but user-visible.

## Fix

None yet.

## History

- 2026-10-14: entry created from the fairydust research notes.
