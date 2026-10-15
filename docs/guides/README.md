# Guides

Step-by-step instructions. Guides are kept correct: when you change a command,
rerun it and update the guide's **Last verified** line. Results never go in a
guide; they go in an [experiment report](../experiments/).

| Guide | Use it to |
| --- | --- |
| [kernel-workflow.md](kernel-workflow.md) | Set up the PC and Mac, build a kernel on the Mac, and boot it under the m1n1 hypervisor |
| [branch-hv-testing.md](branch-hv-testing.md) | Test a pinned development branch, including the J413 USB-C/DP driver checks |
| [recording-an-experiment.md](recording-an-experiment.md) | Turn a hardware run into an experiment report with published evidence |
| [x86-cross-build-qemu.md](x86-cross-build-qemu.md) | Compile-check on an x86 PC and boot generic arm64 kernels in QEMU |

Every guide starts with:

```markdown
# Title

**Applies to:** hardware and kernel versions ·
**Last verified:** YYYY-MM-DD on `MAC-NN`; link to the experiment, if any
```
