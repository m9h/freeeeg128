#!/usr/bin/env python3
"""Record an LSL stream for a fixed duration, write to FIFF + BIDS.

Designed to be run alongside a source that's already publishing to LSL —
either ``synth_to_lsl.py`` (synthetic) or the real FreeEEG128 host client.

Usage:
    python3 scripts/record_session.py --duration 30 --subject demo
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from freeeeg128.recorder import LSLRecorder


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=30.0)
    ap.add_argument("--stream", default="FreeEEG128")
    ap.add_argument("--out-dir", default="out/recordings", type=Path)
    ap.add_argument("--subject", default="demo")
    ap.add_argument("--session", default="01")
    ap.add_argument("--task", default="rest")
    ap.add_argument("--skip-bids", action="store_true")
    args = ap.parse_args()

    rec = LSLRecorder(stream_name=args.stream, verbose=True)
    rec.connect()

    print(f"[record] draining {args.duration:.1f} s from {args.stream!r}…")
    t0 = time.monotonic()
    n = rec.record_for(args.duration)
    wall = time.monotonic() - t0
    print(f"[record] got {n} samples in {wall:.2f} s "
          f"(expected ~{int(rec.sample_rate_hz * args.duration)})")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    fif_path = args.out_dir / f"sub-{args.subject}_ses-{args.session}_task-{args.task}_{ts}_raw.fif"
    rec.to_fif(fif_path)
    print(f"[record] wrote FIFF  {fif_path}  ({fif_path.stat().st_size / 1024:.0f} KB)")

    if not args.skip_bids:
        bids_root = args.out_dir / "bids"
        try:
            written = rec.to_bids(
                bids_root=bids_root,
                subject=args.subject,
                session=args.session,
                task=args.task,
            )
            print(f"[record] wrote BIDS dataset at {written}")
        except Exception as e:
            print(f"[record] BIDS write failed: {e.__class__.__name__}: {e}")


if __name__ == "__main__":
    main()
