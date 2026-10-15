#!/usr/bin/env python3
"""Operations sent over SSH on stdin; no permanent agent is installed on the Mac."""
import hashlib
import contextlib
import fcntl
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

SYSFS = Path("/sys")


def run(args, *, capture=True, check=True):
    result = subprocess.run(args, check=check, stdout=subprocess.PIPE if capture else sys.stderr,
                            stderr=None, text=True)
    return result.stdout.strip() if capture else None


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except PermissionError:
        return subprocess.check_output(["sudo", "-n", "cat", "--", str(path)])


def release_ok(release):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+\-]{0,127}", release):
        raise ValueError("Invalid kernel release")
    return release


def artifact_hashes(output):
    files = [".config", "arch/arm64/boot/Image", "System.map", "modules.order", "Module.symvers"]
    files += [str(p.relative_to(output)) for p in sorted((output / "arch/arm64/boot/dts/apple").glob("*.dtb"))]
    for name in (output / "modules.order").read_text().splitlines():
        module = Path(name).with_suffix(".ko")
        if module.is_absolute() or ".." in module.parts:
            raise ValueError("Unexpected module path in modules.order")
        files.append(str(module))
    result = {}
    for name in files:
        with (output / name).open("rb") as stream:
            result[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    return result


def boot_artifacts(release, compatible):
    # Tethered candidates deliberately have modules but no /boot entry. Their
    # SSH health check must work without assuming an installed boot artifact.
    unavailable = {"boot_artifacts_available": False, "kernel_config": {}, "artifact_sha256": {}}
    try:
        files = installed_files(release)
    except ValueError:
        return unavailable
    board = compatible.removeprefix("apple,")
    relevant = {name: path for name, path in files.items()
                if not name.endswith(".dtb") or name.endswith("-" + board + ".dtb")}
    if not all(Path(path).is_file() for path in relevant.values()):
        return unavailable
    options = read_bytes(files[".config"]).decode().splitlines()
    return {"boot_artifacts_available": True,
        "kernel_config": {line.split("=", 1)[0]: line.split("=", 1)[1] for line in options
            if line.startswith(("CONFIG_ARM64_16K_PAGES=", "CONFIG_BLK_DEV_INITRD=", "CONFIG_SERIAL_SAMSUNG_CONSOLE=", "CONFIG_RD_ZSTD="))},
        "configuration_source": files[".config"],
        "artifact_sha256": {name: hashlib.sha256(read_bytes(path)).hexdigest() for name, path in relevant.items()}}


def inventory():
    cmdline = Path("/proc/cmdline").read_text().strip()
    compatible = Path("/proc/device-tree/compatible").read_bytes().split(b"\0")[0].decode()
    model = Path("/proc/device-tree/model").read_bytes().rstrip(b"\0").decode()
    result = {
        "release": os.uname().release,
        "model": model,
        "compatible": compatible,
        "cmdline": cmdline,
        "root_uuid": run(["findmnt", "-n", "-o", "UUID", "/"]),
        "root_source": run(["findmnt", "-n", "-o", "SOURCE", "/"]),
        "root_fstype": run(["findmnt", "-n", "-o", "FSTYPE", "/"]),
        "root_options": run(["findmnt", "-n", "-o", "OPTIONS", "/"]),
        "efi_partuuid": run(["findmnt", "-n", "-o", "PARTUUID", "/boot/efi"]),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "ssh_enabled": run(["systemctl", "is-enabled", "sshd"], check=False),
        "ssh_active": run(["systemctl", "is-active", "sshd"], check=False),
        "modules_present": Path("/lib/modules", os.uname().release).is_dir(),
        "sudo": subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0,
    }
    result.update(boot_artifacts(release_ok(result["release"]), compatible))
    return result


def source_info(source):
    fingerprint = hashlib.sha256(subprocess.check_output(
        ["git", "-C", str(source), "diff", "HEAD", "--binary"]))
    untracked = subprocess.check_output(["git", "-C", str(source), "ls-files", "--others", "--exclude-standard", "-z"])
    for name in sorted(untracked.split(b"\0")):
        if name:
            fingerprint.update(name)
            path = source / os.fsdecode(name)
            fingerprint.update(os.readlink(path).encode() if path.is_symlink() else path.read_bytes())
    return {"source": str(source), "fingerprint": fingerprint.hexdigest(),
            "commit": run(["git", "-C", str(source), "rev-parse", "HEAD"]),
            "dirty": bool(run(["git", "-C", str(source), "status", "--porcelain"])),
            "diff": run(["git", "-C", str(source), "diff", "--stat"])}


def make_command(settings):
    source = Path(settings["source"]).expanduser().resolve()
    output = Path(settings.get("output") or source).expanduser().resolve()
    command = ["make", "--no-print-directory", "-C", str(source)]
    if output != source:
        command.append("O=" + str(output))
    for arg in settings.get("make_args", []):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=[^\n\r]*", arg):
            raise ValueError("Make arguments must be NAME=value assignments")
        if arg.split("=", 1)[0] in {"INSTALL_MOD_PATH", "INSTALL_PATH", "DEPMOD"}:
            raise ValueError("Installation paths are managed by the workflow")
        command.append(arg)
    return command, source, output


@contextlib.contextmanager
def build_lock(settings):
    _, _, output = make_command(settings)
    locks = Path.home() / ".cache/asahi-workflow/locks"
    locks.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(str(output).encode()).hexdigest()
    with (locks / name).open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another workflow build/stage owns " + str(output))
        yield


def preflight(command, output):
    config = (output / ".config").read_text().splitlines()
    if "CONFIG_ARM64_16K_PAGES=y" not in config:
        raise ValueError("The hardware build needs CONFIG_ARM64_16K_PAGES=y")
    if "CONFIG_RUST=y" in config:
        run(command + ["rustavailable"], capture=False)


def profile_modules(profile, options):
    missing = [key for key in profile["options"] if options.get(key) not in {"y", "m"}]
    if missing:
        raise ValueError("Driver profile needs enabled options: " + ", ".join(missing))
    return [module for key, module in profile["options"].items()
            if module and options[key] == "m"]


def config_options(path):
    return dict(line.split("=", 1) for line in Path(path).read_text().splitlines()
                if line.startswith("CONFIG_") and "=" in line)


def driver_check(settings):
    release = release_ok(settings["release"])
    profile, options = settings["profile"], settings["options"]
    modules = profile_modules(profile, options)
    result = {"release": release, "profile": profile["name"], "modules": {}, "errors": []}
    for module in modules:
        check = subprocess.run(["modinfo", "-k", release, "-F", "vermagic", module],
                               capture_output=True, text=True)
        deps = subprocess.run(["modprobe", "--set-version", release, "--show-depends", module],
                              capture_output=True, text=True)
        result["modules"][module] = {"vermagic": check.stdout.strip(),
            "dependencies": deps.stdout.splitlines(), "error": check.stderr + deps.stderr}
        if check.returncode or check.stdout.split()[:1] != [release] or deps.returncode:
            result["errors"].append("Missing/mismatched module or dependencies: " + module)
    if settings.get("live"):
        result["running_release"] = os.uname().release
        if os.uname().release != release:
            result["errors"].append("Running kernel differs from the selected bundle")
        result["bindings"] = {}
        for driver, device in profile["bindings"].items():
            bound = (SYSFS / "bus" / driver.split("/")[0] / "drivers" / driver.split("/")[1] / device).is_symlink()
            result["bindings"][driver + "/" + device] = bound
            if not bound:
                result["errors"].append("Device is not bound: " + device)
        pd = list((SYSFS / "bus/i2c/drivers/tps6598x").glob("*-" + profile["pd_address"]))
        result["pd_devices"] = [p.name for p in pd if p.is_symlink()]
        if not result["pd_devices"]:
            result["errors"].append("Front-port PD controller is not bound")
        result["connectors"] = {}
        for path in sorted((SYSFS / "class/drm").glob("card*-*/status")):
            result["connectors"][path.parent.name] = {"status": path.read_text().strip(),
                "modes": (path.parent / "modes").read_text().splitlines()}
        if not any(re.fullmatch(r"card\d+-DP-\d+", name) for name in result["connectors"]):
            result["errors"].append("No DRM DisplayPort connector registered")
        try:
            result["deferred_devices"] = read_bytes(SYSFS / "kernel/debug/devices_deferred").decode()
        except (OSError, subprocess.CalledProcessError):
            result["deferred_devices"] = None
    result["passed"] = not result["errors"]
    return result


def build(settings):
    command, source, output = make_command(settings)
    if not (output / ".config").is_file():
        raise ValueError("Build output needs an existing .config; see docs/guides/kernel-workflow.md")
    preflight(command, output)
    if settings.get("driver_profile"):
        profile_modules(settings["driver_profile"], config_options(output / ".config"))
    before = source_info(source)
    run(command + ["olddefconfig"], capture=False)
    if settings.get("driver_profile"):
        profile_modules(settings["driver_profile"], config_options(output / ".config"))
    release = release_ok(run(command + ["-s", "kernelrelease"]))
    if release == os.uname().release or os.path.lexists("/lib/modules/" + release):
        raise ValueError("Build release already installed. Use a new --localversion.")
    run(command + ["-j" + str(settings["jobs"]), "Image", "dtbs", "modules"], capture=False)
    with (output / "arch/arm64/boot/Image").open("rb") as stream:
        header = stream.read(64)
    if header[0x38:0x3c] != b"ARM\x64":
        raise ValueError("Build did not produce a raw arm64 Image")
    after = source_info(source)
    if before != after:
        raise ValueError("Source changed during the build; rerun with a stable source tree")
    return {**settings, **after, "output": str(output), "release": release,
            "artifact_sha256": artifact_hashes(output)}


def installed_files(release):
    release_ok(release)
    files = {
        "arch/arm64/boot/Image": "/boot/vmlinuz-" + release,
        "initramfs.img": "/boot/initramfs-" + release + ".img",
        "System.map": "/boot/System.map-" + release,
        ".config": "/boot/config-" + release,
    }
    dtbs = sorted(Path("/boot/dtb-" + release, "apple").glob("*.dtb"))
    if not dtbs:
        raise ValueError("No device trees installed for " + release)
    files.update({"arch/arm64/boot/dts/apple/" + p.name: str(p) for p in dtbs})
    return files


def stage(settings):
    command, source, output = make_command(settings)
    release = release_ok(run(command + ["-s", "kernelrelease"]))
    if release != settings["release"]:
        raise ValueError("Build release changed; run build again")
    if source_info(source) != {k: settings[k] for k in ("source", "commit", "dirty", "diff", "fingerprint")}:
        raise ValueError("Source changed since build; run build again")
    if artifact_hashes(output) != settings["artifact_sha256"]:
        raise ValueError("Build artifacts changed since build; run build again")
    destination = Path("/lib/modules", release)
    if os.path.lexists(destination):
        raise ValueError("Refusing to overwrite installed modules for " + release)
    for relative in ("arch/arm64/boot/Image", "System.map", ".config", "modules.order"):
        if not (output / relative).is_file():
            raise ValueError("Missing build artifact: " + relative)
    profile = settings.get("driver_profile")
    add_drivers = profile_modules(profile, config_options(output / ".config")) if profile else []
    stage_dir = Path(tempfile.mkdtemp(prefix="asahi-hv-"))
    try:
        run(command + ["modules_install", "INSTALL_MOD_PATH=" + str(stage_dir / "root"),
                       "DEPMOD=true"], capture=False)
        modules = stage_dir / "root/lib/modules" / release
        # cp -T -n can silently skip an existing target. mkdir provides an atomic
        # refusal if another process installs this release after the check above.
        run(["sudo", "-n", "mkdir", str(destination)], capture=False)
        run(["sudo", "-n", "cp", "-a", "--no-preserve=ownership", str(modules) + "/.",
             str(destination)], capture=False)
        if shutil.which("restorecon"):
            run(["sudo", "-n", "restorecon", "-RF", str(destination)], capture=False)
        run(["sudo", "-n", "depmod", release], capture=False)
        initramfs = stage_dir / "initramfs.img"
        dracut = ["sudo", "-n", "dracut", "--force", "--hostonly", "--no-hostonly-cmdline"]
        if add_drivers:
            dracut += ["--add-drivers", " ".join(add_drivers)]
        run(dracut + ["--kver", release, str(initramfs)], capture=False)
        if add_drivers:
            listing = run(["sudo", "-n", "lsinitrd", str(initramfs)])
            present = {Path(line.split()[-1]).name.split(".ko", 1)[0].replace("-", "_")
                       for line in listing.splitlines() if ".ko" in line}
            missing = [name for name in add_drivers if name.replace("-", "_") not in present]
            if missing:
                raise ValueError("Initramfs omitted requested drivers: " + ", ".join(missing))
        files = {"arch/arm64/boot/Image": str(output / "arch/arm64/boot/Image"),
                 "System.map": str(output / "System.map"), ".config": str(output / ".config"),
                 "initramfs.img": str(initramfs)}
        files.update({"arch/arm64/boot/dts/apple/" + p.name: str(p)
                      for p in sorted((output / "arch/arm64/boot/dts/apple").glob("*.dtb"))})
        return {**settings, "files": files, "staging_dir": str(stage_dir),
                "modules_installed": True, "initramfs_add_drivers": add_drivers}
    except Exception:
        # An incomplete, uniquely named module directory is left for inspection;
        # no existing release or normal /boot entry is ever replaced.
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise


def export_bundle(settings):
    files = settings["files"]
    # Streaming tar uses normalized archive names, not paths supplied by tar output.
    # Read one artifact at a time so peak memory is bounded by the largest file.
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
        for name, path in files.items():
            data = read_bytes(path)
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))


