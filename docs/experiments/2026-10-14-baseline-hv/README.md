# 2026-10-14: Installed baseline kernel under m1n1 HV

**Author:** Mustafa Maras · **Runs:** `20261013T235111448825Z`, `20261014T013041090133Z`,
`20261014T014030194466Z` · **Status:** final

Links marked *(private)* go to the team's private evidence repository; see
[Record an experiment](../../guides/recording-an-experiment.md#3-copy-the-evidence).

## Goal

Set up the workflow and check that the Mac's installed kernel boots under the
m1n1 hypervisor with its normal root filesystem, before testing any modified
kernel. Also check whether the USB-C/DP drivers are ready with the proxy cable
on the front port.

## Inputs

| Input | Value |
| --- | --- |
| Kernel | Installed `7.1.13-fairydust+` (source commit not recorded by the installed kernel) |
| Config | `/boot/config-7.1.13-fairydust+`, SHA-256 `81e3ad71bcf015e2c3cc08856c31410e5fcb6a6f93b60114e2792c265b5e0684` |
| Driver profile | none for the boot; `j413-usbc-dp` for the driver checks |
| m1n1 commit | `ce2b8a43cea4220b602af1005dc9dbfc59c9624e` |
| Guide followed | [kernel workflow](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/blob/07324248e65a99e39b99240519058a00db5ebf7c/docs/KERNEL_WORKFLOW.md) as of project commit `07324248e65a` |
| Exact inputs (private) | `kernel.config` for each run, linked from its `logs.md`; source and workflow snapshots weren't captured |
| Hardware | `MAC-01`; proxy cable on **ATC1** (front port, iodev 5); `PC-01`; no external display |

## Procedure

Followed the guide's one-time setup and "First hardware test". Run
`20261013T235111448825Z` is a normal-boot `check --running`. Run
`20261014T013041090133Z` was the first HV attempt. Run
`20261014T014030194466Z` booted the baseline under HV; the HV
interrupt/inspect/resume test and the two driver checks were done during it.

The workflow's first native build was also checked during this session (not a
boot test): build record `20261014T005646` failed the kernel's Rust support
check, and `20261014T005806` built release
`7.1.13-fairydust-sdp-20261014t005806894561z` (5,805 modules) from
`ce9f2eba72c061a50b2d790450e90af3439d8c24` and staged it. Those build logs stay
local in `.asahi/builds/`.

## Results

| Check | Result | How | Evidence |
| --- | --- | --- | --- |
| Normal boot: release, root, modules, SSH, sudo | PASS | automated | [check.json](evidence/20261013T235111448825Z/check.json) |
| First HV attempt | FAIL: chainloader stopped; host `aarch64-linux-gnu-gcc` missing | automated | [hv.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/23a591e8074eeb0e4f779724dc350d549bcd278e/2026-10-14-baseline-hv/20261014T013041090133Z/hv.log) *(private)*, [adt-repair.json](evidence/20261014T013041090133Z/adt-repair.json) |
| HV boot: exact run marker, release, root UUID, modules, SSH | PASS | automated | [check.json](evidence/20261014T014030194466Z/check.json) |
| HV interrupt, `ctx`, resume; SSH after resume | PASS | manual | [control-check.json](evidence/20261014T014030194466Z/control-check.json) |
| Graphical target and display manager active; no failed units | PASS | manual | [control-check.json](evidence/20261014T014030194466Z/control-check.json), [guest-health.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/23a591e8074eeb0e4f779724dc350d549bcd278e/2026-10-14-baseline-hv/20261014T014030194466Z/guest-health.log) *(private)* |
| USB-C/DP driver readiness, proxy on ATC1 (first check) | FAIL: profile expected module `i2c-apple`, but `CONFIG_I2C_APPLE` builds `i2c-pasemi-platform`; front PHY unbound | automated | [driver-check 031544](evidence/20261014T014030194466Z/driver-check-20261014T031544041901Z.json) |
| USB-C/DP driver readiness, proxy on ATC1 (corrected profile) | FAIL: front PHY and external DCP unbound; DCP deferred | automated | [driver-check 031828](evidence/20261014T014030194466Z/driver-check-20261014T031828184009Z.json) |
| Native build and staging leave installed boot files unchanged | PASS | automated | local build/stage records |
| External display output | NOT TESTED | — | no external display |

## Observations

- With the proxy on ATC1, m1n1 logged `Initializing hypervisor over iodev 5`
  ([hv.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/23a591e8074eeb0e4f779724dc350d549bcd278e/2026-10-14-baseline-hv/20261014T014030194466Z/hv.log) *(private)*, line 120) and removed
  `atc-phy1` from the guest. The DCP driver then logged
  `apple-dcp 271c00000.dcp: Failed to get dp-phy: -517` repeatedly
  ([guest-health.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/23a591e8074eeb0e4f779724dc350d549bcd278e/2026-10-14-baseline-hv/20261014T014030194466Z/guest-health.log) *(private)*).
  `-517` is `-EPROBE_DEFER`: DCP waits forever for a PHY it can't have.
- The baseline initramfs (about 45 MiB) fits m1n1's default 128 MiB upload
  heap.
- Run `014030` ended with a clean power-off (`reboot: Power down` in
  [serial.log](https://github.com/MagicCat3022/asahi-sdp-evidence/blob/23a591e8074eeb0e4f779724dc350d549bcd278e/2026-10-14-baseline-hv/20261014T014030194466Z/serial.log) *(private)*), after which the HV
  controller exited with a serial `SerialException`. That is the expected end
  of a run; see [Shut down](../../guides/test-a-kernel.md#5-shut-down).

## Conclusion

The workflow boots the installed kernel under HV with the original root, and
the identity check can tell an HV boot from a normal one. The proxy can't
share the port that fairydust uses for DP on J413, so DP tests need the proxy
on ATC0; see [port setup](../../guides/test-a-kernel.md#use-the-right-usb-c-port).

Tool changes that came out of this session: a host toolchain preflight before
the target is touched (from the first HV attempt), a Rust support preflight
before reconfiguring (from the first build), and the profile's I²C module name
corrected to `i2c-pasemi-platform`.

## Next steps

- Build and test a candidate with the proxy on ATC0:
  [2026-10-14-tipd-oob-fixes](../2026-10-14-tipd-oob-fixes/).

## Corrections

None.
