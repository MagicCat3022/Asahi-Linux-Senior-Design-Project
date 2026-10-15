# YYYY-MM-DD: Short experiment title

<!-- Folder: docs/experiments/YYYY-MM-DD-slug/ (UTC date of the first run).
     Steps: docs/guides/recording-an-experiment.md -->

**Author:** NAME · **Runs:** `YYYYMMDDTHHMMSS…Z` · **Status:** draft | final

## Goal

One or two sentences: the question this run answers. Link the failure entries
it targets, e.g. [F-001](../../failures/F-001-slug.md).

## Inputs

| Input | Value |
| --- | --- |
| Kernel commit | full 40-character hash (branch name) |
| Kernel release | `7.1.13-fairydust-sdp-…` |
| Config | SHA-256 of `.config`; changes from the baseline, if any |
| Driver profile | `j413-usbc-dp` or none |
| Toolchain | clang, rustc, bindgen versions (from `.config`) |
| m1n1 commit | from `boot.json` |
| Guide followed | [guide name](../../guides/…) at project commit `…` |
| Hardware | `MAC-01`; proxy on ATC0; `MON-01` via `CAB-01` on ATC1 |

## Procedure

Link the guide. List only what you did differently from it, plus any
physical actions, e.g. "unplugged `CAB-01` at T+60 s, replugged at T+75 s".

## Results

| Check | Result | How | Evidence |
| --- | --- | --- | --- |
| HV boot, exact run marker, release, root | PASS | automated | [check.json](evidence/RUN_ID/check.json) |
| Driver binding (live) | PASS | automated | [driver-check](evidence/RUN_ID/driver-check-STAMP.json) |
| External display shows image | NOT TESTED | — | no monitor attached |
| Hotplug ×10 | FAIL 3/10 | manual | notes below, [serial.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/main/SLUG/RUN_ID/serial.log) *(private)* |

Use only PASS, FAIL, NOT TESTED, or BLOCKED. "Automated" means a tool wrote
the evidence file; "manual" means a person observed it.
Logs live in the private evidence repository; each run's `evidence/RUN_ID/logs.md`
lists their links.

## Observations

What happened that the table doesn't show: log excerpts (short, with file and
line), timing, surprises.

## Conclusion

What this run shows, and what it doesn't. Which failure entries changed status.

## Next steps

- …

## Corrections

Leave empty. After the report is merged, add dated corrections here instead
of editing the text above.
