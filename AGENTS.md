# Instructions for AI coding assistants

This checkout is the `project` branch of the team's Asahi Linux fork. It holds
documentation, the WSL/m1n1 hypervisor (HV) test workflow, and its tests. It
contains **no kernel source**: kernel work happens in separate worktrees on
the test Mac and on `work/*` branches. The repository is **public**.

The controller is a Windows PC running Ubuntu on WSL2. The Mac is a separate
machine, reached over SSH for builds and over a USB-C cable (forwarded into
WSL by usbipd-win) for m1n1. PC paths and Mac paths are different namespaces.

## Repository map

| Path | What it is | Read it when |
| --- | --- | --- |
| [docs/README.md](docs/README.md) | Map of the docs and the rules for writing them | Before adding or moving any document |
| [docs/guides/kernel-workflow.md](docs/guides/kernel-workflow.md) | Setup, build, stage, HV boot | Before running any workflow command |
| [docs/guides/branch-hv-testing.md](docs/guides/branch-hv-testing.md) | Pinned branch builds and J413 USB-C/DP checks | Before testing a development branch |
| [docs/guides/recording-an-experiment.md](docs/guides/recording-an-experiment.md) | Turning a run into a report | After any hardware run |
| [docs/experiments/](docs/experiments/README.md) | Frozen reports with redacted evidence | To learn what has been tested |
| [docs/failures/](docs/failures/README.md) | Failure catalogue (`F-NNN`) | Before investigating a display bug |
| [docs/decisions/](docs/decisions/README.md) | Why things are done this way | Before changing a convention |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branches, pull requests, commit messages | Before committing |
| `tools/asahi` | Single entry point for the workflow; `./tools/asahi --help` | — |
| `tools/check-docs.py` | Documentation checks | Before finishing any docs change |
| `asahi.local.json`, `.asahi/` | Machine config and generated state (ignored) | Never commit |
| `~/Github/asahi-sdp-evidence` | Clone of the **private** evidence repository (free-text run logs) | When recording or reading run logs |

## Rules that always apply

- **Public repository.** This repo is a public fork and can't be made
  private. Never commit SSH keys, `asahi.local.json`, `.asahi/`, kernel
  images, initramfs files, ADT dumps, run logs, IP addresses, usernames,
  hostnames, UUIDs, or serial numbers. Publish run records only with
  `./tools/asahi evidence`, which keeps logs in the private evidence
  repository, then read the output before committing it. Don't quote log
  lines in public docs without checking them first.
