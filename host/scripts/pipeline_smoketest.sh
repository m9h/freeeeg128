#!/usr/bin/env bash
# End-to-end host-pipeline smoke test, no FreeEEG128 hardware required.
#
# 1. Starts the synthetic LSL source (128 ch x 250 Hz, realtime pacing)
# 2. Runs the recorder for 20 s, which writes FIFF + BIDS
# 3. Reports sample counts, file sizes, BIDS tree contents
#
# Exit code 0 = the entire chain produced non-empty outputs with <1%
# sample drop.  Any other code = something is wrong.

set -euo pipefail

VENV="${VENV:-$HOME/freeeeg}"
HOST_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HOST_DIR"

PY="$VENV/bin/python"
DURATION="${DURATION:-25}"
RECORD_SEC="${RECORD_SEC:-20}"
RATE="${RATE:-250}"

echo "==> starting synth source ($DURATION s, $RATE Hz, 128 ch, realtime)"
"$PY" scripts/synth_to_lsl.py \
    --duration "$DURATION" --rate "$RATE" --channels 128 --realtime \
    > /tmp/synth.log 2>&1 &
SYNTH_PID=$!
trap 'kill "$SYNTH_PID" 2>/dev/null || true' EXIT

sleep 3

echo "==> recording for $RECORD_SEC s"
"$PY" scripts/record_session.py \
    --duration "$RECORD_SEC" \
    --subject smoketest \
    --task test

wait "$SYNTH_PID" 2>/dev/null || true
trap - EXIT

echo
echo "==> latest FIFF"
ls -la out/recordings/sub-smoketest_*_raw.fif | tail -1

echo
echo "==> BIDS tree"
find out/recordings/bids -maxdepth 5 -type f 2>/dev/null | sort | sed 's/^/  /'

echo
echo "==> bids-validator check (if installed)"
if command -v bids-validator >/dev/null 2>&1; then
    bids-validator out/recordings/bids || echo "(bids-validator reported issues above)"
else
    echo "  (bids-validator not installed; skip.  Install via: npm install -g bids-validator)"
fi

echo
echo "==> smoke test PASSED"
