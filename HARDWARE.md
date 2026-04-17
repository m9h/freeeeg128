# FreeEEG128-alpha — Hardware & Acquisition Notes

Canonical reference for collecting new data with the 128-channel MindBigData
capture rig described in Vivancos, "MindBigData 2023 MNIST-8B"
([arXiv:2306.00455](https://arxiv.org/abs/2306.00455)).

This file is the living single source of truth. Extend it as we add firmware
builds, PCB revisions, cap modifications, host software, and stimulus/timing
infrastructure.

Owner: Morgan Hough — one alpha unit on hand (fewer than 5 exist worldwide).
Stimulus timing validated with a Neurobs Labstreamer
(<https://neurobs.com/menu_presentation/menu_hardware/labstreamer>).

---

## 1. System overview

```
 dry Ag/AgCl electrode (130×, 4mm snap)
   │  0.6 mm shielded cable, 1.5 mm DIN touch-proof at the box end
   ▼
 custom brain-box (passive fan-out / channel selection)
   │
   ▼
 FreeEEG128-alpha acquisition board
   ├─ 16× TI ADS131M08  (8-ch, 24-bit Δ-Σ, gain 32, Vref 1.25 V, 250 Hz)
   └─ STM32H743ZI  (Cortex-M7 @ 480 MHz, NeuroIDSS open firmware)
   │
   ▼  USB (simulated serial / virtual COM)     ◄── USB power bank
 Host PC
   ├─ custom capture app (raw packets → CSV, live PSD quality dashboard)
   └─ custom stimulus app (65" display + spoken-digit WAV, manual button trigger)
```

## 2. Cap and electrodes

- **Cap**: flexible textile with **130 pre-assigned mounting holes** in the 10/5 system.
- **Electrodes**: **130 dry passive Ag/AgCl**, 12 mm diameter, multi-prong
  (pass through hair), DC resistance ≤ 500 Ω.
  Open design in `cap-free-dry-electrodes/` (`free_dry_electrodes_12_18`, `free_dry_electrodes_6i_6o`).
- **Leads**: 0.6 mm shielded cable, **4 mm snap** on electrode, **1.5 mm DIN touch-proof** at brain-box.
- **Brain-box**: custom passive breakout for channel routing into the ADC PCB.
- **Reference / ground**: **CP1 = reference, CP2 = ground** (hard-wired; their 3-D coords are in `3Dcoords.csv` but no signal is stored for them). If you want CP1/CP2 as data, you have to re-plan the montage.
- **Channel list (128)**: FP1, FPz, FP2, AFp1, AFpz, AFp2, AF7, AF3, AF4, AF8, AFF5h, AFF1h, AFF2h, AFF6h, F9, F7, F5, F3, F1, Fz, F2, F4, F6, F8, F10, FFT9h, FFT7h, FFC5h, FFC3h, FFC1h, FFC2h, FFC4h, FFC6h, FFT8h, FFT10h, FT9, FT7, FC5, FC3, FC1, FCz, FC2, FC4, FC6, FT8, FT10, FTT9h, FTT7h, FCC5h, FCC3h, FCC1h, FCC2h, FCC4h, FCC6h, FTT8h, FTT10h, T7, C5, C3, C1, Cz, C2, C4, C6, T8, TTP7h, CCP5h, CCP3h, CCP1h, CCP2h, CCP4h, CCP6h, TTP8h, TP7, CP5, CP3, (CP1), Cpz, (CP2), CP4, CP6, TP8, TP10, TPP9h, TPP7h, CPP5h, CPP3h, CPP1h, CPP2h, CPP4h, CPP6h, TPP8h, TPP10h, P9, P7, P5, P3, P1, Pz, P2, P4, P6, P8, P10, PPO9h, PPO5h, PPO1h, PPO2h, PPO6h, PPO10h, PO9, PO7, PO3, POz, PO4, PO8, PO10, POO9h, POO1, POO2, POO10h, O1, Oz, O2, OI1h, OI2h, I1, Iz, I2. CP1 (ref) and CP2 (gnd) are included in the 3-D coord file as 128+2 sites.
- **ADC↔channel map** (8 channels per ADC, deliberately scattered to increase singularity):

  | ADC  | ch1   | ch2   | ch3   | ch4   | ch5   | ch6   | ch7    | ch8    |
  | ---- | ----- | ----- | ----- | ----- | ----- | ----- | ------ | ------ |
  | ADC1 | F9    | P9    | C3    | Fz    | Pz    | C4    | F10    | P10    |
  | ADC2 | T7    | FT9   | FFC5h | CP5h  | Oz    | FCC6h | FT10   | T8     |
  | ADC3 | C5    | AF7   | PO9   | FCC1h | CPP2h | F8    | C6     | PO8    |
  | ADC4 | TPP9h | FC5   | CPP3h | F1    | AFp4  | FC6   | CPP4h  | PPO10h |
  | ADC5 | F7    | PPO9h | AFF1h | CPP1h | F2    | FC4   | OI2h   | PPO6h  |
  | ADC6 | TPP7h | FCz   | CCP3h | C1    | F2    | I1    | TTP8h  | PPO9h  |
  | ADC7 | FFT9h | P7    | FP1   | C1    | F2    | I1    | TTP8h  | PPO6h  |
  | ADC8 | FTT9h | P5    | FCC1h | FP2   | FT10h | FCC6h | P8     | PO10   |
  | ADC9 | FCz   | CP5   | FCC1h | PPO2h | FC4   | PO3   | TPP8h  | I2     |
  | ADC10| F5    | FP5   | AFp2  | Cpz   | FC4   | CP6   | PO3    | I2     |
  | ADC11| F3    | CCP3h | TP7   | PPO5h | CCP4h | PO4   | FT8    | TP8    |
  | ADC12| TTP7h | AFp1  | FC1   | O1    | F4    | C2    | P4     | FFT8h  |
  | ADC13| F7    | CCP5h | AF3   | PPO5h | CCP4h | PO4   | FT8    | TP8    |
  | ADC14| FTT7h | FC3   | FFC3h | P3    | FFC2h | CPP6h | CPP4h  | Po2    |
  | ADC15| FCC5h | CP3   | FFC3h | FCz   | FFC4h | CP4   | P2     | Po2    |
  | ADC16| F1    | FCC5h | Iz    | P3    | FFC2h | CPP6h | AFPz   | PoO1   |

  (Table reconstructed from the paper body — double-check against firmware channel
  order in `firmware-stm32cubeide-1.5.1/Src/main.c` before trusting it.)

## 3. Acquisition board

- **ADC**: 16× [TI ADS131M08](https://www.ti.com/lit/ds/sbas950b/sbas950b.pdf)
  (8-ch simultaneous-sampling 24-bit Δ-Σ, also a differential amplifier).
- **Config in firmware**: sample rate **250 Hz**, gain **32**, Vref **1.25 V**.
- **Microcontroller**: [STM32H743ZI](https://www.st.com/en/microcontrollers-microprocessors/stm32h743zi.html)
  (Cortex-M7 @ 480 MHz, 2 MB flash, 1 MB RAM, DP-FPU, L1 cache).
- **Packetization**: 250 packets/second, 128 channels/packet, 24-bit raw values.
- **Power**: USB power bank (not wall adapter; reduces line-noise coupling).
- **Status**: alpha hardware. Fewer than 5 units built worldwide per the paper.

### Raw → microvolt conversion

The firmware emits 24-bit raw integers. No preprocessing is applied on-board.

```
µV = raw * (1_250_000 / ((2^23 − 1) * 32))
```

(Vref 1.25 V × 10⁶ µV/V ÷ full-scale count ÷ gain 32.)

Note that the "half-cell potential" from the electrode–electrolyte interface is
included in the raw signal — subtract or high-pass filter before analysis.

## 4. Host interface

- **Transport**: USB CDC — device appears as a **simulated serial port / virtual COM**.
- **Baud**: firmware streams at whatever the STM32 USB-CDC enumerates at (CDC-ACM; effectively full-speed USB). Packet framing is defined in firmware Src (see `main.c`, `ads131m0x.c`).
- **Driver**: OS-native USB CDC-ACM — no vendor driver required on Linux/macOS; on Windows the standard `usbser.sys` should bind.
- **Client**: a custom capture app (not open-source). It reads raw packets, timestamps on host clock, buffers 250 pkt/s, writes CSV, and runs a per-channel PSD quality dashboard (red=flat/floating, green=OK).
- **OpenVIBE driver**: the 128-ch repo ships an OpenViBE acquisition-server driver under `firmware-freeeeg128-alpha/OpenVIBE/freeeeg32/` (derived from the 32-ch driver — confirm channel count before use).

### Things that are NOT supplied

- No LSL outlet in firmware or capture app.
- No hardware trigger input on the EEG board — stimulus sync relies on host timestamps only.
- No impedance-check mode documented (quality is inferred from PSD).
- No vendor SDK; no Windows GUI; no cross-platform install path.

## 5. Stimulus & timing

The paper's setup:

- 65″ screen in a fixed environment, single seated subject.
- Custom stimulus app shows the MNIST digit pixel image + plays the spoken-digit WAV simultaneously (24 kHz, 16-bit PCM, per-digit duration in paper §2.2).
- **Block structure**: 10 captures per block (5 digit + 5 blank, 2 s each = 20 s of focused attention).
- **Session**: minutes up to ~1 hour, broken into blocks; subject starts each block manually via a button press; subject reviews flat-sensor report after each block and decides save/discard.
- **Synchronization**: host clock only. No photodiode, no hardware trigger line.

### Our improvement path — Labstreamer

Our setup will validate stimulus timing with a **Neurobs Labstreamer**:

- TTL/photodiode capture of actual screen onset and audio envelope.
- Network time sync to the host running the stimulus + capture apps.
- LSL outlet so markers land on the same clock as the EEG.

Open questions for us to resolve before new collection:

1. The FreeEEG128 firmware does not expose a trigger line. Options to close the gap:
   - (a) Route TTL through an LSL marker stream on the host, cross-correlate with an added photodiode channel recorded as one of the 128 (sacrifice one unused-but-noisy channel).
   - (b) Add a GPIO/UART trigger input to the firmware and splice a fresh USB-serial message format (firmware change).
   - (c) Use the Labstreamer as the master clock and post-hoc align using its audio envelope + photodiode streams.
2. Capture client rewrite: the original app is not public. We will want a Python capture that pyserial-reads the CDC stream, parses packets, and republishes as an LSL outlet — lets the Labstreamer's LSL streams join the same recording.
3. Channel-quality gate: reproduce the PSD-based red/green per-channel dashboard so we only collect when ≥96 % of channels are green (paper's accept threshold).

## 6. Repository layout (this directory)

```
freeeeg128/
├── HARDWARE.md                         ← this file
├── README.md                           ← project index
├── firmware-freeeeg128-alpha/          ← full repo: KiCAD + firmware + OpenViBE driver + makefile tarball
│   ├── KiCAD/                          ← schematics (per-ADC + top), PCB, libs, 3-D renders
│   ├── STM32CubeIDE/                   ← IDE project snapshot
│   ├── OpenVIBE/freeeeg32/             ← acquisition-server driver (derived from 32-ch)
│   ├── datasheets/                     ← ADS131M08, REF2025
│   └── STM32H743ZI_ads131_80MHz_makefile.tar.gz   ← standalone makefile firmware build
├── firmware-stm32cubeide-1.5.1/        ← dedicated firmware repo (Src/Inc, .ioc, build configs)
└── cap-free-dry-electrodes/            ← KiCAD for the 12×18 and 6i/6o dry electrode PCBs
```

Future additions (extend this tree as we build the pipeline):

```
├── host/                 ← our Python capture + LSL bridge
├── docs/                 ← setup/QC procedure, reviewer-facing protocols
├── labstreamer/          ← Presentation/PsychoPy scripts + Labstreamer configs
├── analysis/             ← decoding/validation pipelines
└── hardware-revisions/   ← our deltas to the alpha PCB (if we fab new)
```

## 7. Setup & QC procedure (to reproduce)

1. Power the acquisition board from a **USB power bank** — not mains.
2. Seat the dry-electrode cap; manually press each electrode to scalp to verify contact.
3. Connect USB to host; confirm serial port enumerates.
4. Launch capture app + PSD quality dashboard.
5. Accept the session only if **≥96–97 %** of channels show green (≤4–5 flat channels).
6. Record in blocks of 10 captures (5 stim + 5 blank, 2 s each). After each block, review flat-sensor report; save or discard.
7. Watch ambient temperature — sweating kills dry-electrode contact.
8. Session length: from minutes to ~1 hour depending on fatigue and signal stability.

## 8. Recommended preprocessing

From the paper's own guidance:

- Start from raw (as shipped), apply the µV conversion above.
- 50 Hz notch if collected in EU mains; **60 Hz notch for US**.
- FIR high-pass at 0.1 Hz; band-pass 0.1–40 Hz (or to 50 Hz).
- Baseline correction — but note 1/f caveats (cited Gyurkovics 2021).
- EMG/ECG artifact removal (cited Suresh 2008) — critical with dry electrodes.

## 9. Known gaps / risks for a fresh collection

- **Alpha hardware reliability**: the author abandoned an earlier 64-ch version because signal reliability was insufficient for large datasets. Validate SNR and channel dropout behavior on our unit before any long collection.
- **No timing guarantees without Labstreamer**: the original dataset is aligned on host wall-clock. Any claim about ERP latencies (P300, N170, etc.) needs the Labstreamer-validated pipeline.
- **Capture software is not open-sourced**: budget time to rebuild the host side from scratch.
- **Firmware is alpha-grade**: review `main.c` / `ads131m0x.c` for known issues (watchdogs, USB stall recovery, drop counters) before depending on long continuous captures.
- **Single-subject dataset precedent**: if we want generalizable data, we need to confirm cap fit and electrode contact across head sizes (original cap had pre-cut holes for one morphology).

## 10. References

- Vivancos, D. "MindBigData 2023 MNIST-8B." arXiv:2306.00455 (2023).
- Vivancos, D. & Cuesta, F. "MindBigData 2022: A Large Dataset of Brain Signals." arXiv:2212.14746 (2022).
- NeuroIDSS FreeEEG128-alpha (AGPL-3.0): <https://github.com/neuroidss/FreeEEG128-alpha>
- Hackaday project log: <https://hackaday.io/project/181521-freeeeg128-alpha>
- TI ADS131M08 datasheet: <https://www.ti.com/lit/ds/sbas950b/sbas950b.pdf>
- ST STM32H743ZI: <https://www.st.com/en/microcontrollers-microprocessors/stm32h743zi.html>
- Neurobs Labstreamer: <https://neurobs.com/menu_presentation/menu_hardware/labstreamer>
