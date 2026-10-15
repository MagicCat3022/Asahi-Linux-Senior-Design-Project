"""Host-only safety and PTY tests; these never reboot or modify the Mac."""
import argparse
import contextlib
import fcntl
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import pty
import subprocess
import signal
import select
import sys
import tarfile
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    result = importlib.util.module_from_spec(spec)
    loader.exec_module(result)
    return result


host = module("asahi_host", ROOT / "tools/asahi")
remote = module("asahi_remote", ROOT / "tools/asahi-remote.py")
launcher = module("asahi_launcher", ROOT / "tools/asahi-hv-launch.py")


def target():
    return {"cmdline": "BOOT_IMAGE=test root=UUID=abc ro rootflags=subvol=root quiet rhgb rootflags=subvol=root rd.luks.uuid=luks-def",
            "root_uuid": "abc", "root_options": "rw,subvol=/root", "root_fstype": "btrfs",
            "compatible": "apple,j413", "efi_partuuid": "efi-test"}


def fixture_bundle(directory):
    files = {"arch/arm64/boot/Image": b"\0" * 0x38 + b"ARM\x64" + b"\0" * 32,
             "arch/arm64/boot/dts/apple/t8112-j413.dtb": b"dtb", "System.map": b"symbol",
             ".config": b"CONFIG_ARM64_16K_PAGES=y\nCONFIG_BLK_DEV_INITRD=y\nCONFIG_SERIAL_SAMSUNG_CONSOLE=y\nCONFIG_RD_ZSTD=y\n",
             "initramfs.img": b"\x28\xb5\x2f\xfdtest"}
    for name, contents in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    manifest = {"release": "test-release", "modules_installed": True,
                "sha256": {name: host.digest(directory / name) for name in files}}
    host.save(directory / "manifest.json", manifest)
    return manifest


