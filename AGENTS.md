# SDP kernel workflow

This checkout's `project` branch holds documentation and development tools.
Kernel changes belong in a separate worktree based on a kernel branch.

Use `docs/KERNEL_WORKFLOW.md` and `./tools/asahi --help` as the entry points.
Use `docs/BRANCH_HV_TESTING.md` for pinned development branches and J413
USB-C/DP tests. Build with `--profile j413-usbc-dp` for these experiments;
staging inherits the profile and verifies its modules in the initramfs.
Run `driver-check` before boot and `driver-check --live` afterward. On this
branch J413 DP uses ATC1 (front port); put the proxy on ATC0, nearest MagSafe.
Never move the proxy cable while a guest is running.
The host launcher uses a scoped Python shim for a configurable HV upload
heap and replaces its intermediate process before running the upstream
helper. Preserve that exec behavior: a waiting Python parent receives Ctrl-C
alongside the HV shell and can terminate the controller.
Machine configuration is `asahi.local.json`; generated state, bundles, build
records, and logs are in `.asahi/`. Both are ignored. Never commit SSH keys,
machine configuration, or captured binary artifacts.

The controller is Windows/Ubuntu WSL2; the Mac is a separate SSH target and
USB m1n1 target. Host paths and remote source paths are different namespaces.
Quote remote `~` paths. Use the configured SSH identity, not passwords in
commands or chat. `doctor` identifies the current HOME, project, and devices.

First inspect `doctor --online`, `discover`, and the selected bundle. Preserve
a captured installed baseline. Use `build --dry-run` to inspect native build
configuration, then `build` and `stage` for a new uniquely named release.
Staging installs candidate modules and generates its initramfs but must not
change the normal boot entry. Do not overwrite existing module releases.

Read applicable instructions in the chosen kernel source tree before editing.
The user has authorized AI assistance with m1n1 usage in this workflow; m1n1
is an external dependency, not a repository to modify as part of host tooling.

For automated HW runs, `session start` owns serial/HV in tmux. Before starting,
check for an existing `asahi-hv` session and old picocom/primary-port clients.
Use `hv interrupt`, `hv command`, `hv resume`, `hv show`, `logs`, and `ssh`
to operate an existing session. Detaching from tmux keeps the controller alive.
Do not terminate its controller while the guest runs. Physical boot selection
or a hard power cycle may still require the user.

`check` must verify the exact run marker, expected release, root UUID, modules,
and active SSH before reporting an HV smoke pass. `check --running` is only
a normal-Asahi baseline check. Do not claim HV or peripheral tests passed
from a normal SSH connection or host-only tests.

For workflow code changes, run:

```sh
uv run --no-project --python 3.13 --with pyserial==3.5 \
  python -m unittest discover -s tests -v
```

Record relevant build/boot/driver results and remaining hardware limitations.
Use existing user authorization for routine development; these instructions
do not add a separate approval requirement.
