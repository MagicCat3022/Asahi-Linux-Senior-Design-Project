# YYYY-MM-DD: Short experiment title

<!-- ./tools/asahi evidence starts this file for you, with Inputs and the
     automated Results filled in. Steps: docs/guides/recording-an-experiment.md -->

**Author:** NAME · **Runs:** `RUN_ID` · **Status:** draft | final

## Goal

One or two sentences: the question this run answers, and the failure entries
it targets, if any.

## Inputs

| Input | Value |
| --- | --- |
| Kernel commit | Full commit hash and the source folder it was built from |
| Kernel release | `7.1.13-fairydust-sdp-…` |
| Config | SHA-256 of `.config`; changes from the baseline |
| Driver profile | `j413-usbc-dp` or none |
| Toolchain | Versions from `build.json`, or "not recorded" |
| m1n1 commit | From `boot.json` |
| Project commit | The commits whose tools built and booted the kernel |
| Exact inputs (private) | Archives kept, and any that are unavailable; links in `evidence/RUN_ID/logs.md` |
| Hardware | `MAC-01`; proxy on ATC0; `MON-01` via `CAB-01` on ATC1 |

## Procedure

Followed [Test a kernel](../../guides/test-a-kernel.md). List only what you
did differently, plus any physical actions, e.g. "unplugged `CAB-01` at
T+60 s, replugged at T+75 s".

## Results

| Check | Result | How | Evidence |
| --- | --- | --- | --- |
| HV boot: run marker, release, root, modules, SSH | PASS | automated | [check.json](evidence/RUN_ID/check.json) |
| External display shows image | NOT TESTED | — | no monitor attached |
| Hot-plug ×10 | FAIL 3/10 | manual | Observations, below |

Use only PASS, FAIL, NOT TESTED, or BLOCKED. **Automated** means a tool
performed the check; **manual** means a person observed it, so name the
observer and time in Observations.

## Observations

What happened that the table doesn't show: short log excerpts with file and
line, timing, surprises. Quoted lines become public, so read them first.

## Conclusion

What this run shows, and what it doesn't. Which failure entries changed status.

## Next steps

- …

## Corrections

Leave empty. After the report is merged, add dated corrections here instead
of editing the text above.
