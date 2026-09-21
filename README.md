# Asahi Linux Senior Design Project

[![Sync upstream kernel branches](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/actions/workflows/sync-upstream.yml/badge.svg?branch=project)](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/actions/workflows/sync-upstream.yml)

Senior design fork of [AsahiLinux/linux](https://github.com/AsahiLinux/linux), including the [fairydust branch](https://github.com/AsahiLinux/linux/tree/fairydust).

## Branches

| Branch | Purpose | Automatic updates |
| --- | --- | --- |
| [`main`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/tree/main) | Tracks `AsahiLinux/linux:main` | Daily |
| [`fairydust`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/tree/fairydust) | Tracks `AsahiLinux/linux:fairydust` | Daily |
| [`asahi`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/tree/asahi) | Tracks upstream's default branch, `AsahiLinux/linux:asahi` | Daily |
| `project` (default) | Project documentation and GitHub Actions configuration | Maintained by the team |

The default `project` branch has its own history and contains no kernel source. Select a kernel branch above to browse or build the kernel. Keeping automation on `project` lets the three tracked branches retain upstream's exact commits.

Put project notes and research in this branch. Create development branches from the appropriate kernel branch for code changes, for example `work/fairydust-usb`. Open code pull requests against the team's development branch, not the upstream-tracking branches or the documentation-only `project` branch.

## Daily upstream sync

The [sync workflow](.github/workflows/sync-upstream.yml) runs daily at **09:17 UTC** (5:17 a.m. Eastern Daylight Time / 4:17 a.m. Eastern Standard Time). It also runs when its workflow file changes on `project`, and can be run manually under **Actions -> Sync upstream kernel branches -> Run workflow**, using the `project` branch.

Each tracked branch is updated independently through GitHub's API with `force: false`. No kernel checkout or personal access token is needed; the workflow uses the repository's built-in `GITHUB_TOKEN` with `contents: write` permission.

- A branch advances only when the update is a fast-forward.
- If someone commits directly to a tracked branch, or upstream rebases/force-pushes it, its sync job fails without overwriting commits. The other branches are still processed.
- A deleted branch or an API/permissions error fails visibly; the workflow does not silently recreate or reset branches.
- Inspect failed jobs in Actions. Preserve any project commits on a development branch, inspect the upstream history, and choose a recovery before resetting a tracked branch. The workflow does not make that decision automatically.
- Changes on `project` and team development branches are never touched by this workflow. Merge or rebase upstream updates into your development branches deliberately.

Scheduled runs can be delayed by GitHub. GitHub also disables schedules in public repositories after **60 days without repository activity**; re-enable this workflow in Actions if that happens. Keep `project` as the default branch because scheduled workflows run from the default branch. See [GitHub's schedule documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Start kernel development

Use Linux, or a WSL2 Linux filesystem, for a kernel checkout and build. For work based on fairydust:

```sh
git clone --single-branch --branch fairydust \
  https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project.git
cd Asahi-Linux-Senior-Design-Project
git remote add upstream https://github.com/AsahiLinux/linux.git
git switch -c work/fairydust
git push -u origin work/fairydust
```

Substitute `asahi` or `main` for `fairydust` if that is the intended base. A single-branch clone avoids downloading every experimental upstream branch, but kernel history is still large.

To incorporate later fairydust updates into your development branch:

```sh
git fetch upstream fairydust
git switch work/fairydust
git merge FETCH_HEAD
```

Resolve any conflicts and test before pushing. Upstream history rewrites may require a deliberate rebase/cherry-pick instead of a merge.

## Edit project documentation

For a small checkout of the documentation and automation branch:

```sh
git clone --single-branch --branch project \
  https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project.git \
  Asahi-Linux-Senior-Design-Project-docs
```

This repository setup does not install a kernel build environment or verify a kernel build. Follow the build documentation on the selected kernel branch when setting up that environment.
