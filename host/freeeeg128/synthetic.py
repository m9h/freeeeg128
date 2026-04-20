"""Pure-Python synthetic source emitting FreeEEG128 framed packets.

Replaces BrainFlow's SYNTHETIC_BOARD for development work on aarch64 hosts
(the BrainFlow 5.21 wheel for aarch64 is broken).  Generates plausible-
looking EEG: pink noise + alpha band + a 50/60 Hz line tone, encoded into
the exact wire format defined in docs/packet-format.md so the same parser
handles synthetic and real streams.
"""

from __future__ import annotations

import math
import os
import struct
import time
from dataclasses import dataclass, field

import numpy as np

from . import protocol


@dataclass
class SyntheticSource:
    """Emits EEG_FRAME packets at the configured sample rate.

    Each channel gets a unique noise seed so channels are independent.
    The generator advances its internal monotonic µs clock by 1/sr per
    sample, so device-side timing is deterministic regardless of wall clock.
    """
    n_channels: int = 128
    sample_rate_hz: int = 250
    gain: int = 32
    vref_v: float = 1.25

    # Signal shaping
    alpha_uv_pp: float = 20.0       # peak-to-peak alpha amplitude
    alpha_hz: float = 10.0
    pink_uv_rms: float = 3.0        # pink-noise RMS per channel
    line_uv_pp: float = 2.0         # residual 50/60 Hz line tone
    line_hz: float = 60.0

    # Firmware emulation
    sr_hz_field: int = 0            # defaults to sample_rate_hz when 0
    flags: int = 0

    # Internal state
    _seq: int = 0
    _ts_us: int = 0
    _sample_counter: int = 0
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(0))
    _pink_state: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        if self.sr_hz_field == 0:
            self.sr_hz_field = self.sample_rate_hz
        # Per-channel pink-noise state (4-pole Paul Kellett approximation)
        self._pink_state = np.zeros((self.n_channels, 7), dtype=np.float64)
        self._ts_us = int(time.monotonic_ns() // 1000)

    def _pink(self) -> np.ndarray:
        """Generate one sample of per-channel pink noise (µV)."""
        w = self._rng.standard_normal(self.n_channels)
        s = self._pink_state
        s[:, 0] = 0.99886 * s[:, 0] + w * 0.0555179
        s[:, 1] = 0.99332 * s[:, 1] + w * 0.0750759
        s[:, 2] = 0.96900 * s[:, 2] + w * 0.1538520
        s[:, 3] = 0.86650 * s[:, 3] + w * 0.3104856
        s[:, 4] = 0.55000 * s[:, 4] + w * 0.5329522
        s[:, 5] = -0.7616 * s[:, 5] - w * 0.0168980
        out = s[:, :6].sum(axis=1) + w * 0.5362 + s[:, 6]
        s[:, 6] = w * 0.115926
        return out * self.pink_uv_rms

    def next_uv_sample(self) -> np.ndarray:
        """Return the next per-channel sample in µV (shape (n_channels,))."""
        t = self._sample_counter / self.sample_rate_hz
        alpha = (self.alpha_uv_pp * 0.5) * math.sin(2 * math.pi * self.alpha_hz * t)
        line  = (self.line_uv_pp  * 0.5) * math.sin(2 * math.pi * self.line_hz  * t)
        # Per-channel alpha phase jitter so channels don't all sing in unison
        chan_phase = np.linspace(0, 2 * math.pi, self.n_channels, endpoint=False)
        alpha_v = alpha * np.cos(chan_phase)  # rough topography proxy
        x = self._pink() + alpha_v + line
        self._sample_counter += 1
        return x

    def uv_to_int24(self, uv: np.ndarray) -> np.ndarray:
        """Inverse of protocol.raw_to_uv — produce int24 counts."""
        fullscale = (1 << 23) - 1
        counts = uv * (fullscale * self.gain) / (self.vref_v * 1_000_000.0)
        # Clip to int24 range and round
        counts = np.clip(np.rint(counts), -(1 << 23), (1 << 23) - 1).astype(np.int32)
        return counts

    @staticmethod
    def _int32_to_be24(counts: np.ndarray) -> bytes:
        """Serialize int32 counts as big-endian int24 bytes."""
        u32 = counts.astype(np.int32).view(np.uint32) & 0xFFFFFF
        out = bytearray(len(u32) * 3)
        out[0::3] = ((u32 >> 16) & 0xFF).astype(np.uint8).tobytes()
        out[1::3] = ((u32 >> 8)  & 0xFF).astype(np.uint8).tobytes()
        out[2::3] = (u32 & 0xFF).astype(np.uint8).tobytes()
        return bytes(out)

    def next_packet(self) -> bytes:
        """Produce one EEG_FRAME packet (n_samp=1) as framed bytes."""
        uv = self.next_uv_sample()
        counts = self.uv_to_int24(uv)
        samples_u24 = self._int32_to_be24(counts)
        payload = protocol.encode_eeg_frame(
            samples_u24=samples_u24,
            n_ch=self.n_channels,
            n_smp=1,
            sr_hz=self.sr_hz_field,
            flags=self.flags,
            adc_status=b"\x00" * 16,
        )
        pkt = protocol.encode(
            ptype=protocol.PacketType.EEG_FRAME,
            seq=self._seq,
            ts_us=self._ts_us,
            payload=payload,
        )
        self._seq = (self._seq + 1) & 0xFFFFFFFF
        self._ts_us += 1_000_000 // self.sample_rate_hz
        return pkt

    def iter_packets(self, duration_s: float | None = None, *,
                     realtime: bool = False):
        """Yield packets indefinitely or for ``duration_s`` seconds.

        If ``realtime`` is True, yields are paced to the sample-rate clock
        using time.monotonic so the stream runs at wall-clock rate.
        """
        n = int(self.sample_rate_hz * duration_s) if duration_s is not None else None
        t0 = time.monotonic()
        i = 0
        while n is None or i < n:
            pkt = self.next_packet()
            if realtime:
                target = t0 + (i + 1) / self.sample_rate_hz
                delay = target - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
            yield pkt
            i += 1
