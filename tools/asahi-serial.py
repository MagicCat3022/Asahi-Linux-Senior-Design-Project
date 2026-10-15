#!/usr/bin/env python3
"""Reconnectable virtual UART. Ctrl-] exits; every received byte is logged."""
import fcntl
import os
from pathlib import Path
import select
import sys
import termios
import time
import tty

import serial


def main():
    device, directory = sys.argv[1], Path(sys.argv[2])
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = Path(os.environ.get("ASAHI_CONSOLE_LOCK", str(Path(__file__).resolve().parents[1] / ".asahi/locks/console")))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = lock_path.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("Another workflow serial console is running; use session attach.")
    previous = termios.tcgetattr(sys.stdin.fileno()) if sys.stdin.isatty() else None
    ready = directory / "serial.ready"
    inputs = [sys.stdin.fileno()]
    print("Waiting for", device, "(Ctrl-] exits). Log:", directory / "serial.log", flush=True)
    try:
        if previous:
            tty.setraw(sys.stdin.fileno())
        with (directory / "serial.log").open("ab", buffering=0) as log:
            while True:
                if not Path(device).exists():
                    readable, _, _ = select.select(inputs, [], [], 0.5)
                    if readable:
                        data = os.read(sys.stdin.fileno(), 4096)
                        if b"\x1d" in data:
                            return
                        if not data:
                            inputs.clear()
                    continue
                try:
                    with serial.Serial(device, 500000, timeout=0, exclusive=True) as port:
                        ready.write_text(str(os.getpid()))
                        while True:
                            readable, _, _ = select.select([port.fileno()] + inputs, [], [], 0.5)
                            if port.fileno() in readable:
                                data = port.read(65536)
                                if data:
                                    log.write(data)
                                    sys.stdout.buffer.write(data)
                                    sys.stdout.buffer.flush()
                            if inputs and sys.stdin.fileno() in readable:
                                data = os.read(sys.stdin.fileno(), 4096)
                                if b"\x1d" in data:
                                    return
                                if data:
                                    port.write(data)
                                else:
                                    inputs.clear()
                except (serial.SerialException, OSError) as exc:
                    ready.unlink(missing_ok=True)
                    if Path(device).exists():
                        print("\r\nSerial unavailable:", exc, "\r", flush=True)
                    time.sleep(1)
    finally:
        ready.unlink(missing_ok=True)
        if previous:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, previous)
        lock.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
