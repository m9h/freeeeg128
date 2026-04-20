"""LSL loopback: outlet + inlet round-trip on localhost.

Matches the production path: FreeEEG128 Python host publishes an LSL outlet,
MNE Scan / LabRecorder / Timeflux reads it.
"""

from __future__ import annotations

import time

import numpy as np
from pylsl import StreamInfo, StreamInlet, StreamOutlet, resolve_byprop

from . import emit

CH = 128
FS = 250
N_SAMPLES = FS * 60  # 60 s of data


def main() -> None:
    info = StreamInfo("freeeeg128-bench", "EEG", CH, FS, "float32", "bench-dev")
    outlet = StreamOutlet(info, chunk_size=25)

    streams = resolve_byprop("name", "freeeeg128-bench", timeout=5.0)
    if not streams:
        emit("lsl.resolve", -1, "status")
        return
    inlet = StreamInlet(streams[0], max_buflen=120)

    emit("lsl.resolve", 1, "status")

    # Warmup: prime the inlet/outlet pair.  The first pull_chunk after
    # StreamInlet construction can block on LSL's own handshake/buffer
    # setup, producing a deceptive "1 s max latency" datapoint that isn't
    # representative of steady state.  Push 100 samples and drain.
    rng = np.random.default_rng(0)
    batch = 25  # 100 ms
    for _ in range(4):
        warm = rng.standard_normal((batch, CH)).astype(np.float32)
        for row in warm:
            outlet.push_sample(row)
        inlet.pull_chunk(timeout=1.0, max_samples=batch)

    # Timed loop
    n_batches = N_SAMPLES // batch
    lat_ms = np.empty(n_batches, dtype=np.float64)
    t0 = time.perf_counter()
    for i in range(n_batches):
        block = rng.standard_normal((batch, CH)).astype(np.float32)
        ts_push = time.perf_counter()
        for row in block:
            outlet.push_sample(row)
        inlet.pull_chunk(timeout=0.5, max_samples=batch)
        lat_ms[i] = (time.perf_counter() - ts_push) * 1000
    wall = time.perf_counter() - t0

    emit("lsl.latency_p50_ms", round(float(np.percentile(lat_ms, 50)), 3), "ms")
    emit("lsl.latency_p95_ms", round(float(np.percentile(lat_ms, 95)), 3), "ms")
    emit("lsl.latency_max_ms", round(float(np.max(lat_ms)), 3), "ms")
    emit("lsl.throughput_samples_per_s", round(N_SAMPLES / wall, 1), "sps")
    emit("lsl.wall_s", round(wall, 2), "s")


if __name__ == "__main__":
    main()
