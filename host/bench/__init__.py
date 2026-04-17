"""FreeEEG128 host benchmarks.

Each bench module exposes a ``main()`` that prints CSV rows of the form:
    metric,value,unit,timestamp,host
and can be run with ``python -m bench.bench_xxx``.
"""

from __future__ import annotations

import socket
import time
from contextlib import contextmanager

HOST = socket.gethostname()


def emit(metric: str, value: float | int, unit: str) -> None:
    """Print one CSV row to stdout."""
    ts = int(time.time())
    print(f"{metric},{value},{unit},{ts},{HOST}", flush=True)


@contextmanager
def timed(metric: str, unit: str = "ms"):
    """Context manager timing the enclosed block and emitting ``metric``."""
    t0 = time.perf_counter()
    yield
    dt = (time.perf_counter() - t0) * (1000 if unit == "ms" else 1)
    emit(metric, round(dt, 3), unit)
