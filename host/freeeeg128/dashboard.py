"""FastAPI quality dashboard: live operator view of a FreeEEG128 LSL stream.

- Pulls samples from an LSL outlet (any source: the real device, the
  synthetic source, or a replay file — they all look the same to LSL).
- Maintains a 2-second rolling buffer per channel.
- Computes per-channel broadband-RMS, alpha-band RMS, dominant frequency,
  and a green / yellow / red / grey quality code once per second.
- Serves a single-page browser UI at ``/`` plus an SSE stream at
  ``/events`` that pushes JSON updates so the page can re-render live
  without JS-frameworks.

Run from Pi:
    python3 -m freeeeg128.dashboard --port 8000
Open:
    http://<pi-hostname>.local:8000/

Inspired by Vivancos 2023 §3.1 paper's green/red PSD dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pylsl import StreamInlet, resolve_byprop

from . import quality


# --------------------------------------------------------------------------- #
# Background LSL thread: keeps the rolling buffer and per-channel quality up
# to date.  Main thread serves HTTP and snapshots the latest state.
# --------------------------------------------------------------------------- #

class DashState:
    def __init__(self, window_s: float = 2.0) -> None:
        self.window_s = window_s
        self.connected = False
        self.stream_name = ""
        self.n_channels = 0
        self.sample_rate = 0.0
        self.channel_labels: list[str] = []
        self.buffer: np.ndarray | None = None   # (C, N)
        self.buf_len: int = 0
        self.samples_total = 0
        self.drops_total = 0
        self.packets_rx = 0
        self.last_lsl_ts = 0.0
        self.started_at = time.time()
        self.quality: list[quality.QualityResult] = []
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "connected": self.connected,
                "stream_name": self.stream_name,
                "n_channels": self.n_channels,
                "sample_rate": self.sample_rate,
                "channel_labels": self.channel_labels,
                "samples_total": self.samples_total,
                "drops_total": self.drops_total,
                "packets_rx": self.packets_rx,
                "uptime_s": time.time() - self.started_at,
                "quality": [
                    {
                        "code": int(q.code),
                        "rms": round(q.broadband_uv_rms, 3),
                        "alpha": round(q.alpha_uv_rms, 3),
                        "dominant": round(q.dominant_hz, 2),
                    }
                    for q in self.quality
                ],
            }


def _lsl_reader_thread(state: DashState, stream_name: str,
                       resolve_timeout: float = 5.0) -> None:
    streams = resolve_byprop("name", stream_name, timeout=resolve_timeout)
    if not streams:
        with state.lock:
            state.connected = False
        return
    inlet = StreamInlet(streams[0], max_buflen=360)
    info = inlet.info()
    n_ch = info.channel_count()
    sr = info.nominal_srate() or 250.0
    buf_len = max(1, int(sr * state.window_s))
    buf = np.zeros((n_ch, buf_len), dtype=np.float32)
    write_idx = 0
    samples_total = 0

    # Extract channel labels if present
    labels: list[str] = []
    try:
        ch = info.desc().child("channels").child("channel")
        for _ in range(n_ch):
            labels.append(ch.child_value("label") or f"ch{len(labels):03d}")
            ch = ch.next_sibling()
    except Exception:
        labels = [f"ch{i:03d}" for i in range(n_ch)]

    with state.lock:
        state.connected = True
        state.stream_name = stream_name
        state.n_channels = n_ch
        state.sample_rate = sr
        state.channel_labels = labels
        state.buffer = buf
        state.buf_len = buf_len

    last_assess = 0.0
    while not state.stop_event.is_set():
        samples, _ts = inlet.pull_chunk(timeout=0.1, max_samples=250)
        if samples:
            arr = np.asarray(samples, dtype=np.float32).T  # (C, N)
            n = arr.shape[1]
            # Ring-buffer write
            end = write_idx + n
            if end <= buf_len:
                buf[:, write_idx:end] = arr
            else:
                first = buf_len - write_idx
                buf[:, write_idx:] = arr[:, :first]
                buf[:, : n - first] = arr[:, first:]
            write_idx = (write_idx + n) % buf_len
            samples_total += n
            with state.lock:
                state.samples_total = samples_total
                state.packets_rx += 1

        # Re-assess quality at most once per second
        now = time.monotonic()
        if now - last_assess >= 1.0 and samples_total >= buf_len:
            last_assess = now
            # Assemble a contiguous view
            ordered = np.concatenate(
                [buf[:, write_idx:], buf[:, :write_idx]], axis=1
            )
            q = quality.assess_array(ordered, sr)
            with state.lock:
                state.quality = q


# --------------------------------------------------------------------------- #
# HTTP layer
# --------------------------------------------------------------------------- #

_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>FreeEEG128 — quality monitor</title>
<style>
 body { font-family: -apple-system, 'SF Mono', Menlo, monospace; margin: 1rem; background: #0e1116; color: #c9d1d9; }
 h1 { margin: 0 0 .5rem 0; font-size: 1.1rem; color: #58a6ff; }
 .topbar { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: .75rem; font-size: .85rem; }
 .topbar span { background:#161b22; padding:.25rem .6rem; border-radius:4px; }
 .grid { display: grid; grid-template-columns: repeat(16, 1fr); gap: 2px; }
 .cell { aspect-ratio: 1/1; border-radius: 2px; font-size: 9px; text-align: center;
         display: flex; flex-direction: column; justify-content: center; align-items: center;
         color: #111; cursor: help; overflow: hidden; padding: 1px; }
 .q0 { background: #33cc66; } /* green  */
 .q1 { background: #e3b341; } /* yellow */
 .q2 { background: #e5534b; color:#fff; } /* red */
 .q3 { background: #30363d; color:#999; } /* grey */
 .cell small { font-size: 8px; opacity: .75; }
 .legend { display:flex; gap:.75rem; margin-top:.75rem; font-size:.8rem; }
 .legend span.sw { display:inline-block; width:10px; height:10px; margin-right:.3rem; border-radius:2px; vertical-align: middle; }
 footer { margin-top: 1rem; font-size: .75rem; color: #6e7681; }
</style>
</head><body>
<h1>FreeEEG128 — quality monitor</h1>
<div class="topbar">
 <span id="state">connecting…</span>
 <span id="sr"></span>
 <span id="nch"></span>
 <span id="samples"></span>
 <span id="drops"></span>
 <span id="uptime"></span>
</div>
<div class="grid" id="grid"></div>
<div class="legend">
 <span><span class="sw q0"></span>good (RMS &gt; 0.5 µV)</span>
 <span><span class="sw q1"></span>marginal</span>
 <span><span class="sw q2"></span>bad / flat / saturated</span>
 <span><span class="sw q3"></span>no data yet</span>
</div>
<footer>Live at 1 Hz via SSE.  Green/red gate follows Vivancos 2023 §3.1.</footer>
<script>
const grid = document.getElementById('grid');
const es = new EventSource('/events');
es.onmessage = (ev) => {
  const s = JSON.parse(ev.data);
  document.getElementById('state').textContent = s.connected ? ('● ' + s.stream_name) : '○ waiting for outlet';
  document.getElementById('state').style.color = s.connected ? '#33cc66' : '#e5534b';
  document.getElementById('sr').textContent = s.sample_rate.toFixed(0) + ' Hz';
  document.getElementById('nch').textContent = s.n_channels + ' ch';
  document.getElementById('samples').textContent = s.samples_total.toLocaleString() + ' samples';
  document.getElementById('drops').textContent = s.drops_total + ' drops';
  document.getElementById('uptime').textContent = Math.floor(s.uptime_s) + ' s up';
  if (grid.childElementCount !== s.n_channels) {
    grid.innerHTML = '';
    for (let i = 0; i < s.n_channels; i++) {
      const d = document.createElement('div');
      d.className = 'cell q3';
      d.id = 'c' + i;
      grid.appendChild(d);
    }
  }
  for (let i = 0; i < s.quality.length; i++) {
    const c = document.getElementById('c' + i);
    if (!c) continue;
    const q = s.quality[i];
    c.className = 'cell q' + q.code;
    const label = (s.channel_labels[i] || ('ch' + i)).replace(/^ch/, '');
    c.innerHTML = label + '<small>' + q.rms.toFixed(1) + '</small>';
    c.title = (s.channel_labels[i] || 'ch' + i) + '\\nRMS ' + q.rms.toFixed(2) + ' µV'
            + '\\nα-RMS ' + q.alpha.toFixed(2) + ' µV'
            + '\\ndominant ' + q.dominant.toFixed(1) + ' Hz';
  }
};
</script>
</body></html>
"""


def create_app(state: DashState) -> FastAPI:
    app = FastAPI(title="FreeEEG128 quality monitor")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:  # noqa: D401
        return HTMLResponse(_HTML)

    @app.get("/events")
    async def events():  # noqa: D401
        async def gen():
            while True:
                s = state.snapshot()
                yield f"data: {json.dumps(s)}\n\n"
                await asyncio.sleep(1.0)
        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.get("/state")
    async def full_state():
        return state.snapshot()

    return app


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stream", default="FreeEEG128", help="LSL stream name to bind to")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--window-s", type=float, default=2.0,
                    help="rolling window (s) for quality assessment")
    args = ap.parse_args()

    import uvicorn

    state = DashState(window_s=args.window_s)
    reader = threading.Thread(target=_lsl_reader_thread,
                              args=(state, args.stream),
                              daemon=True, name="lsl-reader")
    reader.start()

    app = create_app(state)
    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    finally:
        state.stop_event.set()


if __name__ == "__main__":
    main()
