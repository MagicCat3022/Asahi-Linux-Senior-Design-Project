# Test a development branch under m1n1 HV

This procedure builds a pinned branch revision natively on the Mac, installs
its uniquely named modules, and boots its kernel/DTB/initramfs through the WSL
controller. Follow [KERNEL_WORKFLOW.md](KERNEL_WORKFLOW.md) first for machine
setup, dependencies, SSH, USB forwarding, and the baseline capture. The normal
Asahi boot files remain the recovery path.

## 1. Fetch and pin the branch on the Mac

Open the Mac shell from the SDP `project` checkout **in WSL**:

```bash
./tools/asahi ssh
```

Run **on the Mac**:

```bash
cd ~/linux-fairydust
branch=tipd-oob-fixes
repo=https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project.git
git fetch --no-tags "$repo" "refs/heads/$branch:refs/remotes/sdp/$branch"
commit=$(git rev-parse "refs/remotes/sdp/$branch^{commit}")
git log -3 --oneline "$commit"
git diff --stat HEAD.."$commit"
git worktree add --detach ~/kernel-tipd-oob-fixes "$commit"
cp ~/linux-fairydust/.config ~/kernel-tipd-oob-fixes/.config
git -C ~/kernel-tipd-oob-fixes status --short
exit
```

`~/linux-fairydust/.config` here is the known working baseline configuration;
preserve that baseline or use the captured installed config as described in
the main guide. An arbitrary config from another kernel is insufficient.
Read applicable source-tree instructions before making changes.

Change the branch and worktree path together for another experiment. If a
worktree already exists, inspect it and reuse its pinned revision or choose a
new path. Do not reset a worktree containing someone else's changes. Detached
HEAD pins a test revision even if the remote branch advances; create a local
work branch with `git switch -c work/your-experiment` when developing changes.
Record the full commit, configuration, toolchain, and local changes for each
test. Here reproducibility means recorded inputs and repeatable operations;
build timestamps and generated signing keys can still change binary hashes.

Reuse the same dedicated worktree for subsequent edits/builds so Kbuild can
reuse its outputs. Keep a fresh release suffix for each staged test. An initial
full build in a fresh worktree is substantially heavier; prefer normal Asahi
for that build when possible. Native building inside the HV guest also works,
but has additional runtime overhead.

## 2. Check the USB-C/DP configuration

For this J413/M2 experiment, the reusable profile is
[`tools/profiles/j413-usbc-dp.json`](../tools/profiles/j413-usbc-dp.json).
It requires the branch's TIPD core/I2C driver, Type-C and DP alt mode, Apple
ATC PHY, display crossbar, Apple DRM, I2C, DART, tunables, DWC3 glue, role
switch, mailbox, and RTKit configuration. Required tristates can be `y` or
`m`; the profile preserves that choice. It does not replace the full baseline
configuration or enable missing options automatically.

For an intentional configuration change, use `make LLVM=1 menuconfig` in the
Mac worktree (with `ncurses-devel` installed), preserve the existing platform
and root-storage options, and run `olddefconfig`. The profile is specific to
this branch's J413 wiring. Review it when testing a different board or a
revision that changes symbols, module names, or bindings.

For the current branch, the J413 DTS already defines
`ENABLE_DCPEXT_TYPEC`. Its included `t8112-jxxx.dtsi` connects `usb-pd@3f`'s
connector to `dcpext`, enables external DCP, and routes its DP PHY and mux to
`atcphy1`. Build and use that branch's `t8112-j413.dtb` together with its
kernel; an old DTB can omit or change the experiment's wiring.

## 3. Build, stage, and audit from WSL

Run **in WSL**, from this checkout:

```bash
./tools/asahi build --source '~/kernel-tipd-oob-fixes' \
  --profile j413-usbc-dp --dry-run
./tools/asahi build --source '~/kernel-tipd-oob-fixes' \
  --profile j413-usbc-dp --jobs 4
./tools/asahi stage
./tools/asahi driver-check
./tools/asahi bundles
./tools/asahi boot --dry-run
```

