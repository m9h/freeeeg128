"""Tests for the byte-source adapters (pyserial loopback + file replay)."""

from __future__ import annotations

import os
import pty
import threading
import time
from pathlib import Path

import pytest

from freeeeg128 import protocol, replay, synthetic


# ---------------------------------------------------------------------------
# Replay source
# ---------------------------------------------------------------------------

def test_replay_from_file(tmp_path: Path):
    """File-backed byte source should round-trip a captured stream."""
    src = synthetic.SyntheticSource(n_channels=128, sample_rate_hz=250)
    # Write 100 packets to disk
    capture = tmp_path / "capture.bin"
    with capture.open("wb") as f:
        for _ in range(100):
            f.write(src.next_packet())

    # Replay through a parser and count recovered packets
    parser = protocol.PacketParser()
    total = 0
    for chunk in replay.iter_bytes(capture, chunk_size=500):
        for _ in parser.feed(chunk):
            total += 1
    assert total == 100
    assert parser.drop_count == 0


# ---------------------------------------------------------------------------
# pyserial loopback via pty
# ---------------------------------------------------------------------------

def test_serial_loopback_via_pty():
    """Smoke test: the serial adapter reads bytes from a pty pair and the
    parser recovers a packet.  Doesn't try to stress-test the pty's
    kernel buffer — that's checked by live runs against real /dev/ttyACM."""
    import tty

    from freeeeg128 import serial_source

    parent_fd, child_fd = pty.openpty()
    child_name = os.ttyname(child_fd)
    tty.setraw(child_fd)
    tty.setraw(parent_fd)

    src = synthetic.SyntheticSource(n_channels=128, sample_rate_hz=250)
    pkt = src.next_packet()

    # Writer: push one packet, then hang around so the adapter can read it.
    def writer():
        time.sleep(0.05)  # let the reader open the pty first
        remaining = pkt
        while remaining:
            n = os.write(parent_fd, remaining)
            remaining = remaining[n:]

    wt = threading.Thread(target=writer, daemon=True)
    wt.start()

    parser = protocol.PacketParser()
    got = 0
    try:
        for chunk in serial_source.iter_bytes(child_name, read_timeout_s=0.05,
                                               duration_s=1.0):
            for _ in parser.feed(chunk):
                got += 1
            if got >= 1:
                break
    finally:
        wt.join(timeout=1.0)
        os.close(child_fd)
        os.close(parent_fd)

    assert got == 1, f"expected 1 packet through the adapter, got {got}"
    assert parser.drop_count == 0
