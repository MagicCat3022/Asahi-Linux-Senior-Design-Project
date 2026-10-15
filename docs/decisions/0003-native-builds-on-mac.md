# 0003: Build test kernels natively on the Mac

**Date:** 2026-10-14 · **Status:** accepted · **Deciders:** Mustafa Maras (full-team review pending)
· *Recorded after the fact; the reasoning is reconstructed from the workflow
guides.*

## Context

Kernels can be cross-compiled on an x86 PC (see the
[x86 cross-build guide](../guides/x86-cross-build-qemu.md)) or built natively
on the Mac. A kernel booted under the HV also needs modules installed on the
Mac's root filesystem under its exact release name, and an initramfs
generated for that Mac, which happen on the Mac either way. The installed
baseline's configuration uses Clang/LLVM, Rust, BTF, and module signing, so
the build toolchain has to match all of them.

## Decision

Test kernels are built over SSH on the Mac with `./tools/asahi build`, using
Fedora's native Clang/LLD and a rustup toolchain, from the baseline `.config`.
Staging installs the modules under a new release name and generates the
initramfs on the Mac, then copies the bundle to the PC.

## Consequences

- The build toolchain matches what the baseline was built with, and modules,
  initramfs, and kernel come from one place and one record.
- Builds compete with the Mac's other work, and a full build is slow (prefer
  booting normal Asahi for it). Incremental builds in one worktree are fast.
- Cross-compiling in WSL isn't automated. The x86 guide remains useful for
  compile checks and QEMU work without the Mac.
