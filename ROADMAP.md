# FreeEEG128 — Alpha → Beta Roadmap

Two tracks in parallel. The alpha is in hand now; the beta is a future board rev
that adds an **ESP32-S3 co-processor** (WiFi/BLE, LSL, CircuitPython, STEMMA QT)
while keeping the STM32H743ZI as the acquisition engine.

MCU choice is settled — see `feedback_freeeeg128_mcu.md` in memory.

---

## What carries over (alpha → beta)

| Carries 1:1                                                              | Needs re-work                                           |
| ------------------------------------------------------------------------ | -------------------------------------------------------- |
| ADS131M08 driver (SPI + DRDY + CRC)                                       | Host transport (USB-CDC → STM32↔ESP32 SPI/UART bridge)   |
| TIM1/TIM8 DMA sample-sync cascade                                         | USB re-enumeration / power-up handshake                  |
| LSM6DS3 IMU driver                                                        | Board pinmap (some pins move for the new bridge + radio) |
| SDMMC + FatFS logging layer                                               | DFU pathway (ESP-side OTA replaces STM DFU user-surface) |
| Framed packet format (seq, µs timestamp, per-ADC status, CRC)             | —                                                        |
| Host command protocol (config, start/stop, impedance)                     | —                                                        |
| Channel/capability descriptor                                             | —                                                        |
| Host-side Python capture client + LSL outlet + analysis pipeline          | — (the beta just changes its transport backend)         |
| Labstreamer integration (TTL markers, timing validation)                  | — (marker ingestion path is identical)                   |
| Cap prep / impedance / QC procedures                                      | — (same cap, same electrodes)                            |
| Noise floor + per-channel calibration data                                | — (same analog front-end silicon)                        |

**Design rule:** the framed packet the alpha's STM32 sends over USB-CDC is
byte-for-byte the same packet the beta's STM32 sends to the ESP32-S3 over SPI.
The ESP32 just re-emits it over WiFi/WebSocket/LSL. Nothing above the
transport layer changes.

---

## Track A — Alpha, now

### Phase 0: Bring-up & characterization (alpha, baseline)

Goals: confirm the unit works, measure actual behavior, document reality vs paper.

- [ ] Power the unit from a USB battery; confirm USB enumerates as CDC on macOS/Linux.
- [ ] Capture a raw stream with the existing firmware; verify 128 × 250 Hz × 24-bit framing.
- [ ] Cap-off noise floor: record 5 min with inputs shorted to bias; compute per-channel µVrms and line-noise spur at 60 Hz.
- [ ] Cap-on signal: 5 min eyes-closed; confirm 8-12 Hz alpha over O1/O2/Pz.
- [ ] Electrode impedance: manual touch-test, log dead-channel pattern.
- [ ] Trace actual STM32 pinout vs `.ioc` — freeze a pin/function map document.
- [ ] Identify whether a Labstreamer TTL can be routed via the ADuM1402 ISO_UART spare lane.
- [ ] Confirm microSD socket works with existing firmware (may or may not be wired in active paths).

### Phase 1: Firmware rewrite v1 (alpha)

Goals: produce the **reference firmware + protocol** that the beta will inherit.

- [ ] Re-bootstrap `.ioc` on current STM32CubeMX; resolve HS/FS USB conflict (lock to FS).
- [ ] Modularize: `hal/`, `drivers/` (ads131m08, lsm6ds3, sdcard), `transport/` (cdc, bridge-stub), `services/` (acquisition, logging, command).
- [ ] Define framed packet: magic, length, seq, µs timestamp, ADC status mask, 128 × int24 samples, IMU, CRC32.
- [ ] Host command protocol v1: `START`, `STOP`, `SET_RATE`, `SET_GAIN <ch> <g>`, `LEAD_OFF_START`, `LEAD_OFF_STOP`, `GET_CAPS`.
- [ ] Capability descriptor (channel map, rates supported, firmware rev) returned on `GET_CAPS`.
- [ ] Forward ADS131M08 per-sample CRC; drop detection + counters.
- [ ] Enable IWDG; add boot banner with reset cause.
- [ ] Enable RTC (LSE is populated); device-side µs timestamp.
- [ ] Clean dead code: `ad7779.c/h`, W5500 blocks, commented LCD code.
- [ ] MPU-backed non-cacheable DMA region; re-enable DCache.
- [ ] Expose DFU-jump command on the control channel.

### Phase 2: Host stack (alpha, parallel)

Goals: the full acquisition + analysis pipeline, transport-agnostic.

