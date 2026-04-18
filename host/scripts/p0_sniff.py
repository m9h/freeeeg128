#!/usr/bin/env python3
"""P0.1 — CDC enumeration + raw-byte sniffer for stock FreeEEG128 firmware.

Usage:
    python3 scripts/p0_sniff.py                      # auto-find port
    python3 scripts/p0_sniff.py /dev/cu.usbmodem1101 # explicit

Prints a hex dump of the first N seconds of raw bytes and characterises:
- bytes/sec actual vs expected (~96 kB/s at 128ch × 250Hz × 24-bit)
- any obvious frame delimiters (most-common byte value at fixed stride)
- first 256 bytes in hex so we can eyeball the framing

Does NOT decode the stream — the stock firmware's wire format is unknown
until P0.1 finishes. This script is how we *find out* what the firmware
emits.
"""

from __future__ import annotations

import glob
import sys
import time
from collections import Counter

import serial

BAUDRATE = 115200  # CDC-ACM ignores baud, but pyserial needs a value
DURATION_S = 5


def find_port() -> str | None:
    candidates = (
        glob.glob("/dev/cu.usbmodem*")        # macOS
        + glob.glob("/dev/tty.usbmodem*")     # macOS (alternate)
        + glob.glob("/dev/ttyACM*")           # Linux
    )
    return candidates[0] if candidates else None


def hex_dump(buf: bytes, width: int = 16) -> str:
    lines = []
    for i in range(0, len(buf), width):
        chunk = buf[i : i + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:08x}  {hex_part:<{width*3}}  {ascii_part}")
    return "\n".join(lines)


def main() -> None:
    port = sys.argv[1] if len(sys.argv) > 1 else find_port()
    if port is None:
        print("ERROR: no CDC serial port found.")
        print("Candidates checked: /dev/cu.usbmodem* /dev/tty.usbmodem* /dev/ttyACM*")
        print("Is the board plugged into USB_DATA and powered via USB_POWER?")
        sys.exit(1)
    print(f"Port: {port}")

    with serial.Serial(port, BAUDRATE, timeout=0.5) as ser:
        ser.reset_input_buffer()
        print(f"Reading for {DURATION_S} s ...")
        t0 = time.perf_counter()
        chunks: list[bytes] = []
        total = 0
        while time.perf_counter() - t0 < DURATION_S:
            data = ser.read(4096)
            if data:
                chunks.append(data)
                total += len(data)
        elapsed = time.perf_counter() - t0

    buf = b"".join(chunks)
    rate_kBps = (total / elapsed) / 1024

    print()
    print(f"Bytes read        : {total:>10} in {elapsed:.2f} s")
    print(f"Throughput (kB/s) : {rate_kBps:>10.1f}")
    print(f"Target (stock fw) : {96.0:>10.1f}  (= 128 ch × 3 B × 250 Hz)")
    print()

    if total == 0:
        print("No data received. The board enumerated as CDC but emits no stream.")
        print("Either the stock firmware needs a start command, or something is wrong.")
        return

    print("First 256 bytes in hex:")
    print(hex_dump(buf[:256]))
    print()

    # Cheap framing sniff: look for the most-common byte at every stride
    # in [2, 4, 8, 128, 256, 384, 512, 1024].
    print("Framing hints (most-common byte at stride N over the capture):")
    for stride in (2, 4, 8, 128, 256, 384, 385, 386, 512, 1024):
        if len(buf) <= stride:
            continue
        col = buf[::stride]
        c = Counter(col)
        common, count = c.most_common(1)[0]
        dominance = count / len(col)
        marker = "  <-- candidate frame delimiter" if dominance > 0.8 else ""
        print(f"  stride {stride:>5}: most-common = 0x{common:02x}  "
              f"({count}/{len(col)} = {dominance:.1%}){marker}")


if __name__ == "__main__":
    main()
