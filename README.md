# Asahi Linux Senior Design Project

[![Sync upstream kernel branches](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/actions/workflows/sync-upstream.yml/badge.svg?branch=project)](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/actions/workflows/sync-upstream.yml)

A UConn senior design project to improve USB-C DisplayPort support on M1 and
M2 Macs in [Asahi Linux](https://asahilinux.org/). We change the kernel's
USB-C and display drivers in Asahi's `fairydust` branch, test them on real
Macs, and record the results. See the [proposal](deliverables/proposal/).

## Start here

1. **[How it works](docs/overview.md):** the project, the test setup, and the
   words we use. Read this first.
2. **Set up:** [the test Mac](docs/guides/set-up-the-test-mac.md), then
   [the controller PC](docs/guides/set-up-the-controller-pc.md).
3. **Every test:** [Test a kernel](docs/guides/test-a-kernel.md), then
   [Record an experiment](docs/guides/recording-an-experiment.md).

Everything else, including results and known failures, is listed
in [docs/](docs/README.md).

```sh
./tools/asahi status    # where things stand and what to do next
./tools/asahi --help    # every command, grouped by step
```

## What's in this branch

This is the `project` branch: docs and tools only, with no kernel source.

| Path | Contents |
| --- | --- |
| [docs/](docs/README.md) | Guides, reference, research, experiment reports, failures |
| [tools/](tools/), [tests/](tests/) | `./tools/asahi`, the build-and-test tool, and its tests |
| [deliverables/](deliverables/README.md) | Course reports |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branches, pull requests, commit messages |
| [AGENTS.md](AGENTS.md) | Instructions for AI coding assistants |

Kernel code lives on the `fairydust`, `asahi`, and `main` branches (daily
copies of upstream), our shared `usb/dev` branch, and subsystem/topic branches
such as `usb/tipd-hpd-fix`. Kernel pull requests target `usb/dev`. See
[Branches and the upstream sync](docs/reference/branches-and-sync.md).

To check out only this branch:

```sh
git clone --single-branch --branch project \
  https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project.git
```
