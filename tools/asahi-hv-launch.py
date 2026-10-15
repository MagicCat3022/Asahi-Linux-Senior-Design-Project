#!/usr/bin/env python3
"""Run upstream boot tools with a scoped Python shim for HV upload capacity."""
import os
from pathlib import Path
import runpy
import sys


def heap_bytes(value):
    size = int(value)
    if not 128 <= size <= 2048:
        raise ValueError("hv_heap_mib must be between 128 and 2048")
    return size * 1024 * 1024


def check_port(proxy):
    expected = os.environ.get("ASAHI_HV_EXPECT_IODEV")
    actual = int(proxy.iodev_whoami())
    print(f"Proxy transport: iodev {actual}", flush=True)
    if expected and actual != int(expected):
        port = os.environ.get("ASAHI_HV_EXPECT_PORT")
        raise ValueError(f"Proxy is on iodev {actual}; this bundle's driver profile requires iodev {expected}"
                         + (f" ({port})" if port else "") + ". No guest started. "
                         "Move the cable's Mac end to that port.")


def run_guest(script, arguments):
    sys.path.insert(0, str(script.resolve().parents[1]))
    from m1n1 import proxyutils
    original = proxyutils.ProxyUtils.__init__
    reserve = heap_bytes(os.environ.get("ASAHI_HV_HEAP_MIB", "512"))
    def initialize(self, proxy, *args, **kwargs):
        check_port(proxy)
        # Upstream run_guest explicitly requests 128 MiB. Larger initramfs
        # blobs can exceed that allocation when gzip cannot compress them.
        kwargs["heap_size"] = max(kwargs.get("heap_size", 0), reserve)
        original(self, proxy, *args, **kwargs)
    proxyutils.ProxyUtils.__init__ = initialize
    previous = sys.argv
    sys.argv = [str(script)] + arguments
    try:
        print(f"HV upload heap: {reserve // (1024 * 1024)} MiB", flush=True)
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = previous
        proxyutils.ProxyUtils.__init__ = original


def main():
    if sys.argv[1:2] == ["--python"]:
        arguments = sys.argv[2:]
        if arguments and Path(arguments[0]).name == "run_guest.py":
            run_guest(Path(arguments[0]), arguments[1:])
        else:
            os.execv(sys.executable, [sys.executable] + arguments)
        return
    helper = Path(sys.argv[1]).resolve()
    heap_bytes(os.environ.get("ASAHI_HV_HEAP_MIB", "512"))
    sys.path.insert(0, str(helper.parents[1]))
    from m1n1.proxy import UartInterface, M1N1Proxy
    iface = UartInterface()
    try:
        check_port(M1N1Proxy(iface))
    finally:
        iface.dev.close()
    environment = dict(os.environ)
    environment["ASAHI_HV_PYTHON"] = sys.executable
    environment["ASAHI_HV_RUNNER"] = str(Path(__file__).resolve())
    environment["PATH"] = str(Path(__file__).parent / "runtime") + os.pathsep + environment["PATH"]
    # Replace the launcher: a waiting Python parent would also receive Ctrl-C
    # and kill the HV child while the child is entering its interactive shell.
    os.execve("/bin/bash", ["bash", str(helper)] + sys.argv[2:], environment)


if __name__ == "__main__":
    main()
