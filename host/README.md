# freeeeg128 — host-side Python stack

Runs on the Raspberry Pi Zero 2W companion of the FreeEEG128 beta, or on any
Linux / macOS host for development. The same package reads both the BrainFlow
synthetic board (pre-validation) and the FreeEEG128 USB-CDC stream (once
firmware is ready).

## Why this directory exists

The beta architecture has a Raspberry Pi Zero 2W sharing a shoulder-bag
enclosure with the FreeEEG128 PCB (see `../ENCLOSURE.md` and `../ROADMAP.md`
§B0.1). This directory holds the code that runs on that Pi:

- Synthetic-data benchmarks (before real device is ready).
- Capture client that reads the FreeEEG128 framed USB-CDC stream (once
  `docs/packet-format.md` is locked).
- LSL outlet republishing the stream for MNE Scan, BrainFlow, EEG-ExPy,
  Timeflux, LabRecorder, etc.
- FastAPI web UI for session control and quality monitoring.
- BIDS-EEG / FIFF writers.

## Pi Zero 2W setup

Tested on **Raspberry Pi OS 64-bit Lite, Bookworm** (2026 builds).

### 1. Flash the OS

Use Raspberry Pi Imager (macOS / Windows / Linux):

- Device: `Raspberry Pi Zero 2 W`
- OS: `Raspberry Pi OS (64-bit) Lite`
- Storage: 32 GB microSD, Class 10 or better
- Advanced options (gear icon):
  - Enable SSH with password authentication
  - Set hostname: `freeeeg-pi`
  - Set username: `morgan` (or your preferred)
  - Configure Wi-Fi with your SSID + password
  - Set locale

### 2. First boot and install

Boot the Pi, SSH in:

```bash
ssh morgan@freeeeg-pi.local
```

Clone this repo and run the installer:

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/<you>/freeeeg128.git
cd freeeeg128/host
./scripts/install_pi.sh
```

The installer creates a venv at `~/freeeeg`, installs NumPy, SciPy, pylsl,
BrainFlow, MNE-Python, and optionally EEG-ExPy, then runs a quick smoke test.

### 3. Run the benchmark suite

```bash
source ~/freeeeg/bin/activate
cd ~/freeeeg128/host
make bench
```

Results are appended to `results/bench-<hostname>-<date>.csv` so you can
compare across OS choices, Pi models, and (eventually) real-device runs.

## Benchmarks

| Bench | File | What it measures |
| --- | --- | --- |
| Python / NumPy speed | `bench/bench_python.py` | 128×25 000 complex FFT time, dot product, memory BW proxy |
| LSL loopback | `bench/bench_lsl.py` | Outlet + inlet round-trip latency and throughput for 128-ch float32 at 250 Hz |
| BrainFlow synthetic | `bench/bench_brainflow.py` | `SYNTHETIC_BOARD` streaming at 250 Hz for 60 s; drop count |
| MNE online preprocessing | `bench/bench_mne.py` | Bandpass filter + ICA on 5-min synthetic epoch |
| EEG-ExPy pipeline | `bench/bench_eegexpy.py` | Visual-P300 paradigm runtime with synthetic backend (skipped if `eeg-expy` not installed) |

Each prints one line of JSON per metric to stdout; `make bench` pipes all of
them into one CSV.

## Targets (Pi Zero 2W, stock Raspberry Pi OS Lite, 2S 18650 on USB-C PD)

These are sanity targets we establish once so we can tell when something
regresses later. Fill in the first time you run them.

| Bench | Target | Measured (Pi Zero 2W) | Measured (laptop) |
| --- | --- | --- | --- |
| FFT 128×25 000 complex | < 50 ms | | |
| LSL push+pull 100 samples × 128 ch | < 20 ms round-trip | | |
| BrainFlow synth 60 s @ 250 Hz | 0 drops | | |
| MNE bandpass + ICA, 5 min | < 30 s | | |
| Wall power at USB meter, 10-min idle loopback | < 2 W | | |
| Wall power, 10-min active capture | < 3 W | | |

## Directory layout

```
host/
├── README.md                       ← this file
├── Makefile                        ← make bench, make install, make fmt
├── pyproject.toml                  ← package metadata, dependencies
├── bench/
│   ├── __init__.py
│   ├── bench_python.py
│   ├── bench_lsl.py
│   ├── bench_brainflow.py
│   ├── bench_mne.py
│   └── bench_eegexpy.py
├── scripts/
│   ├── install_pi.sh               ← apt + pip bootstrap
│   └── run_all_bench.sh            ← runs every bench and appends to results/
└── results/                        ← .csv files per run, committed so we can diff across revisions
```

Future additions:

```
├── freeeeg128/                     ← the actual capture client package
│   ├── transport/                  ← USB-CDC reader, LSL outlet
│   ├── protocol/                   ← framed-packet parser (mirrors firmware docs/packet-format.md)
│   ├── services/                   ← impedance, quality monitor, BIDS writer, FIFF writer
│   └── ui/                         ← FastAPI web UI
```

## Running without a Pi

Everything works on a laptop too:

```bash
python3 -m venv ~/freeeeg
source ~/freeeeg/bin/activate
pip install -e .
make bench
```

Useful during development — iterate on the Mac, push to the Pi over SSH for
final timing numbers.

## License

AGPL-3.0 (matches upstream NeuroIDSS firmware).
