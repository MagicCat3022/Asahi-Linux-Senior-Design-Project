# 0001: Documentation layout and one editable home per document

**Date:** 2026-10-14 · **Status:** accepted · **Deciders:** Mustafa Maras (full-team review pending)

## Context

Project writing was spread across the repo (`docs/`), a `Sharepoint/` folder
of Markdown, Word, and PDF files, and status notes inside guides. The guides
mixed procedures with one-off results, so they were hard to follow and went
stale. The proposal promises a failure catalogue, a diagnosis report,
before/after failure rates, and a final report of at least 15 pages, so
results need to be traceable to evidence.

Options considered: keep editing on SharePoint; keep two copies; or make Git
the single home for technical writing and use SharePoint only for submissions
and large files.

## Decision

All technical writing lives as Markdown in Git on the `project` branch,
organized by type: guides, reference, research, experiments, failures,
decisions, and status, as described in [docs/README.md](../README.md).
SharePoint holds course and admin files, PDFs as submitted, and large
artifacts. No document has two editable copies.

## Consequences

- Writing gets reviewed in pull requests and can link to exact commits and
  run IDs. Phase 4's plan to publish documentation needs no conversion.
- Teammates used to Word must convert drafts before merging
  (`pandoc -t gfm`).
- Evidence published from runs must be redacted, because the repository is
  public. `./tools/asahi evidence` does this.
- `tools/check-docs.py` enforces links, file names, and indexes, so the layout
  doesn't erode.
