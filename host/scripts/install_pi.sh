#!/usr/bin/env bash
# One-shot bootstrap for Raspberry Pi OS 64-bit Lite.
# Idempotent: safe to re-run.

set -euo pipefail

VENV="${VENV:-$HOME/freeeeg}"

echo "==> apt packages"
sudo apt update
sudo apt install -y \
  git build-essential \
  python3 python3-venv python3-dev python3-pip \
  libopenblas-dev \
  libusb-1.0-0 \
  curl

echo "==> creating venv at $VENV"
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
pip install --upgrade pip wheel

echo "==> core stack"
pip install \
  "numpy>=1.26" \
  "scipy>=1.12" \
  "pylsl>=1.16" \
  "brainflow>=5.14" \
  "mne>=1.8" \
  "pyserial>=3.5" \
  "fastapi>=0.115" \
  "uvicorn>=0.32"

echo "==> optional: eeg-expy (may take a while, has heavy deps)"
pip install "eeg-expy>=0.1.0" || {
  echo "WARN: eeg-expy install failed; benchmarks involving it will be skipped."
}

echo "==> smoke test"
python - <<'PY'
import numpy, scipy, pylsl, brainflow, mne
print(f"numpy     {numpy.__version__}")
print(f"scipy     {scipy.__version__}")
print(f"pylsl     {pylsl.library_version()}")
print(f"brainflow {brainflow.__version__ if hasattr(brainflow,'__version__') else '?'}")
print(f"mne       {mne.__version__}")
PY

echo
echo "Done.  Activate the venv with:  source $VENV/bin/activate"
echo "Then:  make bench"
