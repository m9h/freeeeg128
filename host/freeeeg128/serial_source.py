"""pyserial byte-source adapter — drop-in replacement for SyntheticSource.

Wraps a ``serial.Serial`` object as an iterator of byte chunks suitable
for feeding into ``PacketParser`` via ``lsl_bridge.bridge()``.

This is the *one* module that changes between pre-hardware development
(using ``SyntheticSource``) and real-device operation (using this).
"""

from __future__ import annotations

import time
from typing import Iterator

import serial  # type: ignore


DEFAULT_BAUD = 115200  # CDC-ACM ignores baud; pyserial just needs a value
DEFAULT_READ_SIZE = 4096


def open_serial(port: str, baudrate: int = DEFAULT_BAUD,
                read_timeout_s: float = 0.1) -> "serial.Serial":
    s = serial.Serial(port=port, baudrate=baudrate, timeout=read_timeout_s)
    s.reset_input_buffer()
    return s


def iter_bytes(port: str,
               *,
               baudrate: int = DEFAULT_BAUD,
               read_size: int = DEFAULT_READ_SIZE,
               read_timeout_s: float = 0.1,
               duration_s: float | None = None,
               tee_path: str | None = None) -> Iterator[bytes]:
    """Yield raw byte chunks from a pyserial port.

    ``duration_s`` bounds total time; ``None`` means run until the source
    closes or the consumer stops.  ``tee_path`` writes a copy of every
    chunk to disk for later replay / debugging — write is fsync-free so
    small drops can occur on abrupt shutdown.
    """
    ser = open_serial(port, baudrate=baudrate, read_timeout_s=read_timeout_s)
    tee = open(tee_path, "wb", buffering=0) if tee_path else None
    t_start = time.monotonic()
    try:
        while True:
            chunk = ser.read(read_size)
            if chunk:
                if tee is not None:
                    tee.write(chunk)
                yield chunk
            if duration_s is not None and (time.monotonic() - t_start) >= duration_s:
                break
    finally:
        try:
            ser.close()
        finally:
            if tee is not None:
                tee.close()
