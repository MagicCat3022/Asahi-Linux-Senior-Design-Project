# Record an experiment

**Applies to:** any hardware run made with `./tools/asahi` ·
**Last verified:** 2026-10-14, by rebuilding the two existing experiment reports

Every hardware run you might cite later, whether it passed or failed, becomes
an experiment report. The reports are the raw material for the failure
catalogue, the before/after failure rates, and the final report.

## Where evidence goes

This repository is public and, as a fork, can't be made private. So evidence
is split ([decision 0004](../decisions/0004-private-evidence-repository.md)):

| Evidence | Where | Why |
| --- | --- | --- |
| Reports and structured records (`boot.json`, `check.json`, driver checks, build summary) | This repository, `docs/experiments/SLUG/evidence/RUN_ID/` | Known fields, so redaction is reliable |
| Free-text logs (`serial.log`, `hv.log`, `guest-health.log`) | Private repository [`MagicCat3022/asahi-sdp-evidence`](https://github.com/MagicCat3022/asahi-sdp-evidence), `SLUG/RUN_ID/` | Logs can contain identifiers nobody knew to look for |
| Binaries (kernel images, initramfs, ADT dumps) | Nowhere, or SharePoint `03 Large artifacts/RUN_ID/` if a teammate needs one | Large, and recreatable from the build record |

## One-time setup

Ask the repository owner to add you as a collaborator on
`asahi-sdp-evidence`, then clone it next to this checkout:

```bash
git clone https://github.com/MagicCat3022/asahi-sdp-evidence.git ~/Github/asahi-sdp-evidence
```

Check that `asahi.local.json` has these settings (`./tools/asahi init` adds
them; for an older config, add them by hand):

```json
"private_evidence_dir": "~/Github/asahi-sdp-evidence",
"private_evidence_url": "https://github.com/MagicCat3022/asahi-sdp-evidence"
```

## 1. Before the run

Pick a short slug and today's UTC date (the date in the run IDs), then copy
the template:

```bash
mkdir -p docs/experiments/2026-10-21-hotplug-baseline
cp docs/templates/experiment.md docs/experiments/2026-10-21-hotplug-baseline/README.md
```

Fill in **Goal** and **Inputs** now, while you know them: kernel commit,
config hash, driver profile, m1n1 commit, the guide you're following, and
hardware IDs from [the inventory](../reference/hardware.md). Add any new
cable, monitor, or adapter to the inventory first.

## 2. Run it

Follow the relevant guide. While it runs, note anything physical the tools
can't see, such as "unplugged `CAB-02` at about 14:05, replugged 15 s later",
and what you saw on screen. These become **manual** results.

## 3. Copy the evidence

For each run that belongs to the experiment:

```bash
git -C ~/Github/asahi-sdp-evidence pull
./tools/asahi evidence docs/experiments/2026-10-21-hotplug-baseline/evidence \
  --run-dir .asahi/runs/RUN_ID
```

Without `--run-dir` it uses the latest run. The command:

- writes the run's JSON records, the same-kernel `driver-check` reports taken
  during the run, and a build summary to `evidence/RUN_ID/` in this
  repository;
- writes the run's logs to `~/Github/asahi-sdp-evidence/2026-10-21-hotplug-baseline/RUN_ID/`;
- writes `evidence/RUN_ID/logs.md`, linking each private log;
- prints the `git` command that commits and pushes the private logs. Run it,
  so the links work for your teammates.

Add a report taken before the boot with
`--driver-check .asahi/driver-checks/FILE.json`. If you don't have the private
repository, `--skip-logs` publishes only the structured records.

Everything is redacted, private logs included, in case a file is ever moved
or quoted. The command replaces home and project paths, the Mac's user and
hostname, device serial numbers, UUIDs, machine IDs, and MAC addresses. The
same value always gets the same placeholder, such as `<root-uuid>` or
`<uuid-2>`, so records still line up. Then check the public part for anything
it couldn't know about:

```bash
grep -rniE "password|token|ssid|@" docs/experiments/2026-10-21-hotplug-baseline/evidence | less
```

In the report, link logs by their private URL and mark them *(private)*.
Quote the few lines that matter directly in the report's **Observations**;
quoted lines are public, so read them first.

## 4. Write the results

Fill in **Results** with one row per check. Use only **PASS**, **FAIL**,
**NOT TESTED**, or **BLOCKED**. Mark each row **automated** (a tool wrote the
evidence file) or **manual** (a person observed it), and link the evidence
file. List what you didn't test as clearly as what passed.

For repeated tests, give the rate: "FAIL 3/10".

## 5. Update the failure catalogue

If the run reproduced, ruled out, or helped explain a failure:

- add a row to that entry's **Evidence** table;
- change its **Status** if warranted (for example `upstream-reported` →
  `reproduced`), with a line in its **History**;
- update the table in [failures/README.md](../failures/README.md).

If you found a new failure, copy [the failure template](../templates/failure.md)
to the next free `F-NNN`.

## 6. Index and submit

Make sure the private logs are pushed, add a row to
[experiments/README.md](../experiments/README.md), run the checks, and open a
pull request to `project` within a week of the run:

```bash
python3 tools/check-docs.py
```

After the report is merged it is frozen. If you later find a mistake, add a
dated line under **Corrections** instead of editing the results.