- [ ] Python capture client: reads CDC, parses framed packets, writes BIDS-EEG.
- [ ] LSL outlet: republish EEG + IMU + markers with native-µs timestamps.
- [ ] Labstreamer integration: ingest TTL markers as LSL; cross-check with an in-band photodiode channel.
- [ ] Stimulus pipeline: PsychoPy or Presentation scripts with LSL markers; timing-characterize the display.
- [ ] Quality dashboard: per-channel PSD (matches paper's green/red gate), impedance display, drop-counter trend.
- [ ] BIDS-EEG writer + dataset template for MindBigData-style single-subject datasets.
- [ ] **FIFF writer** (Neuromag format) alongside BIDS-EEG — lets MNE-Python read captures via `mne.io.read_raw_fif()`. Enables MNE-CPP replay/forward-model pipelines trivially.
- [ ] **MNE-CPP integration** (see `docs/mne-cpp-plugin.md` when written): Stage 1 is free via LSL outlet; Stage 2 is a native MNE Scan acquisition plugin (`freeeeg128adapter`) modeled on `applications/mne_scan/plugins/lsladapter/`, upstreamable to mne-tools/mne-cpp after P1.0 protocol freeze + P1.4 driver stable.

### Phase 3: Data collection on alpha

Goals: validate the full stack end-to-end; produce real datasets.

- [ ] Replicate a small MindBigData-style block (MNIST or ERP paradigm) to prove parity with the paper.
- [ ] ERP validation: auditory oddball — confirm P300 latency within 20 ms of Labstreamer ground truth.
- [ ] Publish dataset + acquisition protocol before the beta arrives so we have a reference.

---

## Track B — Beta design, in parallel

### Phase B0: Architecture (now)

Decide the bridge before fabrication.

- [ ] **MCU keep vs upgrade** (see §B0.1 below). Default: keep H743ZI.
- [ ] Co-processor: **ESP32-S3** (default) vs ESP32-P4 + C6 (if USB-HS + DP-FPU needed on the radio side).
- [ ] Bridge link: SPI (fast, low-latency) or UART (simpler, fewer pins). Favor SPI: 6 Mbps sustained well within the packet budget, and STM32H7 has spare SPI capacity.
- [ ] Direction: STM32 is SPI master (clocks the link), ESP32-S3 is slave + data-ready interrupt. Symmetric framing so commands flow back.
- [ ] Isolation: ESP32-S3 lives on the **host side** of the existing ADuM barrier. New isolator (ADuM141D or similar) on the STM32↔ESP32 SPI lane. Radio never crosses the analog ground plane.
- [ ] Power: separate RF-quiet LDO for ESP32-S3; antenna oriented away from analog front-end.
- [ ] STEMMA QT / Qwiic connector on the ESP32 side — Adafruit I²C sensors plug directly.
- [ ] Trigger input: dedicate one ADuM1402 channel for isolated TTL from Labstreamer into STM32 (not ESP32).

### B0.1 — STM32 MCU upgrade evaluation

Default: **keep STM32H743ZI**. Every STM32 in-family refresh keeps our 6-SPI /
TIM-DMA-cascade advantage unchanged; clock-bump variants solve a problem we
don't have.

| Option                                | Speed         | Key delta vs H743                                              | Verdict                                                                                      |
| ------------------------------------- | ------------- | -------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| STM32H753ZI                           | 480 MHz       | + crypto accelerator, pin-compat                                | No — crypto lives on ESP32-S3.                                                               |
| STM32H723/H725ZG                      | 550 MHz       | +15% clock, less RAM (565 KB)                                   | No — gain we don't need, RAM regression.                                                      |
| STM32H7A3/H7B3ZI                      | 280 MHz       | 2 MB flash + 1.4 MB RAM, USB-HS PHY on-die                      | Marginal — deeper buffers, but clock regression.                                              |
| STM32H755/H757ZI (M7 + M4)            | 480 + 240     | dual-core, M4 could own bridge                                  | No — doesn't give Adafruit/CircuitPython alignment. ESP32-S3 remains the right tool.         |
| STM32H7R / H7S                        | 600 MHz       | XiP-flash design, newest H7                                     | No — external-flash architecture overcomplicates.                                            |
| **STM32N6**                           | 800 MHz (M55 + Helium + NPU) | Vector DSP + on-die Neural-ART NPU                              | **Maybe** — only qualitatively new upgrade. Unlocks on-device ML (artifact gating, decoding). |
| **STM32MP2 series** (M33 + A35 Linux) | heterogeneous | Cortex-A runs Linux → native PyLSL/BrainFlow/ROS                | **No — see §B0.2.** Wrong tool for a belt-pack 128-ch acquisition rig.                         |

**Decision rule:**
- If beta = "same job, cleaner firmware + radio surface" → H743 + ESP32-S3.
- If beta = "add on-device ML (real-time artifact gating, adaptive filter, decoder)" → **STM32N6** + ESP32-S3.
- If beta = "drop the ESP32 entirely, run Linux on-device" → **STM32MP2**, no ESP32 (but lose Adafruit alignment).

See also: `COMPARISON.md` (open-source EEG landscape), `REFERENCES.md` (academic refs including Black et al 2017 Open Ephys 128-ch).

### B0.2 — STM32MP2 evaluation (done; rejected)

Evaluated ST's heterogeneous Cortex-A + Cortex-M MPU line as a way to run Linux
on-device and eliminate the ESP32-S3 co-processor. Findings (pricing
pre-2026 estimates, re-verify at distributor before citing in design docs):

- **SPI count**: MP25x has **8 SPI** (≥ our 6 — pass). MP23x ~6 (borderline). MP21x ~4 (fail).
- **Timer/DMA cascade**: M33 domain exposes TIM1/TIM8 + HRTIM + newer GPDMA; our CS-pulse pattern ports, but HAL-layer rewrite required.
- **Dev boards**: MP257F-DK ~$150-180, MP257F-EV1 ~$600-750, MP235F-DK ~$100-130 (all pre-2026; re-verify).
- **Silicon qty-1k**: ~$18-30 per MP25 SKU vs ~$12-15 H743ZI.
- **Package**: TFBGA-361 at 0.5 mm pitch → forces **6-8 layer HDI PCB with laser microvias**. Real DFM jump for an analog research board.
- **Power**: H743 + ESP32-S3 is ~1-1.5 Wh for a 4-6 h session; MP257 running Linux is **10-20 Wh** — a ~10× battery-mass regression. Unacceptable even for a belt-pack; pushes the amp back to desk-tethered only.
- **EMI**: adding a PMIC (STPMIC25) + LPDDR4 routing next to a 24-bit Δ-Σ front-end is an SNR regression; puts pressure on the ground plane and shielding.
- **Attack surface**: Linux rootfs + secure boot key management is a maintenance burden a medical-isolated device shouldn't carry for nothing.
- **Wins**: 1.35 TOPS on-die NPU (MP257), MIPI-CSI, GbE/TSN, eliminates a coprocessor. None of those are stated requirements.

**Verdict: reject for the belt-pack acquisition board.** (The 128-ch amp is not head-worn — see `ENCLOSURE.md`. But a 10× battery-weight regression is still unacceptable on a belt pack.) If on-device Linux
becomes desirable later (cloud sync, on-device analysis, camera co-registration),
add it as a **separate isolated companion module** (RPi CM5 or an Octavo
OSD32MP25 SoM) connected over isolated SPI/UART — that preserves the
radio-quiet analog section and keeps the medical isolation boundary clean.

This leaves **STM32N6** as the only STM32 upgrade worth further evaluation (on-device ML via M55 + Helium + NPU). Treat it as a B0.1 decision between "H743 default" and "N6 if we want on-device ML."

### Phase B1: Schematic + PCB

- [ ] Freeze STM32 pinmap from Phase 0 audit; avoid gratuitous changes.
- [ ] Add ESP32-S3-WROOM-1-N16R8 (16 MB flash, 8 MB PSRAM).
- [ ] Add RF shield can; antenna cutout; ground-stitching to analog section.
- [ ] Add STEMMA QT, Qwiic, user buttons, addressable LED (Adafruit-curriculum surface).
- [ ] Add isolated TTL trigger header (BNC or 3.5 mm) for Labstreamer.
- [ ] Optional: magjack + LAN8742A RMII PHY for true Ethernet (only if WiFi latency proves insufficient for some use case).
- [ ] Keep cap-side connector and electrode pinout identical — cap is a big investment.

### Phase B2: Firmware (port + co-processor)

- [ ] STM32 firmware: replace `transport/cdc.c` with `transport/bridge_spi.c`; everything else unchanged.
- [ ] ESP32-S3 firmware v1 (ESP-IDF): consume bridge packets, emit over WiFi WebSocket + LSL.
- [ ] ESP32-S3 firmware v2 (optional): CircuitPython build exposing the same packet stream via Python APIs for teaching.
- [ ] OTA: ESP-side for field updates; STM-side retained via DFU.

### Phase B3: Bring-up & parity

- [ ] Side-by-side capture on alpha (CDC) vs beta (WebSocket) of the same paradigm; confirm byte-identical packets.
- [ ] Re-run ERP validation to confirm beta matches alpha latency characterization.

---

## Future form-factor variants (post-beta, same architecture)

The STM32H743 + ADS131M08 + framed-packet stack isn't specific to a
128-channel cap. The same firmware, same host Python package, same wire
protocol, same LSL outlet all work at other channel counts. Two concrete
directions worth capturing:

### FreeEEG-Ear — concealed cEEGrid form factor

Knierim, Berger & Reali (2021, *Brain-Computer Interfaces*,
[doi:10.1080/2326263X.2021.1972633](https://doi.org/10.1080/2326263X.2021.1972633))
demonstrate that an OpenBCI-class ADS1299 amplifier, connected to
cEEGrid around-the-ear flex-PCB electrodes (Debener et al. 2015,
*Scientific Reports*), captures clinical-grade EEG at ~10-20 channels
per ear with:

- **~1-minute electrode application** (adhesive-backed cEEGrid, no
  hair prep, no saline/gel)
- **Concealed / wearable-all-day** — sits behind the pinna, not visible
  under normal hair

Pairs naturally with the **Fastball paradigm** (Stothart et al. 2017
*Neuropsychologia*; Stothart et al. 2021 *Brain*) — rapid serial visual
presentation at 3 Hz with embedded 0.6 Hz oddball, ~3-minute passive
protocol producing an implicit-recognition response. Fastball
works on populations where instruction-following fails (dementia,
stroke, paediatric), making it the natural clinical-screening
application for a cEEGrid-class device.

**Architecturally**: one or two ADS131M08s (8 ch each), same
STM32H743-class MCU, same full-speed USB-CDC / Pi-Zero-2W companion
pattern, same firmware source tree with `n_eeg_channels` baked into
the capability descriptor. The hardware delta is almost entirely
**cap connector + mechanical form factor** (flex-PCB strip + adhesive
backing vs 130-pin DIN harness). The firmware doesn't care.

Staging relative to current work:

- **FreeEEG128 beta** finishes first — that's where the acquisition-
  architecture correctness + firmware rewrite + host stack get proven.
- **FreeEEG-Ear** then becomes a board-layout-only project — schematic
  changes limited to removing 14 ADS131M08 instances and the 130-lead
  fan-out, and swapping the cap interface for a cEEGrid-compatible
  connector. Most of the expensive design work (isolation, LDOs,
  references, USB, firmware, host) is direct reuse.
- **Fastball pipeline** can be developed in parallel using EEG-ExPy or
  PsychoPy on the existing Pi-Zero-2W host, validated against the
  FreeEEG128 board, then deployed against FreeEEG-Ear when that board
  lands. The cap-side change is invisible to the stimulus engine.

Clinical indication pathway: dementia memory screening → stroke
recovery assessment → paediatric language/memory assessment → teletherapy
monitoring. Each of those is a several-hundred-thousand-patient-a-year
market in the US alone; none is addressable by a 128-channel research rig.

### FreeEEG256 — density upgrade

Same STM32H743 + firmware, 32× ADS131M08 across the six SPI buses
instead of 16. Moves into the VHD-EEG class (256 ch is where g.Pangolin
lives — see `COMPARISON.md`). Bigger board, more expensive BOM, harder
cap manufacturing. Not on the near-term roadmap but the firmware and
host work done for FreeEEG128 port forward unchanged.

### Both variants exist because the protocol is cap-agnostic

The `CAPABILITIES` packet (protocol v1 §0x20) carries `n_eeg_channels`
and a label list on every boot. Host software auto-configures for the
connected device. This is why these two spin-offs cost one board layout
each, not full firmware + host rewrites.

## Work we should NOT do on the alpha

Things that would waste effort because they don't transfer:

- WiFi bring-up on STM32 (no radio; adding one is the whole point of the beta).
- Ethernet via W5500 SPI module (may feel tempting given the commented-out code, but WiFi-on-beta is the planned path).
- CircuitPython on STM32H7 (H7 isn't a CP tier-1 target; ESP32-S3 on beta is the Python surface).
- Building our own LSL bridge on the STM side — trivial work the beta's ESP32 does natively.

---

## Immediate next steps (this week)

1. Power up the alpha, confirm CDC enumeration, log one 60 s capture with shorted inputs for noise floor.
2. Extract actual STM32 pinout → `docs/alpha-pinmap.md` to freeze before firmware rewrite.
3. Decide: rewrite `.ioc` from scratch on current CubeMX, or migrate the existing one? (Recommendation: scratch — too many gaps to paper over.)
4. Draft the framed-packet spec → `docs/packet-format.md`. This is the single most important artifact for carry-over; lock it before writing any transport code.
