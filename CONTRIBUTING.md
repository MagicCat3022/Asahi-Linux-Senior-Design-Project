# Contributing

## Branches

| Branch | What goes on it | How it changes |
| --- | --- | --- |
| `project` (default) | Documentation, workflow tools, tests, GitHub Actions | Pull requests only |
| `main`, `fairydust`, `asahi` | Exact copies of upstream branches | The daily sync job only; never commit to them |
| `usb/dev` | Shared USB-C and display development, initially branched from `fairydust` | Kernel pull requests |
| `<subsystem>/<topic>` | Kernel changes, for example `usb/tipd-hpd-fix` or `drm/dcp-hotplug` | Owned by whoever creates it |

The daily sync allows forced updates so the three upstream copies match even
after upstream rewrites history. Any commits made directly on them will be
discarded; branch kernel topics from `usb/dev` and target pull requests there.
Use Linux-style subsystem/topic names, with a short lowercase topic and
hyphens between words. See [branches and sync](docs/reference/branches-and-sync.md)
for the concurrency guard and how local clones handle rewritten history.

For documentation or tool changes, branch from `project`
(`git switch -c docs/hotplug-report project`) and open a pull request back to
`project`. Kernel code never goes on `project`; experiment reports link to it
by commit.

## Pull requests

1. Run the checks. CI runs the same ones on every pull request to `project`:

   ```bash
   python3 tools/check-docs.py
   python3 -m unittest discover -s tests
   ```

2. Fill in the pull request template.
3. Get one teammate's approval, then merge.

## Documentation

[docs/README.md](docs/README.md) says where each kind of document goes, how
to name it, and which template to start from. The short version:

- **Guides** say how to do something and are kept current.
- **Experiment reports** say what happened on a run and are frozen.
- **Jira** holds project progress, tasks, plans, and blockers.
- Failures go in the **failure catalogue**.
- The repository is **public**. Publish run records only through
  `./tools/asahi evidence`, which sends logs to the private
  [`asahi-sdp-evidence`](https://github.com/MagicCat3022/asahi-sdp-evidence)
  repository; ask the owner for access.

## Commit messages

- Subject: imperative, at most about 72 characters ("Add hot-plug report
  for baseline", not "added stuff").
- Body: why the change was made, and what someone reviewing it should know.
- Kernel commits follow kernel conventions: a subsystem prefix
  (`usb: typec: tipd: …`), a `Signed-off-by:` line for anything that may go
  upstream, and `./scripts/checkpatch.pl --strict` before review.

## Upstream contributions and AI tools

Asahi Linux closed upstream PR
[#622](https://github.com/AsahiLinux/linux/pull/622) on 2026-09-14 because
it was "developed with LLM assistance … which the Asahi Generative AI Policy
forbids". Read the [policy](https://asahilinux.org/slop) before starting any
patch you hope to send upstream. Keep AI tools away from that patch's code,
commit messages, and cover letter unless the policy clearly allows it.

Using AI assistants for this repository's tools and documentation is the
team's choice. Label AI-assisted commits honestly, for example with a
`Co-Authored-By:` or `Assisted-by:` trailer.