The dry run validates the selected source/config, Rust toolchain, page size,
and profile options. The real build runs `olddefconfig`, rechecks the profile,
then builds `Image dtbs modules` with a fresh release suffix. For a recognizable
suffix, add `--localversion=-sdp-tipd-COMMIT-UNIQUE_RUN` to the real build;
never reuse an installed release.

For experiments that do not need the J413 USB-C/DP checks, omit `--profile`
and `driver-check`; fetching, pinning, building, staging, and HV identity
verification use the same workflow.

`stage` inherits the profile from the build record. For a build created before
the profile was selected, use `./tools/asahi stage --profile j413-usbc-dp`.
Staging installs all modules of the new release, runs depmod, explicitly adds
the profile's modular drivers and their dependencies to the initramfs, and
checks that the requested modules appear in its listing. It downloads a
checksummed bundle and selects it. Built-in drivers stay built in.

`driver-check` reads the selected bundle's full config and checks each required
module's exact kernel release (`vermagic`) and dependency resolution on the
Mac. It does not load modules from the candidate into the running kernel.
Reports go to `.asahi/driver-checks/`. A successful report before boot proves
module availability; device binding is checked separately after boot.

The build record pins the source commit and dirty-source fingerprint, make
arguments, and artifact/config/module checksums. Staging rejects source or
artifact changes after a build. To repeat an experiment, use the same recorded
source/config/toolchain with a new release suffix.

## 4. Reserve the correct USB-C port

On this MacBook Air J413 with this branch's DTS:

| Connection | Mac port |
| --- | --- |
| m1n1 USB proxy to Windows | Rear USB-C port, nearest MagSafe: ATC0 |
| USB-C display / DP adapter being tested | Front USB-C port, farther from MagSafe: ATC1 |
| Charging | MagSafe, if available |

The m1n1 HV removes its active USB controller/PHY from the guest. Putting the
proxy on ATC1 therefore removes the PHY required by this branch's external
display wiring. In the previous baseline run this caused external DCP to
remain deferred with `Failed to get dp-phy: -517`, despite all the relevant
modules being installed. Do not work around this by forcing Linux to reclaim
the proxy's PHY or unbinding its controller.

Confirm the choice in the new `hv.log`: expect `Initializing hypervisor over
iodev 4` and removal of `atc-phy0`, rather than `iodev 5` / `atc-phy1`, for the
current m1n1 revision. Moving the **Mac end** of the proxy cable while the Mac
is off leaves the Windows BUSID unchanged if its end stays on the same port.

The launcher checks the live transport before chainloading and again before
HV initialization; this profile requires iodev 4. Treat that check and the
log as authoritative rather than relying on a remembered cable location.
If a failed HV initialization disabled the other USB interface, moving the
cable may not enumerate it until the Mac is restarted into proxy mode with
the cable already in the intended port.

## 5. Shut down the old guest and boot the candidate

Finish builds, staging, and checks before shutting down. If an HV guest is
already running, save its logs and shut it down cleanly:

```bash
./tools/asahi ssh -- sudo -n systemctl poweroff
```

Wait for the serial log to show shutdown/unmount completion and the machine
to stop. Inspect `./tools/asahi logs`; do not kill the controller while the
guest is still running. After shutdown, retire the old host session:

```bash
tmux kill-session -t asahi-hv
./tools/asahi session start --wait 600
```

Move the proxy cable to ATC0 while the Mac is off. Keep the existing Windows
usbipd auto-attach process running. Hold the Mac's power button for startup
options and select the installed **m1n1 proxy entry**. This physical selection
may require the user. The waiting session loads the selected candidate when
the two USB serial devices appear. If the wait expires, inspect/retire the
failed session and start it again; keep the same selected bundle.

Inspect the boot and verify its identity **from WSL**:

```bash
./tools/asahi hv show
./tools/asahi check --wait 180
./tools/asahi driver-check --live
```

