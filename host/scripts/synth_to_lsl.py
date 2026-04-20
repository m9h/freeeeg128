#!/usr/bin/env python3
"""Run the synthetic source → parser → LSL bridge end-to-end.

Proves the full host pipeline works without a real FreeEEG128 board.  When
the firmware is ready, the only change is the byte source: swap the
SyntheticSource generator for a pyserial.Serial read loop on /dev/ttyACM*.

Usage:
    python3 -m scripts.synth_to_lsl [--duration 30] [--rate 250] [--channels 128]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as `python3 host/scripts/synth_to_lsl.py` by adding host/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from freeeeg128 import lsl_bridge, synthetic


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=30.0, help="seconds to run")
    ap.add_argument("--rate", type=int, default=250)
    ap.add_argument("--channels", type=int, default=128)
    ap.add_argument("--realtime", action="store_true",
                    help="pace emission to sample rate (default: free-run)")
    args = ap.parse_args()

    print(f"Synthetic source: {args.channels} ch × {args.rate} Hz, {args.duration:.1f} s")

    src = synthetic.SyntheticSource(n_channels=args.channels, sample_rate_hz=args.rate)

    def byte_iter():
        for pkt in src.iter_packets(duration_s=args.duration, realtime=args.realtime):
            yield pkt

    stats = lsl_bridge.bridge(
        byte_iter(),
        n_channels=args.channels,
        sample_rate_hz=args.rate,
        duration_s=args.duration,
    )

    print()
    print("=== bridge stats ===")
    for k, v in stats.items():
        print(f"  {k:<12} {v}")
    expected = args.rate * args.duration
    dropped = expected - stats["samples"]
    print(f"  expected     {expected:.0f}")
    print(f"  pushed       {stats['samples']}")
    print(f"  missed       {dropped:.0f}")


if __name__ == "__main__":
    main()
