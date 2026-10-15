# m1n1: setup and basic hardware inspection

**Written:** October 2026 · How m1n1's proxy and hypervisor modes work, and how
to read hardware registers through them. To run the team's HV test loop, follow
the [kernel workflow guide](../guides/kernel-workflow.md), which automates the
host setup below.

```text
Development host                         Apple Silicon Mac
----------------                         -----------------
Python proxy tools   <-- USB -->         m1n1
analysis scripts                         hardware registers
logs / output files                      physical memory
```

The Python code runs on the **host**. m1n1 runs on the **Mac** and performs the requested hardware operations.

## 1. Proxy mode vs. hypervisor mode

m1n1 can be used in two different ways.

### Proxy mode

In proxy mode, the Mac is stopped inside m1n1 and waits for commands from the host.

Use proxy mode to:

- read or write MMIO registers;
- inspect physical memory;
- inspect the Apple Device Tree (ADT);
- experiment with hardware blocks;
- load another m1n1 build or boot payload.

There is no macOS or Linux driver running at the same time.
### Hypervisor mode

In hypervisor mode, m1n1 runs underneath a guest operating system such as macOS or Linux.

This is the mode we use to observe driver behavior. m1n1 can trace hardware accesses when the OS responds to events such as connecting a USB-C display.

## 2. Install m1n1

There are two parts to the setup:

1. the **target Mac**, which runs m1n1;
2. the **development host**, which runs the Python proxy tools.

### Target Mac

The simplest dedicated development setup is the Asahi installer's **tethered-only m1n1 proxy mode**.

From macOS:

```bash
curl https://alx.sh | sh
```

Enable expert mode and choose the tethered-only m1n1 option.

If the Mac already has Asahi installed, the existing m1n1 installation can instead use the stage-1 proxy backdoor. Boot into the recovery environment for the Asahi installation and run:

```bash
csrutil disable
nvram boot-args=-v
```

This makes the installed m1n1 wait briefly for a USB proxy connection during boot.

### Development host

The host needs:

- Git;
- Python 3.9 or newer;
- `pip`;
- an AArch64 cross-compiler;
- the m1n1 build dependencies;
- `picocom`;
- Rust support required by the m1n1 build configuration.

Clone and build m1n1:

```bash
git clone --recursive https://github.com/AsahiLinux/m1n1.git
cd m1n1

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

rustup target add aarch64-unknown-none-softfloat

make
```

The build products are placed in `build/`, including `m1n1.bin` and `m1n1.macho`.

### Linux udev rules

On a Linux host, the repository's udev rules give the two m1n1 USB serial interfaces stable names:

- `/dev/m1n1` — primary proxy interface;
- `/dev/m1n1-sec` — secondary console interface.

Install them with:

```bash
sudo cp udev/80-m1n1.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

Your user may also need access to the system's serial-device group, commonly `dialout` or `uucp`.

## 3. Connect the host to the Mac

Connect the host to a Thunderbolt-capable USB-C port on the target Mac with a data-capable USB cable.

If the target is using the stage-1 proxy backdoor, m1n1 only waits a few seconds for the host to open one of its USB interfaces. Start the secondary-console helper before booting the Mac:

```bash
proxyclient/tools/picocom-sec.sh
```

Then boot the target Mac.

On the host, select the primary proxy interface:

```bash
source .venv/bin/activate
export M1N1DEVICE=/dev/m1n1
```

Without the udev rules, this will normally be one of the `/dev/ttyACM*` devices.

Start the interactive m1n1 Python shell:

```bash
python proxyclient/tools/shell.py
```

At this point, commands entered in the shell run Python on the host and send hardware requests to m1n1 on the Mac.

## 4. Read MMIO registers

Most peripheral registers are **memory-mapped I/O (MMIO)** registers. They are accessed using physical addresses.

Do not guess register addresses. Normally the base address comes from the Apple Device Tree or from an existing driver, and the register offset comes from reverse-engineered register definitions or source code.

Example from the interactive shell:

```python
node = u.adt["/arm-io/REPLACE_WITH_NODE"]
base, size = node.get_reg(0)

offset = VERIFIED_REGISTER_OFFSET
value = p.read32(base + offset)

print(f"0x{value:08x}")
```

Use the access width expected by the hardware:

```python
p.read8(address)
p.read16(address)
p.read32(address)
p.read64(address)
```

For example, a 32-bit register should normally be read with `read32`, not by performing a bulk memory read around it.

Some registers have side effects when read, and some hardware blocks must be powered before their registers are accessible.

## 5. How the Python proxy works

A proxy script is a normal Python program running on the development host.
The Python source code itself is not sent to the Mac for interpretation.

The important source files are:

- `proxyclient/tools/shell.py`  
  Starts the interactive development shell.

- `proxyclient/m1n1/setup.py`  
  Opens the connection to the target and creates the common proxy objects.

- `proxyclient/m1n1/proxy.py`  
  Implements the host-side proxy protocol and operations such as register reads.

- `proxyclient/m1n1/proxyutils.py`  
  Provides higher-level helpers for operations such as ADT access and CPU instructions.

- `src/proxy.c`  
  Runs on the Mac and dispatches proxy requests received from the host.

## 6. How this applies to the DisplayPort project

A practical workflow for the USB-C DisplayPort work is:

1. Establish a reliable m1n1 proxy connection.
2. Identify the relevant USB-C, ATC, PHY, and display-controller nodes and register ranges.
3. Verify that known registers can be read safely.
4. Use existing Asahi and Fairydust code to determine which registers are already understood.
5. Trace the relevant hardware blocks while connecting and disconnecting a USB-C display.
6. Compare the order and values of those accesses with the Linux/Fairydust implementation.

A simple before/after register dump can show that values changed. A hypervisor trace is more useful when the important question is **which registers were accessed, in what order, and in response to which event**.

## References

1. Asahi Linux Documentation — *m1n1 User Guide*
2. Asahi Linux Documentation — *Tethered Boot*
3. AsahiLinux/m1n1 repository
4. Asahi Linux Documentation — *m1n1 Hypervisor*