`check` requires the exact launch marker, selected release, original root UUID,
matching installed modules, and SSH. `driver-check --live` additionally requires
the front ATC PHY and crossbar, external DCP, display subsystem and front-port
PD controller to bind, plus a DRM DP connector. It also records connector
status/modes and deferred devices. An unplugged monitor may correctly report
`disconnected` while driver readiness passes. A successful desktop service
alone does not establish DP readiness or physical display output.

The tmux session must remain alive while the guest runs. For inspection:

```bash
./tools/asahi hv interrupt
./tools/asahi hv command ctx
./tools/asahi hv resume
./tools/asahi check --wait 30
```

## 6. Test hotplug separately

After the candidate and live driver checks pass, connect a display to ATC1.
Record the adapter/cable/display, orientation, resolution, and each plug/unplug
action. Run `driver-check --live` before and after each action to save connector
states and modes. Collect full kernel logs as well:

```bash
./tools/asahi ssh -- sudo -n dmesg
```

For TIPD/DRM debug logs, dynamic debug can be enabled in the guest for the
chosen experiment, if its config provides it:

```bash
./tools/asahi ssh -- sudo -n sh -c \
  'echo "module tps6598x_core +p" > /sys/kernel/debug/dynamic_debug/control'
./tools/asahi ssh -- sudo -n sh -c \
  'echo "module appledrm +p" > /sys/kernel/debug/dynamic_debug/control'
```

Turn these off afterward with the same commands using `-p` instead of `+p`.
For `tipd-oob-fixes`, correlate debounced HPD notifications with DRM connector
state and visible output, and test repeated unplug/replug without modeset
storms. OOB HPD logs are not themselves proof of visible output. PD driver
unbind/rebind is a separate experiment that can affect power and port state;
identify the guest's front controller by its `*-003f` sysfs path rather than
assuming an I2C bus number. Never run it against the proxy port during a run.

If no monitor is available, record boot/module/binding results and leave
hotplug, link training, and visible output explicitly untested. If boot fails,
retain its serial/HV logs and select normal Asahi from startup options. Select
a preserved baseline with `./tools/asahi use PATH_TO_BASELINE` for another HV
run. Keep kernel experiment results separate from host tooling tests.

## Current tipd-oob-fixes experiment

The fetched revision is `301e2ba4004a33f7c808489dc1b5951e41c5c09b`, based on
`ce9f2eba72c061a50b2d790450e90af3439d8c24`, with two commits in
`drivers/usb/typec/tipd/core.c`: connector fwnode cleanup on unregister, and
HPD edge filtering plus a consistent data-role snapshot. The test worktree
uses that exact source revision and the working baseline configuration.
The build and stage passed for release
`7.1.13-fairydust-sdp-tipd-301e2ba4-20261014a`, with 5,805 modules. All 11
requested modular profile drivers were verified in its initramfs; their
installed version strings and dependency resolution passed. Installed baseline
boot-file hashes remained unchanged. Host tooling validation passed 37 tests,
including a real launcher/shim process-group interrupt check.
The candidate's HV boot, exact launch identity, original root, SSH, and live
driver binding checks passed on ATC0. The front PHY, crossbar, PD controller,
external DCP, and display subsystem bound; the deferred-device list was empty.
DRM exposed disconnected `DP-1` and connected `eDP-1` (2560x1600). No display
is connected externally, so visible external output, hotplug, and link training
remain untested. The final boot with the durable launcher passed the same
checks, plus HV interrupt, CPU context inspection, and resume with SSH
verified afterward. The controller remained alive after that test. The run
uses a 512 MiB upload heap and records iodev 4; the 184 MiB initramfs is too
large for the upstream loader's default 128 MiB upload heap.
For this run, generated build outputs were seeded from the compiled clean
parent checkout before the final incremental build. The branch's `.git`, full
`.config`, and changed `drivers/usb/typec/tipd/core.c` were excluded from the
copy. Both checkouts were locked, their commits/cleanliness were checked, and
the protected file hashes were verified before and after. Kbuild then checks
dependencies/commands and rebuilds for the branch and its unique release.
The local experiment input record includes the cache parent and protected
hashes. The full-build procedure above works without this optimization;
do not copy parent sources over changed branch files or seed a live build.
