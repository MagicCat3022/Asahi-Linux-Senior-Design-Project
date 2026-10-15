# 2026-10-14: tipd-oob-fixes candidate under m1n1 HV

**Author:** Mustafa Maras · **Runs:** `20261014T033657656493Z`, `20261014T034242260652Z`,
`20261014T035050128076Z` · **Status:** final (reconstructed from run records
on 2026-10-14)

Links marked *(private)* go to the team's private evidence repository; see
[Record an experiment](../../guides/recording-an-experiment.md#3-copy-the-evidence).

## Goal

Check that the `tipd-oob-fixes` branch builds, boots under the m1n1 HV, and
brings up the whole USB-C/DP driver stack on the front port (ATC1), so it is
ready for hot-plug testing with a monitor. Related failures:
[F-002](../../failures/F-002-cd321x-no-dp-after-usb-failure.md) (same driver).

## Inputs

| Input | Value |
| --- | --- |
| Kernel commit | `301e2ba4004a33f7c808489dc1b5951e41c5c09b` (branch `tipd-oob-fixes`) |
| Base | `ce9f2eba72c061a50b2d790450e90af3439d8c24`, the fairydust tip on 2026-10-14 |
| Changes | Two commits in `drivers/usb/typec/tipd/core.c`: release the connector fwnode on unregister; forward only debounced HPD edges to DRM with a consistent data-role snapshot |
| Kernel release | `7.1.13-fairydust-sdp-tipd-301e2ba4-20261014a` |
| Config | Baseline config after `olddefconfig`, SHA-256 `559193b6c3aa155eb329fe4c9796b335006dc918ae0ecc4051c09fe5ef58caf3` |
| Driver profile | `j413-usbc-dp` |
| Toolchain | Clang/LLD 22.1.8, rustc 1.99.0, bindgen 0.72.1, pahole 1.32, Fedora 44 |
| m1n1 commit | `ce2b8a43cea4220b602af1005dc9dbfc59c9624e` |
| Guide followed | [branch testing guide](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/blob/07324248e65a99e39b99240519058a00db5ebf7c/docs/BRANCH_HV_TESTING.md) as of project commit `07324248e65a` |
| Hardware | `MAC-01`; proxy on ATC1 for the first run, **ATC0** (iodev 4) for the others; `PC-01`; no external display |

## Procedure

Followed the guide. One deviation: an initial full build (record
`20261014T031324`) was stopped. To save time, the final build's outputs were
seeded from the compiled, clean parent checkout. `.git`, `.config`, and the
changed `core.c` were excluded from the copy, both checkouts were locked, and
the protected file hash was checked before and after. Kbuild then rebuilt
what the branch changed. The full-build procedure works without this
shortcut.

## Results

| Check | Result | How | Evidence |
| --- | --- | --- | --- |
| Build and stage: 5,805 modules; all 11 profile modules in the initramfs | PASS | automated | [build.json](evidence/20261014T035050128076Z/build.json); local stage record |
| Pre-boot module check: `vermagic` and dependencies | PASS | automated | [driver-check 033612](evidence/20261014T033657656493Z/driver-check-20261014T033612146432Z.json) |
| HV boot, proxy on ATC1, default 128 MiB upload heap | FAIL: `Exception: Out of memory` loading the 183 MiB initramfs | automated | [hv.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/main/2026-10-14-tipd-oob-fixes/20261014T033657656493Z/hv.log) *(private)*, line 277 |
| HV boot, proxy on ATC0, 512 MiB heap: run marker, release, root, modules, SSH | PASS | automated | [check.json](evidence/20261014T034242260652Z/check.json) |
| Live DP driver readiness (same run) | PASS | automated | [driver-check 034500](evidence/20261014T034242260652Z/driver-check-20261014T034500010230Z.json) |
| HV interrupt keeps the controller alive (same run) | FAIL: Ctrl-C also stopped the launcher; exit code 130 | automated | [boot.json](evidence/20261014T034242260652Z/boot.json), [hv.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/main/2026-10-14-tipd-oob-fixes/20261014T034242260652Z/hv.log) *(private)* |
| Final run with fixed launcher: run marker, release, root, modules, SSH | PASS | automated | [check.json](evidence/20261014T035050128076Z/check.json) |
| Final run: front PHY, crossbar, external DCP, display subsystem bound; no deferred devices; `DP-1` disconnected; `eDP-1` 2560x1600 | PASS | automated | [driver-check 035323](evidence/20261014T035050128076Z/driver-check-20261014T035323279519Z.json) |
| Final run: HV interrupt, `ctx`, resume; SSH after resume; controller alive | PASS | manual | [control-check.json](evidence/20261014T035050128076Z/control-check.json) |
| External display output, hot-plug, link training | NOT TESTED | — | no external display connected |

## Observations

- The candidate initramfs is 191,977,784 bytes (183 MiB). m1n1's
  `run_guest.py` reserves a 128 MiB upload heap, hence the out-of-memory
  failure. The launcher now raises the heap through `hv_heap_mib` (512 MiB
  here) without modifying m1n1.
- With the proxy on ATC0, m1n1 reports `Proxy transport: iodev 4` and
  `Initializing hypervisor over iodev 4` and removes `atc-phy0`, leaving
  `atcphy1` to Linux for DP. Compare the baseline experiment's `-517`
  deferral on ATC1.
- In run `034242`, interrupting the HV shell also stopped the waiting Python
  launcher. The launcher now replaces itself with the m1n1 helper (`exec`),
  and run `035050` kept the controller alive through interrupt and resume.
- The final controller later exited with a serial `SerialException` (the USB
  device went away). Its serial log ends at the login prompt with no shutdown
  recorded, so how that run ended isn't documented.

## Conclusion

The candidate boots under HV, and every driver the J413 DP path needs binds on
ATC1 with nothing deferred. It is ready for hot-plug tests. Nothing here shows
visible external output, hot-plug behavior, or link training, and nothing
here confirms or rules out any failure entry.

## Next steps

- Connect a monitor to ATC1 and run the
  [display hot-plug tests](../../guides/test-a-kernel.md#display-hot-plug-tests), recording
  hardware IDs from [the inventory](../../reference/hardware.md).
- Run the same hot-plug procedure on the unmodified baseline for a comparison
  rate.

## Corrections

- 2026-10-14: the original guide gave the initramfs size as 184 MiB; it is
  191,977,784 bytes (183 MiB).
