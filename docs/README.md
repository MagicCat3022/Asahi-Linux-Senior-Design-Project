# Documentation

This page is the map of `docs/` and the rules for adding to it. The layout was
adopted on 2026-10-14; the reasoning is in
[decision 0001](decisions/0001-documentation-layout.md).

The layout borrows from two common patterns: [Diátaxis](https://diataxis.fr/)
(keep how-to guides, reference, and explanation apart) and
[architecture decision records](https://adr.github.io/) (short, numbered,
never-edited records of why we chose something). On top of those it adds the
records our proposal promises: experiment reports, a failure catalogue, and
the course deliverables.

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
| See known failures and their status | [failures/](failures/README.md) |
| Know why something is done a certain way | [decisions/](decisions/README.md) |
| Look up a machine, cable, or monitor ID | [reference/hardware.md](reference/hardware.md) |
| Understand the drivers and upstream state | [research/](research/README.md) |
| Catch up on the week | [status/](status/README.md) |

## Where things live

| Location | What goes there |
| --- | --- |
| Git, `project` branch | All technical writing: everything in `docs/`, plus LaTeX sources in `deliverables/` |
| Kernel branches (`work/*`) | Kernel code, commit messages, patch cover letters |
| Private repo [`asahi-sdp-evidence`](https://github.com/MagicCat3022/asahi-sdp-evidence) | Free-text run logs, linked from experiment reports; team only ([decision 0004](decisions/0004-private-evidence-repository.md)) |
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
  failures/        failure catalogue, one file per failure class
  decisions/       numbered decision records; frozen
  status/          weekly status, YYYY-Www.md; frozen
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
| Failure entry | `failures/` | Living; update its status | `F-001-dcp-false-crash-on-poweroff.md` | [failure.md](templates/failure.md) |
| Decision | `decisions/` | Frozen; replace with a new record | `0002-proxy-on-atc0.md` | [decision.md](templates/decision.md) |
| Weekly status | `status/` | Frozen | `2026-W42.md` | [status.md](templates/status.md) |

**Guides say how; reports say what happened.** Results never go in a guide,
and a report doesn't repeat procedures. It links to the guide and the project
commit it followed.

## Conventions

- **File names:** lowercase kebab-case, with no spaces, `&`, or capitals.
  The exceptions are `README.md`, failure IDs (`F-001-…`), and ISO weeks
  (`2026-W42.md`).
- **Dates:** ISO (`2026-10-14`). Experiment folders use the UTC date of their
  first run, matching the run IDs.
- **Commits:** full 40-character hashes in records; short hashes are fine in
  prose.
- **Hardware:** refer to it by ID from
  [reference/hardware.md](reference/hardware.md), e.g. `MAC-01`, `MON-02`.
- **Results:** use only **PASS**, **FAIL**, **NOT TESTED**, or **BLOCKED**, and
  mark each as **automated** (a tool wrote the evidence) or **manual** (a
  person observed it). Repeated tests give a rate: "FAIL 3/10".
- **Writing:** short sentences, plain words, and a diagram wherever a picture
  is clearer than a paragraph. Define a term in the
  [glossary](reference/glossary.md) rather than in every document.
- **Format:** Markdown, one `#` heading per file, diagrams in Mermaid or a
  committed SVG. Draft in Word or Google Docs if you like, but convert before
  merging: `pandoc -t gfm --wrap=none -o out.md in.docx`.
- **Evidence:** only what `./tools/asahi evidence` produces, or other text
  you have read. Full logs go to the private evidence repository, never here.
  Never commit binaries, keys, IP addresses, or serial numbers. This
  repository is public, and as a fork it can't be made private.

## Checks

Run before every pull request:

```bash
python3 tools/check-docs.py
```

It checks links and heading anchors, file names, **Last verified** lines in
guides, and that every experiment and failure entry appears in its index.
Pull requests that touch `tools/` also run the test suite; see
[CONTRIBUTING.md](../CONTRIBUTING.md).

## SharePoint

```text
00 README                     link to the GitHub repo and this page
01 Course and admin/          syllabus, rubrics, advisor material, meeting minutes if required
02 Submitted deliverables/    PDFs as submitted, YYYY-MM-DD-name.pdf
03 Large artifacts/<run-id>/  binaries or big logs referenced by an experiment report
```

Nothing on SharePoint is a working copy of something in Git. How to submit a
deliverable is described in [deliverables/README.md](../deliverables/README.md).

## Where the old files went

| Before 2026-10-14 | Now |
| --- | --- |
| `docs/KERNEL_WORKFLOW.md` | Split into [overview.md](overview.md), [guides/set-up-the-test-mac.md](guides/set-up-the-test-mac.md), [guides/set-up-the-controller-pc.md](guides/set-up-the-controller-pc.md), [guides/test-a-kernel.md](guides/test-a-kernel.md), [reference/asahi-tool.md](reference/asahi-tool.md), and [reference/kernel-config.md](reference/kernel-config.md); its status section moved to [experiments/2026-10-14-baseline-hv](experiments/2026-10-14-baseline-hv/) |
| `docs/BRANCH_HV_TESTING.md` | Merged into [guides/test-a-kernel.md](guides/test-a-kernel.md); its results moved to [experiments/2026-10-14-tipd-oob-fixes](experiments/2026-10-14-tipd-oob-fixes/) |
| `README.md` sections on branches and the sync | [reference/branches-and-sync.md](reference/branches-and-sync.md) |
| `Sharepoint/KERNEL_DEV.md` | [guides/x86-cross-build-qemu.md](guides/x86-cross-build-qemu.md) |
| `Sharepoint/m1n1_Paper.md` | [research/m1n1-overview.md](research/m1n1-overview.md) |
| `Sharepoint/Overview of atc.c, core.c.md` | [research/atc-phy-and-tipd-overview.md](research/atc-phy-and-tipd-overview.md) |
| `Sharepoint/USB-C-Display.md` | [research/usb-c-display-commits.md](research/usb-c-display-commits.md) |
| `Sharepoint/Asahi USB Reports Notes.md` | [research/asahi-progress-report-notes.md](research/asahi-progress-report-notes.md) |
| `Sharepoint/Leads.md` | [reference/links.md](reference/links.md) |
| `Sharepoint/Fairydust Research & Current Status.docx` | [research/fairydust-status.md](research/fairydust-status.md) and [failures/](failures/README.md) |
| `Sharepoint/main.pdf` | [deliverables/proposal/](../deliverables/proposal/) |

The originals are in commit `07324248e65a`.

## Open items

- Confirm whether the course requires anything specific on SharePoint
  (meeting minutes, formats, folder names), and adjust the layout above.
- Add the proposal's LaTeX source, or a link to it, in
  [deliverables/proposal/](../deliverables/proposal/).
- Decide who maintains the failure catalogue index and the hardware inventory.
