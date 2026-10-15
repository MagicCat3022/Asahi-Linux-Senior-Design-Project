# 0004: Free-text run logs in a private evidence repository

**Date:** 2026-10-14 · **Status:** accepted · **Deciders:** Mustafa Maras (full-team review pending)

## Context

Experiment reports need evidence, but this repository is a public fork of
AsahiLinux/linux, and GitHub doesn't allow forks of public repositories to be
private. The first published run logs contained the Mac's hardware serial
number, hostname, Mac username, machine ID, and partition UUIDs. Automatic
redaction removed them. Structured records have known fields, so redacting
them is reliable. Free-text logs are where an identifier nobody knew to look
for would slip through, and they were about 594 KB of the 640 KB of evidence.

Options considered: publish everything redacted; keep logs only on the PC that
ran the test; keep them on SharePoint; encrypt them inside the public
repository; or keep them in a separate private GitHub repository, linked by
plain URLs or as a submodule.

## Decision

Free-text logs go to the private repository
[`MagicCat3022/asahi-sdp-evidence`](https://github.com/MagicCat3022/asahi-sdp-evidence),
using the same `SLUG/RUN_ID/` paths as the public evidence folders. Public
reports link to them with plain URLs marked *(private)*. `./tools/asahi
evidence` does the split and still redacts the private copies. No submodule.

## Consequences

- Public readers see the reports and structured records, but get GitHub's 404
  page for log links.
- Teammates and the advisor need collaborator access, and each person clones
  the private repository next to this one.
- Recording an experiment involves two pushes, and the private one must
  happen first so the links work.
- Links point at `main`, not a pinned commit. Don't rewrite or move files in
  the private repository's history.
- The private repository is owned by one personal account. Move it to a team
  organization if ownership needs to outlive that account.
