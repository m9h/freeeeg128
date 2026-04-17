#!/usr/bin/env bash
# Runs every benchmark once, captures output to a timestamped CSV, and
# also measures wall power via a UM25C-like meter if a helper script is present.

set -euo pipefail
cd "$(dirname "$0")/.."

source "${VENV:-$HOME/freeeeg}/bin/activate"

mkdir -p results
OUT="results/bench-$(hostname -s)-$(date +%Y%m%d-%H%M%S).csv"

{
  echo "metric,value,unit,timestamp,host"
  python -m bench.bench_python
  python -m bench.bench_lsl
  python -m bench.bench_brainflow
  python -m bench.bench_mne
  python -m bench.bench_eegexpy || true
} | tee "$OUT"

echo
echo "saved -> $OUT"