class HVLauncher(unittest.TestCase):
    def test_interrupt_keeps_controller_alive_through_real_launcher_and_shim(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = Path(temporary) / "proxyclient"
            scripts = client / "tools"
            package = client / "m1n1"
            scripts.mkdir(parents=True)
            package.mkdir()
            (package / "__init__.py").write_text("")
            (package / "proxy.py").write_text(
                "class UartInterface:\n"
                " def __init__(self): self.dev=self\n"
                " def close(self): pass\n"
                "class M1N1Proxy:\n"
                " def __init__(self,iface): pass\n"
                " def iodev_whoami(self): return 4\n")
            (package / "proxyutils.py").write_text("class ProxyUtils:\n def __init__(self,*a,**k): pass\n")
            helper = scripts / "run_guest_kernel.sh"
            helper.write_text('exec python3 "$(dirname "$0")/run_guest.py"\n')
            (scripts / "run_guest.py").write_text(
                "import signal,time\n"
                "signal.signal(signal.SIGINT,lambda *_:print('INTERRUPTED',flush=True))\n"
                "print('READY',flush=True)\n"
                "while True: time.sleep(0.05)\n")
            env = {**os.environ, "ASAHI_HV_EXPECT_IODEV": "4", "ASAHI_HV_HEAP_MIB": "512"}
            process = subprocess.Popen([sys.executable, str(ROOT / "tools/asahi-hv-launch.py"), str(helper)],
                                       env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            def read_until(token):
                data = b""
                deadline = time.monotonic() + 5
                while token not in data and time.monotonic() < deadline:
                    if select.select([process.stdout], [], [], 0.1)[0]:
                        chunk = os.read(process.stdout.fileno(), 4096)
                        if not chunk: break
                        data += chunk
                self.assertIn(token, data, data.decode(errors="replace"))
            try:
                read_until(b"READY")
                os.killpg(process.pid, signal.SIGINT)
                read_until(b"INTERRUPTED")
                self.assertIsNone(process.poll())
            finally:
                if process.poll() is None: os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
                process.stdout.close()

    def test_scoped_python_shim_preserves_stdin_scripts(self):
        env = {**os.environ, "ASAHI_HV_PYTHON": sys.executable,
               "ASAHI_HV_RUNNER": str(ROOT / "tools/asahi-hv-launch.py")}
        result = subprocess.run([str(ROOT / "tools/runtime/python3"), "-"],
                                input="print('stdin preserved')\n", env=env,
                                capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout, "stdin preserved\n")

    def test_large_upload_heap_overrides_upstream_request_and_restores_class(self):
        calls = []
        class ProxyUtils:
            def __init__(self, proxy, **kwargs):
                calls.append(kwargs)
        original = ProxyUtils.__init__
        fake = SimpleNamespace(proxyutils=SimpleNamespace(ProxyUtils=ProxyUtils))
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "tools/run_guest.py"
            script.parent.mkdir()
            script.write_text("from m1n1 import proxyutils\n"
                              "p=type('Proxy',(),{'iodev_whoami':lambda self:4})()\n"
                              "proxyutils.ProxyUtils(p,heap_size=128*1024*1024,m1n1_heap=128*1024*1024)\n")
            with patch.dict(sys.modules, {"m1n1": fake}), \
                 patch.dict(os.environ, {"ASAHI_HV_HEAP_MIB": "512", "ASAHI_HV_EXPECT_IODEV": "4"}), \
                 contextlib.redirect_stdout(io.StringIO()):
                launcher.run_guest(script, [])
        self.assertEqual(calls[0]["heap_size"], 512 * 1024 * 1024)
        self.assertEqual(calls[0]["m1n1_heap"], 128 * 1024 * 1024)
        self.assertIs(ProxyUtils.__init__, original)

    def test_wrong_transport_is_rejected_before_launch(self):
        with patch.dict(os.environ, {"ASAHI_HV_EXPECT_IODEV": "4"}), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "requires iodev 4"):
                launcher.check_port(SimpleNamespace(iodev_whoami=lambda:5))
        with self.assertRaises(ValueError):
            launcher.heap_bytes(4096)


class Arguments(unittest.TestCase):
    def test_preserves_storage_and_removes_boot_ui(self):
        result = host.boot_arguments(target()).split()
        self.assertIn("root=UUID=abc", result)
        self.assertIn("rd.luks.uuid=luks-def", result)
        self.assertEqual(result.count("rootflags=subvol=root"), 1)
        self.assertNotIn("quiet", result)
        self.assertNotIn("rhgb", result)
        self.assertFalse(any(x.startswith("BOOT_IMAGE=") for x in result))

    def test_infers_uuid_and_btrfs_subvolume(self):
        info = target()
        info["cmdline"] = "ro"
        self.assertIn("root=UUID=abc", host.boot_arguments(info))
        self.assertIn("rootflags=subvol=/root", host.boot_arguments(info))

    def test_removes_previous_run_and_break(self):
        info = target()
        info["cmdline"] += " rd.break=cmdline rd.shell asahi_sdp.run=old"
        result = host.boot_arguments(info)
        self.assertNotIn("rd.break", result)
        self.assertNotIn("asahi_sdp.run", result)


class Bundles(unittest.TestCase):
    def test_transferred_bundle_without_full_config_uses_verified_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = fixture_bundle(directory)
            manifest["kernel_config"] = dict(line.split("=", 1) for line in (directory / ".config").read_text().splitlines())
            (directory / ".config").unlink()
            del manifest["sha256"][".config"]
            host.save(directory / "manifest.json", manifest)
            host.validate_bundle(directory, target())
            del manifest["kernel_config"]["CONFIG_ARM64_16K_PAGES"]
            host.save(directory / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "CONFIG_ARM64_16K_PAGES"):
                host.validate_bundle(directory, target())

    def test_adoption_requires_matching_saved_remote_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "transfer"
            directory.mkdir()
            manifest = fixture_bundle(directory)
            info = {**target(), "release": "test-release", "modules_present": True,
                    "artifact_sha256": manifest["sha256"],
                    "kernel_config": dict(line.split("=", 1) for line in (directory / ".config").read_text().splitlines())}
            state = root / "state"
            host.save(state / "target.json", info)
            cfg = {"target": "user@host"}
            with patch.object(host, "ROOT", root), patch.object(host, "STATE", state), \
                 patch.object(host, "CONFIG", root / "config.json"), contextlib.redirect_stdout(io.StringIO()):
                host.adopt_bundle(cfg, directory)
                active = (root / cfg["bundle"]).resolve()
                self.assertEqual(host.validate_bundle(active, info)["release"], "test-release")
                (directory / "System.map").write_bytes(b"different")
                with self.assertRaisesRegex(ValueError, "differs"):
                    host.adopt_bundle(cfg, directory)
                self.assertEqual((root / cfg["bundle"]).resolve(), active)

    def test_checksums_and_board(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fixture_bundle(directory)
            self.assertEqual(host.validate_bundle(directory, target())["release"], "test-release")
            (directory / "System.map").write_text("changed")
            with self.assertRaisesRegex(ValueError, "checksum"):
                host.validate_bundle(directory, target())

    def test_wrong_board(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            fixture_bundle(directory)
            info = target()
            info["compatible"] = "apple,j999"
            with self.assertRaisesRegex(ValueError, "device tree"):
                host.validate_bundle(directory, info)

    def test_zstd_needs_kernel_support(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = fixture_bundle(directory)
            config = directory / ".config"
            config.write_text(config.read_text().replace("CONFIG_RD_ZSTD=y\n", ""))
            manifest["sha256"][".config"] = host.digest(config)
            host.save(directory / "manifest.json", manifest)
            with self.assertRaisesRegex(ValueError, "CONFIG_RD_ZSTD"):
                host.validate_bundle(directory)

    def test_archive_rejects_escape_links_and_duplicates(self):
        for name, kind in [("../escape", "file"), ("/absolute", "file"), ("link", "link"), ("same", "duplicate")]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                archive = directory / "input.tar"
                with tarfile.open(archive, "w") as stream:
                    entry = tarfile.TarInfo(name)
                    if kind == "link":
                        entry.type = tarfile.SYMTYPE
                        entry.linkname = "/tmp"
                        stream.addfile(entry)
                    else:
                        entry.size = 1
                        stream.addfile(entry, io.BytesIO(b"x"))
                        if kind == "duplicate":
                            stream.addfile(entry, io.BytesIO(b"y"))
                output = directory / "output"
                output.mkdir()
                with self.assertRaises(ValueError):
                    host.extract_archive(archive, output)


class RemoteBuilds(unittest.TestCase):
    def test_missing_profile_option_stops_before_configuration_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / ".config").write_text("CONFIG_ARM64_16K_PAGES=y\n")
            settings = {"source": str(output), "jobs": 4,
                        "driver_profile": {"options": {"CONFIG_REQUIRED_PHY": "phy"}}}
            with patch.object(remote, "run") as invoked:
                with self.assertRaisesRegex(ValueError, "CONFIG_REQUIRED_PHY"):
                    remote.build(settings)
                invoked.assert_not_called()

    def test_profile_option_removed_by_olddefconfig_stops_before_compilation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            config = output / ".config"
            config.write_text("CONFIG_ARM64_16K_PAGES=y\nCONFIG_REQUIRED_PHY=m\n")
            settings = {"source": str(output), "jobs": 4,
                        "driver_profile": {"options": {"CONFIG_REQUIRED_PHY": "phy"}}}
            def olddefconfig(command, **kwargs):
                self.assertEqual(command[-1], "olddefconfig")
                config.write_text("CONFIG_ARM64_16K_PAGES=y\n")
            with patch.object(remote, "run", side_effect=olddefconfig) as invoked, \
                 patch.object(remote, "source_info", return_value={}):
                with self.assertRaisesRegex(ValueError, "CONFIG_REQUIRED_PHY"):
                    remote.build(settings)
                self.assertEqual(invoked.call_count, 1)

    def test_driver_profile_preserves_builtins_and_requires_enabled_features(self):
        profile = {"options": {"CONFIG_PD": "pd", "CONFIG_PHY": "phy", "CONFIG_BUS": None}}
        self.assertEqual(remote.profile_modules(profile,
                         {"CONFIG_PD": "m", "CONFIG_PHY": "y", "CONFIG_BUS": "y"}), ["pd"])
        with self.assertRaisesRegex(ValueError, "CONFIG_PHY"):
            remote.profile_modules(profile, {"CONFIG_PD": "m", "CONFIG_PHY": "n", "CONFIG_BUS": "y"})

    def test_driver_audit_rejects_broken_dependencies_despite_matching_vermagic(self):
        settings = {"release": "candidate", "profile": {"name": "test", "options": {"CONFIG_PD": "pd"}},
                    "options": {"CONFIG_PD": "m"}}
        results = [SimpleNamespace(returncode=0, stdout="candidate SMP", stderr=""),
                   SimpleNamespace(returncode=1, stdout="", stderr="Missing dependency")]
        with patch.object(remote.subprocess, "run", side_effect=results):
            result = remote.driver_check(settings)
        self.assertFalse(result["passed"])
        self.assertIn("pd", result["errors"][0])

    def test_live_dp_readiness_accepts_disconnected_monitor_but_rejects_unbound_phy(self):
        with tempfile.TemporaryDirectory() as temporary:
            sysfs = Path(temporary)
            profile = {"name": "test", "options": {}, "pd_address": "003f",
                       "bindings": {"platform/phy": "front-phy"}}
            phy = sysfs / "bus/platform/drivers/phy/front-phy"
            pd = sysfs / "bus/i2c/drivers/tps6598x/0-003f"
            for path in (phy, pd):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(sysfs)
            connector = sysfs / "class/drm/card2-DP-1"
            connector.mkdir(parents=True)
            (connector / "status").write_text("disconnected\n")
            (connector / "modes").write_text("")
            settings = {"release": "candidate", "profile": profile, "options": {}, "live": True}
            with patch.object(remote, "SYSFS", sysfs), \
                 patch.object(remote.os, "uname", return_value=SimpleNamespace(release="candidate")):
                self.assertTrue(remote.driver_check(settings)["passed"])
                phy.unlink()
                result = remote.driver_check(settings)
                self.assertFalse(result["passed"])
                self.assertTrue(any("front-phy" in e for e in result["errors"]))

    def test_failed_rust_preflight_stops_before_reconfiguring_or_compiling(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            config = output / ".config"
            original = "CONFIG_ARM64_16K_PAGES=y\nCONFIG_RUST=y\n"
            config.write_text(original)
            failure = subprocess.CalledProcessError(1, ["make", "rustavailable"])
            with patch.object(remote, "run", side_effect=failure) as invoked:
                with self.assertRaises(subprocess.CalledProcessError):
                    remote.build({"source": str(output), "jobs": 4})
            self.assertEqual(invoked.call_count, 1)
            self.assertEqual(invoked.call_args.args[0][-1], "rustavailable")
            self.assertEqual(config.read_text(), original)

    def test_same_output_cannot_be_built_or_staged_concurrently(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = {"source": str(root / "source")}
            with patch.object(remote.Path, "home", return_value=root), remote.build_lock(settings):
                with self.assertRaisesRegex(ValueError, "Another workflow build/stage"):
                    with remote.build_lock(settings):
                        self.fail("Concurrent lock was granted")

    def test_tethered_candidate_without_boot_files_can_still_be_inspected(self):
        with patch.object(remote, "installed_files", side_effect=ValueError("No device trees installed")):
            result = remote.boot_artifacts("test-candidate", "apple,j413")
        self.assertFalse(result["boot_artifacts_available"])
        self.assertEqual(result["artifact_sha256"], {})

    def test_installed_proof_includes_configuration_and_artifact_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest = fixture_bundle(directory)
            files = {name: str(directory / name) for name in manifest["sha256"]}
            with patch.object(remote, "installed_files", return_value=files):
                result = remote.boot_artifacts("test-release", "apple,j413")
            self.assertTrue(result["boot_artifacts_available"])
            self.assertEqual(result["kernel_config"]["CONFIG_RD_ZSTD"], "y")
            self.assertEqual(result["artifact_sha256"], manifest["sha256"])

    def test_artifact_hashes_cover_modules_and_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for name in [".config", "arch/arm64/boot/Image", "System.map", "Module.symvers", "drivers/test.ko"]:
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"original")
            (output / "modules.order").write_text("drivers/test.o\n")
            before = remote.artifact_hashes(output)
            (output / "drivers/test.ko").write_bytes(b"changed")
            after = remote.artifact_hashes(output)
            self.assertNotEqual(before["drivers/test.ko"], after["drivers/test.ko"])
            self.assertEqual(before[".config"], after[".config"])

    def test_make_arguments_cannot_override_install_paths(self):
        for assignment in ["INSTALL_MOD_PATH=/", "DEPMOD=bad", "--eval=bad", "LLVM=1\nbad"]:
            with self.subTest(assignment=assignment), self.assertRaises(ValueError):
                remote.make_command({"source": "/tmp/source", "make_args": [assignment]})

    def test_make_has_clean_machine_readable_output(self):
        command, _, _ = remote.make_command({"source": "/tmp/source", "make_args": ["LLVM=1"]})
        self.assertIn("--no-print-directory", command)

    def test_rejects_installed_modules_before_writing(self):
        info = {"source": "/tmp/source", "commit": "abc", "dirty": False, "diff": "", "fingerprint": "hash"}
        settings = {**info, "release": "already-installed", "artifact_sha256": {}}
        with patch.object(remote, "run", return_value="already-installed"), \
             patch.object(remote, "source_info", return_value=info), \
             patch.object(remote, "artifact_hashes", return_value={}), \
             patch.object(remote.os.path, "lexists", return_value=True):
            with self.assertRaisesRegex(ValueError, "overwrite"):
                remote.stage(settings)

    def test_rejects_changed_artifacts(self):
        info = {"source": "/tmp/source", "commit": "abc", "dirty": False, "diff": "", "fingerprint": "hash"}
        settings = {**info, "release": "test", "artifact_sha256": {"Image": "old"}}
        with patch.object(remote, "run", return_value="test"), \
             patch.object(remote, "source_info", return_value=info), \
             patch.object(remote, "artifact_hashes", return_value={"Image": "new"}):
            with self.assertRaisesRegex(ValueError, "artifacts changed"):
                remote.stage(settings)


class Execution(unittest.TestCase):
    def test_proxy_toolchain_paths_preserve_environment_and_directory_separators(self):
        before = os.environ.copy()
        cfg = {"proxy_env": {"USE_CLANG": "1", "TOOLCHAIN": "/opt/llvm/bin", "LLDDIR": "~/.local/lld-shim"}}
        env = host.proxy_environment(cfg)
        self.assertEqual(env["USE_CLANG"], "1")
        self.assertEqual(env["TOOLCHAIN"], "/opt/llvm/bin/")
        self.assertEqual(env["LLDDIR"], str(Path.home() / ".local/lld-shim") + "/")
        self.assertEqual(dict(os.environ), before)
        with self.assertRaisesRegex(ValueError, "proxy_env supports"):
            host.proxy_environment({"proxy_env": {"HOME": "/different-home"}})

    def test_missing_host_compiler_stops_before_target_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            host.save(state / "target.json", target())
            bundle = root / "bundle"
            bundle.mkdir()
            fixture_bundle(bundle)
            m1n1 = root / "m1n1"
            (m1n1 / "build").mkdir(parents=True)
            (m1n1 / "build/m1n1.bin").write_bytes(b"m1n1_initramfs")
            cfg = {"bundle": str(bundle), "m1n1_dir": str(m1n1), "proxy": "/dev/null"}
            args = argparse.Namespace(bundle=None, run_dir=None, dry_run=False, diagnostic=False, wait=0, require_console=False)
            with patch.object(host, "STATE", state), \
                 patch.object(host.subprocess, "check_output", return_value="commit\n"), \
                 patch.object(host, "proxy_preflight", side_effect=ValueError("host toolchain missing")), \
                 patch.object(host, "relay") as controller:
                with self.assertRaisesRegex(ValueError, "host toolchain missing"):
                    host.boot(cfg, args)
            controller.assert_not_called()
            self.assertFalse((state / "latest-run.json").exists())
            self.assertFalse((state / "runs").exists())

    def test_busy_proxy_does_not_replace_active_run_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            host.save(state / "target.json", target())
            previous = {"directory": str(root / "active-run")}
            host.save(state / "latest-run.json", previous)
            bundle = root / "bundle"
            bundle.mkdir()
            fixture_bundle(bundle)
            m1n1 = root / "m1n1"
            (m1n1 / "build").mkdir(parents=True)
            (m1n1 / "build/m1n1.bin").write_bytes(b"m1n1_initramfs")
            (state / "locks").mkdir()
            cfg = {"bundle": str(bundle), "m1n1_dir": str(m1n1), "proxy": "/dev/null"}
            args = argparse.Namespace(bundle=None, run_dir=None, dry_run=False, diagnostic=False, wait=0, require_console=False)
            with (state / "locks/proxy").open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with patch.object(host, "STATE", state), patch.object(host.subprocess, "check_output", return_value="commit\n"), patch.object(host, "proxy_preflight", return_value={}):
                    with self.assertRaisesRegex(ValueError, "owns the proxy/HV"):
                        host.boot(cfg, args)
            self.assertEqual(host.load(state / "latest-run.json"), previous)
            self.assertFalse((state / "runs").exists())

    def test_remote_export_and_host_extract_preserve_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "source"
            source.mkdir()
            fixture_bundle(source)
            files = {str(p.relative_to(source)): str(p) for p in source.rglob("*") if p.is_file()}
            archive = directory / "bundle.tar"
            # Replace only SSH transport; execute the actual remote program.
            with patch.object(host, "ssh_command", return_value=["bash", "-c"]):
                host.remote({}, "export", {"files": files}, archive=archive)
            output = directory / "output"
            output.mkdir()
            host.extract_archive(archive, output)
            self.assertEqual(host.validate_bundle(output, target())["release"], "test-release")

    def test_large_remote_settings_are_sent_over_stdin_not_shell_arguments(self):
        settings = {"files": {"a": "$(not-a-shell-command)" + "x" * 200000}}
        cfg = {"identity": "/nonexistent-test-key", "target": "user@host"}
        with patch.object(host.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=b"{}")) as invoked:
            host.remote(cfg, "plan", settings)
        command = invoked.call_args.args[0]
        self.assertEqual(command[-1], "python3 - plan")
        self.assertLess(len(str(command)), 1000)
        self.assertIn(b"$(not-a-shell-command)", invoked.call_args.kwargs["input"])

    def test_dry_run_does_not_change_latest_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            state = directory / "state"
            host.save(state / "target.json", target())
            bundle = directory / "bundle"
            bundle.mkdir()
            fixture_bundle(bundle)
            m1n1 = directory / "m1n1"
            (m1n1 / "build").mkdir(parents=True)
            (m1n1 / "build/m1n1.bin").write_bytes(b"m1n1_initramfs")
            cfg = {"bundle": str(bundle), "m1n1_dir": str(m1n1)}
            args = argparse.Namespace(bundle=None, run_dir=None, dry_run=True, diagnostic=False)
            with patch.object(host, "STATE", state), patch.object(host.subprocess, "check_output", return_value="commit\n"), contextlib.redirect_stdout(io.StringIO()):
                host.boot(cfg, args)
            self.assertFalse((state / "runs").exists())
            self.assertFalse((state / "latest-run.json").exists())

    def test_check_rejects_previous_boot_even_with_same_kernel(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            host.save(directory / "boot.json", {"run": "new", "release": "same-release"})
            info = {"cmdline": "asahi_sdp.run=old", "release": "same-release"}
            args = argparse.Namespace(run_dir=None, running=False, wait=0)
            with patch.object(host, "run_directory", return_value=directory), patch.object(host, "remote", return_value=info):
                with self.assertRaisesRegex(ValueError, "older/different boot"):
                    host.check({}, args)
            self.assertFalse((directory / "check.json").exists())

    def test_pty_relay_logs_output_and_preserves_exit_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            logfile = str(Path(temporary) / "output.log")
            code = ("import runpy,os,sys; h=runpy.run_path(" + repr(str(ROOT / "tools/asahi")) + "); "
                    "sys.exit(h['relay']([sys.executable,'-c',\"print('PTY works');raise SystemExit(7)\"],"
                    + repr(logfile) + ",os.environ.copy()))")
            result = subprocess.run([sys.executable, "-c", code], input=b"", capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertIn(b"PTY works", result.stdout)
            self.assertIn(b"PTY works", Path(logfile).read_bytes())

    @unittest.skipUnless(importlib.util.find_spec("serial"), "pyserial needed for UART integration test")
    def test_serial_console_logs_and_accepts_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            master, slave = pty.openpty()
            process = subprocess.Popen([sys.executable, str(ROOT / "tools/asahi-serial.py"), os.ttyname(slave), str(directory)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={**os.environ, "ASAHI_CONSOLE_LOCK": str(directory / "lock")})
            try:
                deadline = time.monotonic() + 5
                while not (directory / "serial.ready").exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue((directory / "serial.ready").exists())
                competitor = subprocess.run([sys.executable, str(ROOT / "tools/asahi-serial.py"), os.ttyname(slave), str(directory / "competitor")],
                    input=b"", capture_output=True, timeout=5,
                    env={**os.environ, "ASAHI_CONSOLE_LOCK": str(directory / "lock")})
                self.assertNotEqual(competitor.returncode, 0)
                self.assertIn(b"Another workflow serial console", competitor.stderr)
                os.write(master, b"guest booted\n")
                deadline = time.monotonic() + 5
                while b"guest booted" not in (directory / "serial.log").read_bytes() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertIn(b"guest booted", (directory / "serial.log").read_bytes())
                process.stdin.write(b"help\n")
                process.stdin.flush()
                import select
                self.assertTrue(select.select([master], [], [], 5)[0])
                self.assertIn(b"help", os.read(master, 4096))
                process.stdin.write(b"\x1d")
                process.stdin.flush()
                self.assertEqual(process.wait(timeout=5), 0)
                self.assertFalse((directory / "serial.ready").exists())
            finally:
                if process.poll() is None:
                    process.terminate()
                process.communicate(timeout=5)
                os.close(master)
                os.close(slave)

    @unittest.skipUnless(importlib.util.find_spec("serial"), "pyserial needed for UART integration test")
    def test_serial_reconnects_after_usb_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            descriptors = []
            master, slave = pty.openpty()
            descriptors.extend([master, slave])
            device = directory / "serial-device"
            device.symlink_to(os.ttyname(slave))
            process = subprocess.Popen([sys.executable, str(ROOT / "tools/asahi-serial.py"), str(device), str(directory)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={**os.environ, "ASAHI_CONSOLE_LOCK": str(directory / "lock")})

            def wait_for(predicate):
                deadline = time.monotonic() + 5
                while not predicate() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(predicate())

            try:
                wait_for(lambda: (directory / "serial.ready").exists())
                os.write(master, b"before reset\n")
                wait_for(lambda: b"before reset" in (directory / "serial.log").read_bytes())
                device.unlink()
                os.close(master)
                os.close(slave)
                descriptors.clear()
                wait_for(lambda: not (directory / "serial.ready").exists())
                master, slave = pty.openpty()
                descriptors.extend([master, slave])
                device.symlink_to(os.ttyname(slave))
                wait_for(lambda: (directory / "serial.ready").exists())
                os.write(master, b"after reset\n")
                wait_for(lambda: b"after reset" in (directory / "serial.log").read_bytes())
                self.assertIn(b"before reset", (directory / "serial.log").read_bytes())
                process.stdin.write(b"\x1d")
                process.stdin.flush()
                self.assertEqual(process.wait(timeout=5), 0)
            finally:
                if process.poll() is None:
                    process.terminate()
                process.communicate(timeout=5)
                for descriptor in descriptors:
                    os.close(descriptor)


class Evidence(unittest.TestCase):
    def fixture(self, root):
        state = root / ".asahi"
        host.save(state / "target.json", {"compatible": "apple,j413",
                                          "root_uuid": "391a13cb-c57f-44cb-b1fc-ab233af9d9b4"})
        run = state / "runs/20261014T010000000000Z"
        host.save(run / "boot.json", {"release": "7.1-sdp", "bundle": str(root / ".asahi/bundles/b"),
                                      "cmdline": "root=UUID=391a13cb-c57f-44cb-b1fc-ab233af9d9b4"})
        (run / "serial.log").write_text(
            "FDT: reporting device serial number: FX0AB12CD3\n"
            "Linux version 7.1-sdp (alice@macbox) (clang version 22.1.8)\n"
            "start=0123456789abcdef0123456789abcdef;hostname=macbox;machineid=fedcba9876543210fedcba9876543210\n"
            "Expecting dev-disk-by\\x2duuid-975ed9cd\\x2d1915\\x2d4e3f\\x2dacc0\\x2de2fbdd048e20.device\n"
            "EXT4-fs (nvme0n1p7): mounted filesystem 975ed9cd-1915-4e3f-acc0-e2fbdd048e20\n"
            "brcmfmac: address 02:11:22:33:44:55; firmware version 20.96.31.0.8.7.148\n"
            "commit 301e2ba4004a33f7c808489dc1b5951e41c5c09b keeps hashes\n"
            "systemd[1]: Hostname set to <macbox>.\n"
            "macbox login: \n")
        (run / "m1n1-linux.bin").write_bytes(b"\0binary")
        (run / "proxy.log").write_text("")
        (state / "runs/20261014T020000000000Z").mkdir(parents=True)
        host.save(state / "driver-checks/20261014T013000000000Z.json", {"release": "7.1-sdp", "passed": True})
        host.save(state / "driver-checks/20261014T013100000000Z.json", {"release": "baseline", "passed": False})
        host.save(state / "driver-checks/20261014T023000000000Z.json", {"release": "7.1-sdp", "passed": False})
        host.save(state / "builds/20261014T000000000000Z/build.json", {
            "release": "7.1-sdp", "source": "/home/alice/kernel", "commit": "301e2ba4",
            "artifact_sha256": {".config": "c", "arch/arm64/boot/Image": "i", "drivers/a.ko": "a", "drivers/b.ko": "b",
                                "arch/arm64/boot/dts/apple/t8112-j413.dtb": "j", "arch/arm64/boot/dts/apple/t8103-j274.dtb": "x"}})
        return state, run

    def collect(self, root, state, run, cfg=None, skip_logs=False):
        cfg = cfg or {"target": "alice@192.0.2.5", "private_evidence_dir": str(root / "private"),
                      "private_evidence_url": "https://github.com/team/evidence/"}
        args = SimpleNamespace(destination="docs/experiments/2026-10-14-test/evidence", run_dir=str(run),
                               driver_check=[], skip_logs=skip_logs)
        with patch.object(host, "ROOT", root), patch.object(host, "STATE", state), \
             contextlib.redirect_stdout(io.StringIO()):
            host.evidence(cfg, args)
        return (root / "docs/experiments/2026-10-14-test/evidence" / run.name,
                root / "private/2026-10-14-test" / run.name)

    def test_redacts_machine_identifiers_but_keeps_correlation_and_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, run = self.fixture(root)
            output, private = self.collect(root, state, run)
            serial = (private / "serial.log").read_text()
            for secret in ("FX0AB12CD3", "alice", "macbox", "975ed9cd", "fedcba98", "02:11:22", str(root)):
                self.assertNotIn(secret, serial + (output / "boot.json").read_text())
            self.assertIn("serial number: <serial-number>", serial)
            self.assertIn("(<mac-user>@<mac-hostname>)", serial)
            self.assertIn("<mac-hostname> login:", serial)
            self.assertIn("Hostname set to <<mac-hostname>>.", serial)
            self.assertEqual(serial.count("<uuid-1>"), 2)  # escaped and plain forms of one UUID
            self.assertIn("root=UUID=<root-uuid>", (output / "boot.json").read_text())
            self.assertIn("20.96.31.0.8.7.148", serial)
            self.assertIn("301e2ba4004a33f7c808489dc1b5951e41c5c09b", serial)
            self.assertIn("<project>/.asahi/bundles/b", (output / "boot.json").read_text())

    def test_selects_same_kernel_driver_checks_from_the_run_and_summarizes_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, run = self.fixture(root)
            output, private = self.collect(root, state, run)
            names = sorted(path.name for path in output.iterdir())
            self.assertEqual(names, ["boot.json", "build.json", "driver-check-20261014T013000000000Z.json", "logs.md"])
            self.assertEqual(sorted(path.name for path in private.iterdir()), ["serial.log"])  # empty proxy.log skipped
            self.assertIn("(https://github.com/team/evidence/blob/main/2026-10-14-test/20261014T010000000000Z/serial.log)",
                          (output / "logs.md").read_text())
            build = json.loads((output / "build.json").read_text())
            self.assertEqual(build["module_count"], 2)
            self.assertEqual(sorted(build["artifact_sha256"]),
                             [".config", "arch/arm64/boot/Image", "arch/arm64/boot/dts/apple/t8112-j413.dtb"])
            self.assertEqual(build["source"], "~/kernel")

    def test_logs_need_a_private_destination_or_explicit_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, run = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "private_evidence_dir"):
                self.collect(root, state, run, cfg={"target": "alice@192.0.2.5"})
            output, private = self.collect(root, state, run, cfg={"target": "alice@192.0.2.5"}, skip_logs=True)
            self.assertEqual(sorted(path.name for path in output.iterdir()),
                             ["boot.json", "build.json", "driver-check-20261014T013000000000Z.json"])
            self.assertFalse(private.exists())

    def test_evidence_is_written_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state, run = self.fixture(root)
            self.collect(root, state, run)
            with self.assertRaisesRegex(ValueError, "already exists"):
                self.collect(root, state, run)


class Profiles(unittest.TestCase):
    def test_profiles_come_from_files_and_carry_their_proxy_port(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host.save(root / "profiles/a-dp.json", {"name": "a-dp", "compatible": "apple,j413", "proxy_iodev": 4})
            host.save(root / "profiles/b-dp.json", {"name": "b-dp", "compatible": "apple,j274"})
            host.save(root / "state/target.json", {"compatible": "apple,j413"})
            with patch.object(host, "PROFILES", root / "profiles"), patch.object(host, "STATE", root / "state"):
                self.assertEqual(host.profile_names(), ["a-dp", "b-dp"])
                self.assertEqual(host.profiles_for("apple,j413"), ["a-dp"])
                with self.assertRaisesRegex(ValueError, "b-dp is for apple,j274, but this Mac is apple,j413"):
                    host.driver_profile("b-dp")
                with self.assertRaisesRegex(ValueError, "available: a-dp, b-dp"):
                    host.driver_profile("missing")
                saved = {"provenance": {"driver_profile": {"name": "a-dp", "proxy_iodev": 5}}}
                self.assertEqual(host.expected_proxy_iodev(saved), 5)
                # Bundles staged before profiles recorded a port fall back to the profile file.
                self.assertEqual(host.expected_proxy_iodev({"provenance": {"driver_profile": {"name": "a-dp"}}}), 4)
                self.assertIsNone(host.expected_proxy_iodev({"provenance": {}}))

    def test_shipped_profiles_are_complete(self):
        for name in host.profile_names():
            profile = host.load(host.PROFILES / (name + ".json"))
            self.assertEqual(profile["name"], name)
            for key in ("description", "board", "compatible", "options", "bindings", "pd_address"):
                self.assertIn(key, profile, name)
            self.assertEqual("proxy_iodev" in profile, "proxy_port" in profile, name)


class Status(unittest.TestCase):
    def next_steps(self, root, windows=None):
        with patch.object(host, "ROOT", root), patch.object(host, "STATE", root / ".asahi"), \
             patch.object(host, "CONFIG", root / "asahi.local.json"), \
             patch.object(host, "tmux_windows", lambda name: windows):
            return host.gather_status()["next"]

    def test_next_step_follows_the_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / ".asahi"
            self.assertIn("init --target", self.next_steps(root))
            host.save(root / "asahi.local.json", {"target": "alice@192.0.2.5", "bundle": ".asahi/bundles/base"})
            self.assertIn("discover", self.next_steps(root))
            host.save(state / "target.json", {"compatible": "apple,j413", "release": "7.1"})
            self.assertIn("capture", self.next_steps(root))
            host.save(state / "bundles/base/manifest.json", {"release": "7.1", "origin": "installed-running-kernel"})
            host.save(state / "latest-build.json", {"release": "7.1-sdp", "driver_profile": {"name": "j413-usbc-dp"}})
            self.assertIn("stage --profile j413-usbc-dp", self.next_steps(root))
            host.save(state / "bundles/new/manifest.json", {"release": "7.1-sdp", "origin": "native-development-build"})
            self.assertIn("session start", self.next_steps(root))
            run = state / "runs/20261014T010000000000Z"
            host.save(state / "latest-run.json", {"directory": str(run)})
            host.save(run / "boot.json", {"release": "7.1-sdp", "state": "started"})
            self.assertIn("check --wait", self.next_steps(root, {"serial": True, "hv": True}))
            host.save(run / "check.json", {"passed": True, "mode": "hv"})
            self.assertIn("poweroff", self.next_steps(root, {"serial": True, "hv": True}))
            host.save(run / "boot.json", {"release": "7.1-sdp", "state": "exited"})
            self.assertIn("kill-session", self.next_steps(root, {"serial": True, "hv": False}))
            self.assertIn("recording-an-experiment", self.next_steps(root))
            (root / "docs/experiments/2026-10-14-x/evidence" / run.name).mkdir(parents=True)
            self.assertIn("session start", self.next_steps(root))


class CommandLine(unittest.TestCase):
    def test_every_command_is_grouped_documented_and_has_examples(self):
        grouped = [name for _, names in host.GROUPS for name in names]
        self.assertEqual(sorted(grouped), sorted(host.COMMANDS))
        self.assertEqual(len(grouped), len(set(grouped)))
        parser = host.build_parser()
        commands = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
        self.assertEqual(sorted(commands.choices), sorted(host.COMMANDS))
        for name, sub in commands.choices.items():
            self.assertIn("./tools/asahi " + name, sub.epilog)
            for action in sub._actions:
                if action.dest != "help":
                    self.assertTrue(action.help, f"{name} {action.dest} has no help text")


if __name__ == "__main__":
    unittest.main()
