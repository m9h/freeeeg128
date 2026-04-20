"""Replay a raw captured byte stream from disk.

Pair with ``serial_source.iter_bytes(..., tee_path='capture.bin')`` to
first record a live session, then replay it offline with the rest of the
pipeline unchanged.  Useful for regression testing the parser, quality
dashboard, and recorder without needing the device online.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterator


def iter_bytes(path: str | Path,
               *,
               chunk_size: int = 4096,
               realtime_rate_bps: int | None = None) -> Iterator[bytes]:
    """Yield byte chunks from ``path``.

    ``realtime_rate_bps``: if given, paces emission to roughly that
    bytes-per-second rate (approximates the original stream cadence).
    """
    path = Path(path)
    with path.open("rb") as f:
        t_start = time.monotonic()
        bytes_emitted = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                return
            yield chunk
            bytes_emitted += len(chunk)
            if realtime_rate_bps:
                target = bytes_emitted / realtime_rate_bps
                delay = target - (time.monotonic() - t_start)
                if delay > 0:
                    time.sleep(delay)
