## What and why

<!-- One or two sentences. Link relevant docs, experiments, or failure entries (F-NNN). -->

## Type

- [ ] Guide or reference update
- [ ] Experiment report
- [ ] Failure catalogue change
- [ ] Tools or tests
- [ ] Other:

## Checklist

CI runs `tools/check-docs.py` and the unit tests. It can't check these:

- [ ] Guide changes: commands rerun and **Last verified** updated
- [ ] Experiment reports: every exported file read before `evidence --finalize`
- [ ] No binaries, keys, IP addresses, or serial numbers added
