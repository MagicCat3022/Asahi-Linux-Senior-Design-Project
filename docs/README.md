# Documentation

This page is the map of `docs/` and the rules for adding to it.

The layout separates how-to guides, reference, and research notes, alongside
experiment reports, a failure catalogue, and the course deliverables.

## Start here

New to the project? Read [overview.md](overview.md): what we're building, how
the test setup works, and where things are kept.

| I want to… | Go to |
| --- | --- |
| Understand how the test setup works | [overview.md](overview.md) |
| Look up a word | [reference/glossary.md](reference/glossary.md) |
| Set up a Mac or a PC | [guides/set-up-the-test-mac.md](guides/set-up-the-test-mac.md), [guides/set-up-the-controller-pc.md](guides/set-up-the-controller-pc.md) |
| Build and boot a test kernel, including USB-C display tests | [guides/test-a-kernel.md](guides/test-a-kernel.md) |
| Write up a hardware run | [guides/recording-an-experiment.md](guides/recording-an-experiment.md) |
| Look up a command, setting, or error | [reference/asahi-tool.md](reference/asahi-tool.md) |
| See what has been tested | [experiments/](experiments/README.md) |
| See team-observed failures and their status | [failures/](failures/README.md) |
| Look up a machine, cable, or monitor ID | [reference/hardware.md](reference/hardware.md) |
| Understand the drivers and upstream state | [research/](research/README.md) |
| Track progress, tasks, and blockers | The team's Jira project |

## Where things live

| Location | What goes there |
| --- | --- |
| Jira | Project progress, tasks, plans, and blockers |
| Git, `project` branch | All technical writing: everything in `docs/`, plus LaTeX sources in `deliverables/` |
| Kernel branches (`usb/dev` and subsystem/topic branches) | Kernel code, commit messages, patch cover letters |
| Private repo [`asahi-sdp-evidence`](https://github.com/MagicCat3022/asahi-sdp-evidence) | Run logs and exact build inputs, linked by commit from experiment reports; team only ([recording guide](guides/recording-an-experiment.md)) |
| `.asahi/` on each controller PC (ignored by Git) | Raw tool output: runs, bundles, build records |
| SharePoint | Course and admin files, PDFs exactly as submitted, large binaries |

**One editable home per document.** SharePoint gets an exported PDF or a link
back to the repo, never a second copy that people edit.

## Layout

```text
docs/
  README.md        this page
  overview.md      how the project and test setup work; read first
  guides/          how to do something; kept current
  reference/       facts to look up: glossary, tool, kernel config, hardware, branches, links
  research/        how the code and hardware work; dated
  experiments/     one folder per hardware run we cite; frozen
    YYYY-MM-DD-slug/
      README.md    the report
      evidence/    redacted structured records and logs.md links, one folder per run ID
  failures/        team-observed failures, one file per failure class
  templates/       copy these to start a new document
deliverables/      LaTeX sources for course reports
```

Every folder has a `README.md` that indexes it. When you add a file, add it
to that index in the same commit.

## Document types

| Type | Folder | After it's written | File name | Template |
| --- | --- | --- | --- | --- |
| Guide | `guides/` | Edit in place; keep it correct | `test-a-kernel.md` | header and shape in [guides/README.md](guides/README.md#writing-a-guide) |
| Reference | `reference/` | Edit in place | `hardware.md` | none |
| Research note | `research/` | Update, or point to what replaced it | `fairydust-status.md` | none |
| Experiment report | `experiments/` | Frozen; corrections go in a dated *Corrections* section | `2026-10-14-tipd-oob-fixes/` | [experiment.md](templates/experiment.md) |
| Failure entry | `failures/` | Living; update its status | `F-NNN-slug.md` | [failure.md](templates/failure.md) |

**Guides say how; reports say what happened.** Results never go in a guide,
and a report doesn't repeat procedures. It links to the guide and the project
commit it followed.

## Conventions

`tools/check-docs.py` enforces the first three; the rest are on you.

- **File names:** lowercase kebab-case, with no spaces, `&`, or capitals.
  The exceptions are `README.md` and failure IDs (`F-001-…`).
- **Indexes:** every experiment and failure entry is listed in its folder's
  `README.md`.
- **Links:** relative links and anchors resolve, and private evidence links
  are pinned to a commit (`evidence --finalize` writes them).
- **Dates:** ISO (`2026-10-14`). Experiment folders use the UTC date of their
  first run, matching the run IDs.
- **Hardware:** refer to it by ID from
  [reference/hardware.md](reference/hardware.md), e.g. `MAC-01`, `MON-02`.
- **Results:** use only **PASS**, **FAIL**, **NOT TESTED**, or **BLOCKED**, and
  mark each as **automated** (a tool performed the check) or **manual** (a
  person observed it). Repeated tests give a rate: "FAIL 3/10".
- **Writing:** short sentences, plain words, and a diagram wherever a picture
  is clearer than a paragraph. Define terms in the
  [glossary](reference/glossary.md). Markdown only, one `#` heading per file;
  to convert a Word draft, use `pandoc -t gfm --wrap=none -o out.md in.docx`.
- **Public repository:** publish run records only with `./tools/asahi
  evidence`, and read what it writes. Never commit binaries, keys, IP
  addresses, or serial numbers. As a fork, this repository can't be made
  private.

## Checks

CI runs these on every pull request to `project`; run them first:

```bash
python3 tools/check-docs.py
python3 -m unittest discover -s tests
```

`check-docs.py` checks links and heading anchors, file names, **Last
verified** lines in guides, leftover `FILL IN` markers in reports, finalized
private evidence, and the experiment and failure indexes.

## SharePoint

```text
00 README                     link to the GitHub repo and this page
01 Course and admin/          syllabus, rubrics, advisor material, meeting minutes if required
02 Submitted deliverables/    PDFs as submitted, YYYY-MM-DD-name.pdf
03 Large artifacts/<run-id>/  binaries or big logs referenced by an experiment report
```

Nothing on SharePoint is a working copy of something in Git. How to submit a
deliverable is described in [deliverables/README.md](../deliverables/README.md).
