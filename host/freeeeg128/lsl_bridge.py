"""Bridge: reads FreeEEG128 framed packets from any byte source and
republishes the EEG stream as an LSL outlet.

This is the host-side component on the Pi Zero 2W companion.  The byte
source can be a synthetic generator (pre-real-device development), a
``pyserial.Serial`` opened against the USB-CDC tty (real device), or a
pre-recorded file of framed bytes (replay).
"""

from __future__ import annotations

import time
from typing import Iterable, Iterator

import numpy as np
from pylsl import StreamInfo, StreamOutlet, local_clock

from . import protocol


DEFAULT_STREAM_NAME = "FreeEEG128"
DEFAULT_STREAM_TYPE = "EEG"


def make_outlet(n_channels: int = 128,
                sample_rate_hz: int = 250,
                name: str = DEFAULT_STREAM_NAME,
                source_id: str = "freeeeg128-0",
                channel_labels: list[str] | None = None) -> StreamOutlet:
    info = StreamInfo(name=name, type=DEFAULT_STREAM_TYPE,
                      channel_count=n_channels,
                      nominal_srate=sample_rate_hz,
                      channel_format="float32",
                      source_id=source_id)
    chans = info.desc().append_child("channels")
    labels = channel_labels or [f"ch{i:03d}" for i in range(n_channels)]
    for label in labels[:n_channels]:
        c = chans.append_child("channel")
        c.append_child_value("label", label)
        c.append_child_value("unit", "microvolts")
        c.append_child_value("type", "EEG")
    return StreamOutlet(info, chunk_size=25, max_buffered=360)


def bytes_iter_to_packets(byte_iter: Iterable[bytes]) -> Iterator[protocol.Packet]:
    """Feed chunks through a PacketParser and yield complete packets."""
    parser = protocol.PacketParser()
    for chunk in byte_iter:
        for pkt in parser.feed(chunk):
            yield pkt


def bridge(byte_iter: Iterable[bytes], *,
           outlet: StreamOutlet | None = None,
           n_channels: int = 128,
           sample_rate_hz: int = 250,
           gain: int = 32,
           vref_v: float = 1.25,
           duration_s: float | None = None,
           log_every_s: float = 5.0) -> dict:
    """Pipe framed bytes → LSL samples.

    Returns stats: samples pushed, packets seen, parser drops, wall time.
    """
    own_outlet = outlet is None
    if own_outlet:
        outlet = make_outlet(n_channels=n_channels, sample_rate_hz=sample_rate_hz)

    fullscale_inv = (vref_v * 1_000_000.0) / (((1 << 23) - 1) * gain)
    t_start = time.monotonic()
    t_log = t_start
    samples = 0
    packets = 0
    parser = protocol.PacketParser()

    try:
        for chunk in byte_iter:
            for pkt in parser.feed(chunk):
                packets += 1
                if pkt.ptype != protocol.PacketType.EEG_FRAME:
                    continue
                n_ch, n_smp, flags, sr_hz, adc_status, samples_u24 = protocol.decode_eeg_frame(
                    pkt.payload
                )
                # Vectorize int24 → float32 µV
                u = np.frombuffer(samples_u24, dtype=np.uint8).reshape(n_ch, n_smp, 3)
                raw = (u[:, :, 0].astype(np.int32) << 16
                       | u[:, :, 1].astype(np.int32) << 8
                       | u[:, :, 2].astype(np.int32))
                mask = raw & 0x800000
                raw = np.where(mask != 0, raw - 0x1000000, raw).astype(np.int32)
                uv = (raw.astype(np.float32) * fullscale_inv).T  # (n_smp, n_ch)
                outlet.push_chunk(uv.tolist(), timestamp=local_clock(), pushthrough=True)
                samples += n_smp

            now = time.monotonic()
            if now - t_log >= log_every_s:
                t_log = now
                elapsed = now - t_start
                print(f"[bridge] t={elapsed:6.1f}s  samples={samples}  "
                      f"packets={packets}  drops={parser.drop_count}  "
                      f"sps={samples / max(elapsed, 1e-9):.1f}")

            if duration_s is not None and (now - t_start) >= duration_s:
                break
    finally:
        if own_outlet:
            del outlet  # flush

    return {
        "wall_s": time.monotonic() - t_start,
        "samples": samples,
        "packets": packets,
        "drops": parser.drop_count,
        "bytes": parser.byte_count,
    }
