"""Record a running LSL stream to disk.

Two output formats:
- FIFF (``.fif``) via MNE-Python — native for MNE/MNE-CPP.
- BIDS-EEG directory tree via MNE-BIDS — for OpenNeuro / NEMAR / re-use.

Design: a single ``LSLRecorder`` gathers samples from the inlet into a
growing buffer; it can be flushed to either format.  A session typically
runs ``start()`` → do-stimulus-or-recording → ``stop()`` → ``to_fif()``
and/or ``to_bids()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from pylsl import StreamInlet, resolve_byprop


@dataclass
class LSLRecorder:
    """Drain an LSL outlet into an in-memory buffer."""

    stream_name: str = "FreeEEG128"
    stream_type: str = "EEG"
    resolve_timeout: float = 5.0
    max_buf_samples: int = 250 * 60 * 60  # 1 hour @ 250 Hz default
    chunk_size: int = 250                 # ~1 s at 250 Hz
    verbose: bool = False

    inlet: Optional[StreamInlet] = None
    info: Optional[object] = None
    n_channels: int = 0
    sample_rate_hz: float = 0.0
    _buffer: list = field(default_factory=list)     # list of (samples_CxN, timestamps_N)
    _started: bool = False
    _finished: bool = False

    def connect(self) -> None:
        streams = resolve_byprop("name", self.stream_name, timeout=self.resolve_timeout)
        if not streams:
            raise RuntimeError(
                f"LSL stream name={self.stream_name!r} not found within "
                f"{self.resolve_timeout:.1f} s"
            )
        self.inlet = StreamInlet(streams[0], max_buflen=360)
        self.info = self.inlet.info()
        self.n_channels = self.info.channel_count()
        self.sample_rate_hz = self.info.nominal_srate()
        if self.verbose:
            print(f"[recorder] connected to {self.stream_name} "
                  f"({self.n_channels} ch @ {self.sample_rate_hz} Hz)")

    def drain_once(self) -> int:
        """Pull all currently-available samples.  Returns n samples appended."""
        if self.inlet is None:
            raise RuntimeError("connect() first")
        samples, ts = self.inlet.pull_chunk(
            timeout=0.0, max_samples=self.chunk_size
        )
        n = len(samples)
        if n:
            arr = np.asarray(samples, dtype=np.float32).T  # (C, N)
            ts_arr = np.asarray(ts, dtype=np.float64)
            self._buffer.append((arr, ts_arr))
        return n

    def record_for(self, duration_s: float, poll_hz: float = 50.0) -> int:
        """Drain for the given wall-clock duration.  Returns total samples."""
        import time
        t_end = time.monotonic() + duration_s
        total = 0
        dt = 1.0 / poll_hz
        while time.monotonic() < t_end:
            total += self.drain_once()
            time.sleep(dt)
        # final drain
        total += self.drain_once()
        self._finished = True
        return total

    def as_arrays(self) -> tuple[np.ndarray, np.ndarray]:
        """Return (data CxN, timestamps N) for all buffered samples."""
        if not self._buffer:
            return np.zeros((self.n_channels, 0), dtype=np.float32), np.zeros(0)
        data = np.concatenate([b[0] for b in self._buffer], axis=1)
        ts   = np.concatenate([b[1] for b in self._buffer])
        return data, ts

    # ---- writers ----------------------------------------------------------

    def to_raw(self, ch_names: list[str] | None = None):
        """Build an ``mne.io.Raw`` from the recorded buffer (units: µV)."""
        import mne
        data, _ = self.as_arrays()
        if ch_names is None:
            ch_names = [f"ch{i:03d}" for i in range(self.n_channels)]
        info = mne.create_info(
            ch_names=ch_names[: self.n_channels],
            sfreq=self.sample_rate_hz,
            ch_types="eeg",
        )
        # LSL samples are in µV by convention here; MNE wants Volts
        return mne.io.RawArray(data * 1e-6, info, verbose=False)

    def to_fif(self, path: str | Path, ch_names: list[str] | None = None) -> Path:
        raw = self.to_raw(ch_names=ch_names)
        path = Path(path)
        raw.save(path, overwrite=True)
        return path

    def to_bids(self,
                bids_root: str | Path,
                subject: str,
                session: str = "01",
                task: str = "rest",
                line_freq: float = 60.0,
                ch_names: list[str] | None = None) -> Path:
        """Write the recorded buffer as a BIDS-EEG dataset."""
        from mne_bids import BIDSPath, write_raw_bids

        raw = self.to_raw(ch_names=ch_names)
        raw.info["line_freq"] = line_freq

        bids_root = Path(bids_root)
        bids_path = BIDSPath(
            subject=subject, session=session, task=task,
            datatype="eeg", root=bids_root,
        )
        write_raw_bids(raw, bids_path, overwrite=True, verbose=False,
                       allow_preload=True, format="EDF")
        return bids_path.root