- **Upstream AI policy.** Asahi Linux rejects contributions developed with
  LLM assistance; upstream PR #622 was closed for it (see
  [CONTRIBUTING.md](CONTRIBUTING.md#upstream-contributions-and-ai-tools)). Do
  not write or edit kernel code, commit messages, or cover letters for a
  patch meant for Asahi upstream. If asked to, say why and confirm with the
  user first. Workflow tools and documentation in this repository are fine.
- **Branches.** Never commit to `main`, `fairydust`, or `asahi`; the sync job
  owns them. Kernel changes never go on `project`.
- **m1n1** is an external dependency. Use it; don't modify it. The user has
  authorized AI assistance with m1n1 usage in this workflow.
- **Credentials.** Use the configured SSH identity. Never put passwords in
  commands, files, or chat.
- **Report only what evidence shows.** Don't claim an HV boot, driver, or
  display result from a normal SSH session, host-only tests, or a successful
  build. If something wasn't tested, say **NOT TESTED**.
- Routine development needs no extra approval beyond the user's existing
  authorization. These instructions don't add one.

## Running the workflow

All commands run in WSL from the repository root.

**Orient first.** Run `./tools/asahi doctor --online`. It shows HOME, the
project path, devices, SSH, and sudo. Then run `./tools/asahi bundles` to see
the selected bundle. Read the latest experiment report for current state.

**Build and stage a candidate** (Mac must be booted normally):

```bash
./tools/asahi build --source '~/kernel-WORKTREE' --profile j413-usbc-dp --dry-run
./tools/asahi build --source '~/kernel-WORKTREE' --profile j413-usbc-dp --jobs 4
./tools/asahi stage
./tools/asahi driver-check
```

- Quote remote `~` paths so WSL doesn't expand them.
- Use a fresh, unique release suffix for every staged build. Never overwrite
  an existing module release, and never change the Mac's normal boot entry.
- Read the instructions in the kernel source tree before editing it.
- Omit `--profile` and `driver-check` for experiments that don't involve
  USB-C/DP.

**Boot under HV.** Physical steps (powering the Mac, startup options, moving
cables) need the user. Ask them, and wait.

1. Check for an existing `asahi-hv` tmux session and stray picocom or
   primary-port clients. Only one process may own each serial port.
2. If a guest is running, shut it down cleanly
   (`./tools/asahi ssh -- sudo -n systemctl poweroff`) and confirm in
   `./tools/asahi logs`. Only then run `tmux kill-session -t asahi-hv`.
3. `./tools/asahi session start --wait 600`, then ask the user to boot the
   m1n1 proxy entry. For DP tests the proxy cable must be on **ATC0**
   ([decision 0002](docs/decisions/0002-proxy-on-atc0.md)); never ask anyone
   to move it while a guest runs.
4. `./tools/asahi check --wait 180`, then `./tools/asahi driver-check --live`
   for DP tests.

**Operate a live run** with `hv interrupt`, `hv command`, `hv resume`,
`hv show`, `logs`, and `ssh`. Wait for the HV prompt before sending commands.
Register writes, hooks, breakpoints, and `reboot` affect the real machine.
Never terminate the HV controller while a guest runs. Detaching from tmux is
fine.

**What `check` proves.** `check` passes only with the exact launch marker,
the expected release, the original root UUID, matching modules, and active
SSH. `check --running` is only a normal-boot baseline check.

**Tool code.** The HV launcher replaces its Python process (`exec`) before
running m1n1's helper, so Ctrl-C reaches only the HV shell. Preserve that.
After changing `tools/` or `tests/`, run:

```bash
uv run --no-project --python 3.13 --with pyserial==3.5 \
  python -m unittest discover -s tests -v
```

## Recording results

After any hardware run worth citing, follow
[Record an experiment](docs/guides/recording-an-experiment.md):

1. Copy `docs/templates/experiment.md` to
   `docs/experiments/YYYY-MM-DD-slug/README.md`, using the UTC date of the
   first run.
2. `./tools/asahi evidence docs/experiments/YYYY-MM-DD-slug/evidence --run-dir .asahi/runs/RUN_ID`
   for each run, then read the output for anything identifying. Commit and
   push the private logs with the `git` command it prints (pushing to the
   team's private repository is part of this routine). Link logs by their
   private URL and mark them *(private)*.
3. Fill in results with only **PASS**, **FAIL**, **NOT TESTED**, or
   **BLOCKED**, each marked **automated** or **manual**, each linking its
   evidence file. Things you observed in the HV shell or that the user told
   you are **manual**; say who observed them.
4. Update affected failure entries and `docs/failures/README.md`, and add the
   report to `docs/experiments/README.md`.

## Writing documentation

- Follow [docs/README.md](docs/README.md): put each document in the folder
  for its type, use lowercase kebab-case names, and start from
  `docs/templates/`.
- **Guides say how; reports say what happened.** Don't add results or
  machine status to a guide. When you change a command in a guide, rerun it
  and update its **Last verified** line.
- Never edit a merged experiment report, decision, or weekly status beyond a
  dated *Corrections* note. Write a new record instead.
- Add every new file to its folder's `README.md` index in the same change.
- Refer to hardware by inventory ID (`MAC-01`), not by owner or hostname.
- Write for teammates: plain sentences, no references to chats or sessions.
- Run `python3 tools/check-docs.py` before finishing.
