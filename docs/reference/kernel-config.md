# Kernel configuration and toolchain

Facts about the kernel config and compilers we build with. The steps that use
them are in [Set up the test Mac](../guides/set-up-the-test-mac.md) and
[Test a kernel](../guides/test-a-kernel.md).

## Start from the Mac's own config

Every test kernel starts from the config of the kernel the Mac already runs
(`/boot/config-$(uname -r)`, copied to `~/linux-fairydust/.config`).
`build` then runs `olddefconfig` to fill in options that are new in the
source you're testing.

Other starting points don't work as well:

| Starting point | Problem |
| --- | --- |
| `make defconfig` | Leaves out most Apple drivers |
| `make LLVM=1 defconfig asahi.config` (the fragment in `arch/arm64/configs/`) | Builds, but it isn't the config the Mac boots with |
| `asahi_defconfig` | Doesn't exist in this tree |
| `make localmodconfig` | Drops drivers that aren't loaded right now, which can include ones needed under the hypervisor |
| A config from another distribution | Can point to signing certificates that aren't in this tree |

When you move to a much newer source, read what `olddefconfig` changed. A
renamed or removed driver option won't cause an error.

## Options that must stay on

These are checkpoints from the J413 config, not a complete list. The full
config holds many more Apple drivers that are also needed.

| Area | Options | Why |
| --- | --- | --- |
| Architecture | `CONFIG_ARCH_APPLE=y`, `CONFIG_ARM64_16K_PAGES=y` | Apple Silicon needs 16 KiB pages |
| Initramfs | `CONFIG_BLK_DEV_INITRD=y`, `CONFIG_RD_ZSTD=y` | Our initramfs is Zstandard-compressed |
| Serial console | `CONFIG_SERIAL_SAMSUNG=y`, `CONFIG_SERIAL_SAMSUNG_CONSOLE=y` | Writes the console that `serial.log` records |
| Modules | `CONFIG_MODULES=y`, `CONFIG_DEVTMPFS=y`, `CONFIG_DEVTMPFS_MOUNT=y` | Loading drivers and creating device files |
| Disk | `CONFIG_NVME_APPLE=m`, `CONFIG_NVME_CORE=m`, `CONFIG_BLK_DEV_NVME=m`, `CONFIG_BTRFS_FS=y` | Mounting the root file system; the modules must be in the initramfs |
| Wi-Fi (for SSH) | `CONFIG_BRCMFMAC=m`, `CONFIG_BRCMFMAC_PCIE=y`, `CONFIG_PCI=y`, `CONFIG_PCIE_APPLE=y`, `CONFIG_FW_LOADER=y` | `check` and everything after it use SSH |
| Rust | `CONFIG_RUST=y` | Some Asahi drivers are written in Rust |
| Debug info | `CONFIG_DEBUG_INFO_BTF=y`, `CONFIG_DEBUG_INFO_BTF_MODULES=y` | Needs `pahole` (package `dwarves`) |
| Module signing | `CONFIG_MODULE_SIG_ALL=y`, `CONFIG_MODULE_SIG_KEY="certs/signing_key.pem"`, empty `CONFIG_SYSTEM_TRUSTED_KEYS` | The tree generates its own key |

`tools/asahi` itself refuses a bundle without 16 KiB pages, initramfs
support, or the serial console, and refuses a Zstandard initramfs without
`CONFIG_RD_ZSTD`. USB-C display options are checked by the
[`j413-usbc-dp` profile](asahi-tool.md#driver-profiles).

## Recorded toolchain

Each new `./tools/asahi build` automatically records the tools selected by
Kbuild in `build.json` under `toolchain`. The same metadata is included in
the experiment's exported `build.json`.

| Key | Tool |
| --- | --- |
| `CC` | C compiler, including any wrapper or flags |
| `LD` | Linker |
| `RUSTC` | Rust compiler |
| `BINDGEN` | Rust binding generator |
| `PAHOLE` | BTF debug-information tool |

For each tool, the record contains its selected `command`, the path to its
first executable, its `--version` output, and the version command's return
code. Kbuild supplies the commands, so LLVM paths and version suffixes,
cross-compilers, and explicit make overrides are respected. Unavailable or
failing version queries are recorded with `version: null` and an `error`;
the kernel's normal build checks still determine which tools are required.

This captures versions at build time.

## Tested toolchain

The first native build ([2026-10-14-baseline-hv](../experiments/2026-10-14-baseline-hv/))
used source commit `ce9f2eba72c061a50b2d790450e90af3439d8c24` with:

| Tool | Tested version | Minimum for that source |
| --- | --- | --- |
| Clang / LLD | 22.1.8 | LLVM 15.0.0 |
| rustc (rustup) | 1.99.0 | 1.85.0 |
| bindgen | 0.72.1 | 0.71.1 |
| pahole | 1.32 | |
| OS | Fedora Asahi Remix 44 | |

The minimums come from that source's `scripts/min-tool-version.sh`. Check it
again, and `Documentation/process/changes.rst`, when you change kernel
versions. The upstream [LLVM](https://docs.kernel.org/kbuild/llvm.html) and
[Rust](https://docs.kernel.org/rust/quick-start.html) build guides cover
other toolchain layouts.
