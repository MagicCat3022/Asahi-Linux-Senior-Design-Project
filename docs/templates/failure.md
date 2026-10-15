# F-NNN: Short description of the failure

| Field | Value |
| --- | --- |
| Status | upstream-reported · reproduced · diagnosed · fix-in-progress · fixed · wont-fix · out-of-scope |
| Class | e.g. DCP timeout, PD controller state, link training, routing, suspend/resume |
| Hardware | machines where it occurs (`MAC-01`), and where it was tried without occurring |
| Setup | port, monitor, cable, adapter IDs |
| Rate | n failures / m attempts, per experiment below |
| Upstream | issue and PR links |
| Owner | NAME |

## Symptom

What a user sees.

## Reproduction

Numbered steps, precise enough that a teammate gets the same result.

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| YYYY-MM-DD | [slug](../experiments/YYYY-MM-DD-slug/) | 3/10 FAIL |

## Cause

**Suspected** or **confirmed**. Say which, and what evidence supports it. Link
code by commit and line.

## Fix

Branch, commits, and test results. Or why it won't be fixed.

## History

- YYYY-MM-DD: status changed to `…` because …
