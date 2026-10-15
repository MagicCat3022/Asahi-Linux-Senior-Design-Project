# Cross-build the kernel on x86-64 and test in QEMU

**Applies to:** Ubuntu 24.04 x86-64 host, fairydust 7.1.13 ·
**Last verified:** before 2026-10-10 on an Ubuntu 24.04.5 x86-64 host with
16 cores (exact date not recorded)

Use this guide to compile-check kernel changes, or to boot generic arm64
changes in QEMU, on a PC without the Mac. Kernels you want to run on Apple
hardware go through the [kernel workflow](kernel-workflow.md) instead, which
builds natively on the Mac and boots under the m1n1 hypervisor. See
[decision 0003](../decisions/0003-native-builds-on-mac.md).

> **Missing scripts.** The `dev/build.sh`, `dev/env.sh`, and `dev/run-qemu.sh`
> helpers used below were kept untracked in the author's kernel checkout (see
> [Layout and environment](#layout-and-environment)). They are not in this
> repository yet. Until someone adds them under `tools/`, ask the guide's
> author for a copy.

- Tree: Linux 7.1.13 (`Baby Opossum Posse`), branch `fairydust`
- Target: arm64, Apple Silicon

Both configurations below produce an `Image` and `vmlinux`, and the
`defconfig` kernel boots under QEMU.

## Requirements

```bash
sudo apt install -y \
  build-essential bc bison flex libssl-dev libelf-dev dpkg-dev \
  libncurses-dev rsync cpio kmod dwarves ccache \
  gcc-aarch64-linux-gnu gdb-multiarch qemu-system-arm

cargo install bindgen-cli --locked
```

Two version constraints are not satisfiable from apt.

**bindgen must come from cargo.** `scripts/min-tool-version.sh` requires 0.71.1
or newer. Ubuntu 24.04 ships 0.66.1, which the build rejects.

**Rust must come from rustup.** `arch/arm64/configs/asahi.config` sets
`CONFIG_RUST=y` and `CONFIG_RUST_APPLE_RTKIT=y`, and the minimum rustc is
1.85.0. Ubuntu ships 1.75. Installing `rust-src` from apt also shadows the
rustup toolchain, so use `rustup component add rust-src rustfmt` instead. The
`rust-src` component is required because the kernel compiles `core` and
`compiler_builtins` from its own copies under `rust/library`.

The host rustc cross-compiles to aarch64 with no extra components. The
`aarch64-unknown-none` target specification is built into rustc, and the kernel
supplies its own `core`, so no target-specific `rust-std` is needed.

## Build targets

Two configurations are available. They are kept in separate output directories
and must not be mixed.

### `defconfig`

Plain arm64 defconfig with 4 KiB pages. This is the iteration target and the
only one that runs under QEMU.

```bash
./dev/build.sh defconfig
```

### `asahi`

The real Asahi configuration, with 16 KiB pages and the Apple driver set
(`DRM_ASAHI`, `APPLE_RTKIT`, `MFD_MACSMC`, `APPLE_SIO`, `HID_MAGICMOUSE`, the
DPTX and ATC PHYs, and the Mac-specific I2C, SPI, SPMI, and GPIO controllers).

`arch/arm64/configs/asahi.config` is a fragment rather than a standalone
config. It holds only the Asahi-specific deltas and assumes an arm64 defconfig
beneath it. `build.sh` layers the two together and resolves the result with
`olddefconfig`.

```bash
./dev/build.sh asahi
```

This configuration cannot be run in QEMU. It sets
`CONFIG_ARM64_16K_PAGES=y`, and its device tree blobs describe Apple SoCs. The
failure is expected and does not indicate a broken setup.

### Cross-compilation

Both targets compile arm64 code on x86-64 through
`CROSS_COMPILE=aarch64-linux-gnu-`. This is the standard supported mode, and
the target machine is not involved in the build at all.

## Building

```bash
./dev/build.sh asahi                      # incremental rebuild
./dev/build.sh asahi -- modules           # modules only
./dev/build.sh menuconfig asahi           # edit config options
./dev/build.sh reconfigure asahi          # regenerate .config from scratch
./dev/build.sh clean                      # remove build outputs, keep ccache
./dev/build.sh paths                      # resolved paths and toolchain
./dev/build.sh help                       # full command list
```

Full builds take roughly 15 to 20 minutes on 16 cores. A no-op incremental
build takes about 15 seconds. Editing a file that `rust/kernel` depends on
rebuilds the Rust objects, the modules that link against them, and `vmlinux`,
which takes about a minute.

### ccache

ccache uses content-based compiler checking and a 10 GB ceiling. It is wired up
in a way that is not obvious and is worth stating, because both halves are easy
to get wrong silently.

`Makefile:535` contains `CC = $(CROSS_COMPILE)gcc`. A plain Makefile assignment
overrides the environment, so exporting `CC=ccache ...` has no effect and ccache
never runs. The value must be passed on the make command line instead, where
command-line assignments do take precedence. `build.sh` does this.

`HOSTCC` has an additional constraint. The Rust build passes it to rustc as
`-Clinker=$(HOSTCC)` (`rust/Makefile:547`), so it must be a single executable
path with no arguments. Setting `HOSTCC="ccache gcc"` fails proc-macro
compilation. `dev/env.sh` generates a wrapper script at
`~/kernel-build/bin/ccache-cc` to keep ccache while satisfying that
requirement.

### Using clang

```bash
LLVM=1 ./dev/build.sh asahi
```

This requires the LLVM binutils (`llvm-ar`, `llvm-objcopy`, `llvm-strip` and
the rest), not only `clang` and `lld`; install the `llvm` or `llvm-18` package
first. This path is not verified on this host. GCC is the default because it
has fewer version-matching constraints where Rust is involved.

`LLVM` must be unset or set to `1`. Passing `LLVM=0` is a hard error in the
kernel Makefile.

## Testing in QEMU

```bash
./dev/run-qemu.sh                  # headless, serial on the terminal
./dev/run-qemu.sh --gui
./dev/run-qemu.sh --gdb            # CPU halted, gdbstub on port 1234
./dev/run-qemu.sh --disk img.img   # attach a disk image
./dev/run-qemu.sh --rebuild
```

The runner builds a minimal busybox initramfs and caches it. An initramfs is
required because a kernel without one panics before reaching a prompt.

The guest is arm64 and the host is x86-64, so the host's `/usr/bin/busybox` is
the wrong architecture. Using it produces a boot that fails with
`Failed to execute /init (error -8)`, where -8 is `ENOEXEC`. The runner
therefore downloads a static arm64 busybox on first use and caches it at
`~/kernel-build/bin/busybox-arm64`. To supply your own instead, place a static
aarch64 busybox at that path.

The kernel source tree is shared into the guest read-only over 9p at
`/mnt/share`. Exit QEMU with `Ctrl-a x`, or run `poweroff -f` in the guest.

A successful boot looks like this:

```
=== arm64 defconfig test kernel is up ===
Linux (none) 7.1.13-gce9f2eba72c0 #2 SMP PREEMPT aarch64 GNU/Linux
nproc: 4   free: 1966 MiB
kernel source shared read-only at /mnt/share
BusyBox v1.38.0 ...
~ #
```

### Debugging

Start the guest halted, then attach from a second terminal:

```bash
./dev/run-qemu.sh --gdb

gdb-multiarch ~/kernel-build/defconfig/vmlinux
(gdb) target remote :1234
(gdb) break start_kernel
(gdb) c
```

Symbol names resolve because `defconfig` enables `CONFIG_DEBUG_INFO`; verify
with `grep DEBUG_INFO ~/kernel-build/defconfig/.config`.

Useful commands inside the guest:

```sh
dmesg | grep -i <subsys>   # filter the log for a subsystem
/proc/cmdline             # how the kernel was booted
cat /proc/interrupts      # IRQ routing
```

To resolve an address from a crash report:

```bash
scripts/make.addr2line.sh vmlinux <addr>
```

## Testing Asahi drivers

An Asahi kernel targets Apple Silicon peripherals. It cannot boot on x86-64,
and its modules cannot be loaded into the host kernel. This divides the work:

| Activity | Where it runs |
|---|---|
| Reading, patching, building | The x86 host, per this document |
| Smoke-testing generic arm64 changes | QEMU, with the `defconfig` kernel |
| Testing Asahi drivers (DCP, RTKit, macsmc) | Real M-series hardware |

Building the `asahi` configuration is worthwhile without hardware, because it
compiles every Asahi driver and catches errors in code that cannot otherwise be
exercised. Runtime behaviour remains untested.

The team tests on hardware with the [kernel workflow](kernel-workflow.md),
which boots kernels under the m1n1 hypervisor without touching the Mac's
installed boot files.

For reference only, a manual installation copies the built `Image` to the EFI System Partition
and the modules to `/lib/modules` on the Linux root filesystem:

```bash
# on macOS, with the ESP mounted
sudo cp ~/kernel-build/asahi/arch/arm64/boot/Image /Volumes/ESP/.

# modules, to the Linux rootfs
make -C <srctree> O=~/kernel-build/asahi \
     modules_install INSTALL_MOD_PATH=/mnt/linux
```

The module directory name must match the kernel release exactly. Check it with
`make -s -C <srctree> O=... kernelrelease`, which currently reports
`7.1.13-gce9f2eba72c0`. Asahi boots through m1n1 and m1n1efi rather than a
conventional bootloader, so follow the Asahi documentation for the current
procedure.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `No rule to make target '...tap.o'` | A sparse checkout pruned the build tree. Run `git sparse-checkout disable`. |
| `multiple input filenames provided`, with `gcc` among them | `HOSTCC` contains a space. It must be one executable path, because rustc takes it via `-Clinker=`. See *ccache*. |
| `Failed to execute /init (error -8)` | `ENOEXEC`: the initramfs holds an x86 busybox and the guest is arm64. See *Testing in QEMU*. |
| ccache reports zero hits and 0.0 GB | `CC` was exported rather than passed on the make command line, so it was ignored. See *ccache*. |
| `bindgen` too old or unsupported | Installed from apt. Use `cargo install bindgen-cli --locked`, and confirm `~/.cargo/bin` precedes apt in `PATH`. |
| rustc version errors, or a working rustup suddenly broken | An apt `rust-src` or `rustc` package shadowed rustup. Remove it. |
| `Invalid value for LLVM` | `LLVM=0` is illegal. Leave it unset or set it to `1`. |
| `No working init found` | Booting a kernel with no initramfs. Use `./dev/run-qemu.sh`. |
| Asahi kernel will not boot in QEMU | Expected. Use the `defconfig` kernel. |
| 4 KiB and 16 KiB page mismatch | `asahi.config` pins 16 KiB. Do not merge it into a QEMU test config. |
| `Permission denied` in the build directory | Artifacts owned by root from an earlier container or root build. `sudo chown -R $USER:~/kernel-build`. |
| Garbled output or spurious `command not found` after a build | A shell script was edited while bash was executing it. Bash reads scripts incrementally, so the edit shifted the file. Harmless if the build succeeded. |
| Slow rebuilds | Check `./dev/build.sh ccache` and confirm `CCACHE_DIR` has free space. |

## Layout and environment

```
Asahi-Linux-Senior-Design-Project/
├── dev/                  # helper scripts, not tracked by git
│   ├── env.sh            # shared environment
│   ├── build.sh          # build driver
│   └── run-qemu.sh       # QEMU runner

~/kernel-build/           # build outputs, outside the repository
├── defconfig/            # generic arm64, 4 KiB pages
├── asahi/                # Asahi config, 16 KiB pages
├── bin/
│   ├── ccache-cc         # single-path ccache wrapper for HOSTCC
│   └── busybox-arm64     # static arm64 busybox for the initramfs
├── ccache/               # compiler cache
└── initramfs.cpio.gz     # cached busybox initramfs
```

Builds are out-of-tree and outside the repository, so the source tree stays
clean and one configuration cannot corrupt another. The `dev/` directory is
listed in `.git/info/exclude`, which hides the scripts from `git status`
without modifying any tracked file, so they cannot appear in a patch or be
committed by accident.

The working tree is currently a full checkout, which a build requires. A
sparse checkout is reasonable for reading a kernel tree and unreasonable for
building one, because a build compiles nearly every top-level directory. If a
narrow tree is wanted for reading only, use a second clone:

```bash
git clone --shared . ~/asahi-readonly
```

`dev/env.sh` is the single source of truth for the environment, and every value
honours a pre-set variable, so overrides need no edits:

| Variable | Default |
|---|---|
| `KDEV_SRC` | repository root, detected automatically |
| `KDEV_BUILD_ROOT` | `~/kernel-build` |
| `ARCH` | `arm64` |
| `CROSS_COMPILE` | `aarch64-linux-gnu-` |
| `CC` | `ccache aarch64-linux-gnu-gcc`, passed on the make command line |
| `HOSTCC` | `~/kernel-build/bin/ccache-cc` |
| `KDEV_JOBS` | `$(nproc)` |
| `CCACHE_DIR` | `~/kernel-build/ccache` |
| `CCACHE_MAXSIZE` | `10G` |
| `KBUILD_BUILD_USER`, `KBUILD_BUILD_HOST` | `asahi-dev` |

`KBUILD_BUILD_TIMESTAMP` is deliberately not pinned, because doing so would
make every incremental rebuild appear to modify `vmlinux`. Set it when a
bit-for-bit reproducible build is needed.

## Removing

```bash
./dev/build.sh distclean    # build outputs and ccache
rm -rf ~/kernel-build dev
sed -i '/dev\//d' .git/info/exclude
```

This leaves the kernel tree untouched. Remove the packages with
`sudo apt remove`, and `cargo uninstall bindgen-cli` for bindgen.

## Contributing patches

Asahi CI enforces style:

```bash
./scripts/checkpatch.pl --strict --git HEAD~1
```