def main():
    operation, settings = sys.argv[1], json.loads(sys.argv[2])
    if operation == "discover":
        result = inventory()
    elif operation == "driver-check":
        result = driver_check(settings)
    elif operation == "capture":
        result = inventory()
        if not result["boot_artifacts_available"]:
            raise ValueError("Current kernel has no complete installed /boot artifacts. Capture a normal installed baseline, or use stage for a candidate.")
        result["files"] = installed_files(os.uname().release)
    elif operation == "build":
        with build_lock(settings):
            result = build(settings)
    elif operation == "plan":
        command, source, output = make_command(settings)
        if not (output / ".config").is_file():
            raise ValueError("Build output needs an existing .config")
        preflight(command, output)
        if settings.get("driver_profile"):
            profile_modules(settings["driver_profile"], config_options(output / ".config"))
        result = {**settings, **source_info(source), "output": str(output),
                  "command": command + ["-j" + str(settings["jobs"]), "Image", "dtbs", "modules"],
                  "tools": {name: shutil.which(name) for name in ("clang", "ld.lld", "rustc", "bindgen", "dracut")}}
    elif operation == "stage":
        with build_lock(settings):
            result = stage(settings)
    elif operation == "export":
        export_bundle(settings)
        return
    elif operation == "cleanup":
        path = Path(settings["staging_dir"])
        if path.parent != Path("/tmp") or not path.name.startswith("asahi-hv-"):
            raise ValueError("Unexpected staging directory")
        shutil.rmtree(path)
        result = {"cleaned": str(path)}
    else:
        raise ValueError("Unknown remote operation")
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
