# Open-source EEG board landscape

Comparison of other open-source / open-hardware EEG boards and the concrete
lessons we should steal for the FreeEEG128 rewrite and the beta rev.

> ⚠️ **Live-data caveat:** the research agent that produced the table below had
> no network access in the session it was run in, so **URLs, prices, and 2026
> SKUs are training-data estimates, not live-verified**. Treat this file as a
> starting map. Before citing in any design doc, BOM, or purchase order,
> re-verify at the vendor site and on current GitHub repos.

---

## Boards surveyed

| Board | MCU | ADC | Ch | Max SR | Res | Host I/F | Enclosure | Price USD | License | URL | Lesson for FreeEEG128 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **OpenBCI Cyton** | PIC32MX250F128B | ADS1299 | 8 (16 w/ Daisy) | 250 Hz (16ch) / 500 Hz (8ch) | 24-bit | RFduino BLE → USB-serial | Ultracortex 3D-printable headset | ~$1 000 / ~$2 200 w/ Daisy | MIT (HW+FW) | docs.openbci.com/Cyton | **Reference packet format**: 33-byte binary, `0xA0` start / `0xCn` stop; ASCII command set (`b`=start, `s`=stop, `x…X`=per-ch config). Wide ecosystem. |
| **OpenBCI Ganglion** | nRF51822 (M0 + BLE) | MCP3912 | 4 | 200 Hz | 24-bit | native BLE | small PCB | ~$500 | MIT | docs.openbci.com/Ganglion | BLE-direct firmware pattern for a future small variant. |
| **OpenBCI Galea** | NXP i.MX RT1062 + multi-ADS1299 | multi-ADS1299 | 8 EEG + EMG/EOG/GSR/PPG/eye | 500 Hz | 24-bit | USB-C + VR HMD tether | integrated in Varjo/Valve HMD | ~$25 000 | closed HW / open SDK | galea.co | Productized BrainFlow/LSL integration + multimodal fusion. |
| **OpenBCI WiFi Shield** | ESP8266 | (passthrough) | — | 1 kHz on Cyton | — | WiFi TCP/UDP | shield | ~$80 | MIT | docs.openbci.com/WiFiShield | **Accessory-shield model**: decouple radio from main board. |
| **PiEEG** (PiEEG Ltd) | Raspberry Pi host + thin MCU bridge | ADS1299 (×1/×2) | 8 / 16 | 250-500 Hz | 24-bit | SPI HAT → Raspberry Pi | plastic enclosure + cap | ~€350 / €600 | GPL-3.0 | github.com/pieeg-club/PiEEG | **Host-as-MCU**: offload stack to Pi, MCU is a thin SPI↔USB/Ethernet bridge. |
| **IronBCI** (PiEEG Ltd) | STM32F4 | ADS1299 | 8 | 500 Hz | 24-bit | USB-CDC + BLE | DIY PCB | open-source BOM | GPL-3.0 | github.com/pieeg-club/ironbci | Explicit "FreeEEG32 successor in STM32 form"; adds BLE, Python client, and a validation preprint vs BioSemi. |
| **NeuroPawn Knight** | RP2040 / ESP32-S3 | ADS1299 | 8 | 500 Hz | 24-bit | USB-CDC (+ BLE on ESP) | breadboard / DIY | kit ~$250 | MIT / CERN-OHL | neuropawn.com | Low-cost hobbyist entry; good BrainFlow/LSL example code. |
| **HackEEG** (Starcat / Feuer) | Arduino Due (SAM3X8E) | ADS1299 (1-4 daisy) | 8 / 16 / 24 / 32 | **16 kHz @ 8ch** (packed binary) | 24-bit | USB-CDC | bare shield | ~$450 | MIT | github.com/adamfeuer/hackeeg-client-python | **Dual protocol**: JSONLines for debug + MessagePack for speed. |
| **Neurogate OctaFlow** | ESP32-C3 | ADS1299 | 8 | 4 kHz | 24-bit | USB-CDC + WiFi/BLE | small PCB | ~$200 | open | neurogate.io | ESP32 low-BOM template for a future "FreeEEG-mini" / teaching board. |
| **FreeEEG32-beta** (NeuroIDSS, predecessor) | STM32F4 | 4× ADS131M08 | 32 | 250 Hz-2 kHz | 24-bit | USB-CDC | DIY | ~$500 BOM | AGPL-3.0 | github.com/neuroidss/FreeEEG32-beta | **Proved ADS131M08** (vs industry-default ADS1299) hits research-grade noise; demonstrated 4-chip SPI ganging. The 128 just scales the pattern (16 chips, STM32H7). |
| **Upside Down Labs BioAmp EXG Pill** | host MCU (Arduino / Pi Pico) | MCP6N11 front-end → host ADC | 1 | host-limited | host-limited | analog | tiny PCB | $25-$40 | CERN-OHL-P | github.com/upsidedownlabs/BioAmp-EXG-Pill | Instrumentation-amp reference design + superb educational docs — model for teaching materials. |
| **Cognionics/CGX Quick-series** | proprietary | ADS1299 | 8-64 | 500 Hz | 24-bit | BT / USB | dry-electrode cap | $6 k-$25 k | partial schematic release | cgx.com | **Dry-electrode mechanical designs** worth studying for the brain-box. |
| **ExG / ExGate** (community) | STM32 | ADS1299 | 8 | 500 Hz | 24-bit | USB | DIY | — | GPL | forum-scale | Smallest serious ADS1299 reference. |

---

## Key lessons for FreeEEG128

1. **Adopt OpenBCI Cyton binary framing as a supported mode.** `0xA0` start, 24-bit big-endian signed samples, 3-byte aux slot, `0xC0 + rolling-nibble` stop. Every existing client (BrainFlow, OpenViBE, LSL-OpenBCI, BCI2000, Neurosity, Timeflux) speaks it — compatibility is ~free. Keep our native framed-packet format too, but offer a Cyton-compatible alias.

2. **Dual protocol like HackEEG.** Ship a human-readable **JSONLines / ASCII debug mode** AND a **packed binary mode** for the 128 ch × 250 Hz ≈ 96 kB/s fast path. One firmware, two modes.

3. **Standard command vocabulary.** Cyton has a decade of muscle memory behind `b`/`s` start/stop, `?` version, `v` reset, `z<ch>Z` impedance cycle, `x<ch><gain><type><bias><srb2><srb1>X` per-channel config. Inherit it.

4. **Impedance mode is table-stakes.** Inject 6 nA 31.25 Hz on each channel (ADS1299 LOFF_STAT equivalent — ADS131M08 has lead-off detect too) and report Z per electrode before every session. Neither FreeEEG32-beta nor HackEEG shipped this polished; it's the #1 complaint in OpenBCI forums.

5. **LSL + BrainFlow on day one.** Write the BrainFlow `Board` definition ourselves and upstream it — that alone gives us MNE-LSL, LabRecorder, Timeflux, NeuroPype, and OpenViBE. BrainFlow's `BoardIds` enum is the de-facto registry for open EEG.

6. **Accessory-shield architecture (OpenBCI pattern).** Keep the H743 board purely wired/USB; put WiFi (ESP32-S3) and BLE on a separate pluggable daughterboard. Easier FCC, easier medical-grade variants, simpler firmware.
    → this is the beta-rev plan already.

7. **Timestamp every packet at source.** 64-bit monotonic microsecond counter in every frame + a sync-pulse GPIO for LSL `push_chunk` alignment. IronBCI's validation paper flagged this as the biggest gap in FreeEEG32.

8. **Publish a validation study in the repo.** PiEEG/IronBCI's credibility jumped the day Dzhelyova et al. posted bench comparisons to BioSemi ActiveTwo. We should do SSVEP + alpha-peak reproduction with open data in `docs/validation/` before calling anything "beta".

9. **Document like OpenBCI, not like a PhD repo.** `docs.openbci.com` has separate Getting-Started / SDK / Hardware / Tutorials trees. MkDocs + screenshots beats a 40-page PDF.

10. **License split.** AGPL-3.0 on firmware + **CERN-OHL-S-v2** on hardware. AGPL-only on hardware (as NeuroIDSS currently publishes) is legally murky — AGPL is a software licence. CERN-OHL-S-v2 is the modern answer and matches Upside Down Labs and PiEEG practice.

---

## Specific IronBCI → FreeEEG128 deltas

IronBCI is the most directly comparable reference because it's the same lineage
(NeuroIDSS/PiEEG-Club, STM32-based, single ADS-chip successor to FreeEEG32):

| Feature | FreeEEG32-beta | IronBCI | FreeEEG128-alpha | FreeEEG128-beta target |
| --- | --- | --- | --- | --- |
| ADC | 4× ADS131M08 | 1× ADS1299 | 16× ADS131M08 | 16× ADS131M08 |
| MCU | STM32F4 | STM32F4 | STM32H743 | STM32H743 (keep) |
| Host link | USB-CDC | USB-CDC + **BLE** | USB-CDC | USB-CDC + **WiFi via ESP32-S3** |
| Python client | — | **yes (maintained)** | not open-sourced | to build |
| BrainFlow board | no | **yes** | no | **ship** |
| Validation vs clinical amp | no | **yes (Dzhelyova preprint)** | no | **do SSVEP + alpha-peak study** |
| Impedance check | no | partial | no | **ship** |
| Device-side timestamp | coarse | us-precision | host-only | **device-side µs** |

Direction: the beta should **match IronBCI on every row except channel count**.
IronBCI is the correctness bar; FreeEEG128 beats it only in aggregate channel
count and isolation depth.

---

---

## Black et al. 2017 (Open Ephys + EEG) vs FreeEEG128 — primary comparison

Reference: Black, C. et al. "Open Ephys electroencephalography (Open Ephys + EEG): a modular, low-cost, open-source solution to human neural recording." *J. Neural Eng.* **14**, 035002 (2017). doi:10.1088/1741-2552/aa651f.

This is the canonical open-hardware 128-ch human EEG paper. The architecture
is very different from ours — they ride the Open Ephys neural-recording
platform and adapt commercial EEG caps into Intan RHD headstages, so their
"board" is the generic Open Ephys acquisition board plus adapters. We should
match or beat every row below.

| Axis                            | Open Ephys + EEG (Black 2017)                                                                    | FreeEEG128-alpha / beta                                                                                                          |
| ------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **ADC / amplifier**             | Intan **RHD2132** (32-ch) or **RHD2164** (64-ch) bioamplifiers, **16-bit** ADC, on-headstage SPI  | **16× TI ADS131M08**, **24-bit** Δ-Σ, differential amp, 6 SPI buses                                                              |
| **Channels demonstrated**       | 32 / 64 / up to 128 (2× RHD2164) — board supports up to 512 total                                 | 128 fixed                                                                                                                        |
| **Sample rate**                 | configurable up to 30 kHz (Intan max)                                                             | 250 Hz firmware default; ADS131M08 supports up to ~32 kSPS                                                                       |
| **Resolution**                  | **16-bit** (Intan)                                                                                | **24-bit** (our advantage — +8 bits dynamic range)                                                                               |
| **Input-referred noise**        | ~2.4 µV-RMS (Intan RHD spec)                                                                      | ~0.5 µV-RMS over 250 Hz BW at gain 32 (ADS131M08) — **our advantage**                                                            |
| **Acquisition board**           | **Open Ephys acquisition board**: Opal Kelly XEM-6310 FPGA, USB 3.0 host, up to 8 headstages    | Custom FreeEEG128 PCB with STM32H743ZI + on-board 16× ADS131M08 — **no FPGA, no separate headstage**                             |
| **Host interface**              | USB 3.0 from the Open Ephys board                                                                 | USB-CDC (FS, via ADuM3160 isolator); beta adds WiFi/BLE via ESP32-S3                                                              |
| **Cap / electrodes**            | Adapts **commercial EEG caps** (EasyCap, etc.) via a custom breakout from cap connector → Omnetics → Intan headstage | Open-hardware **130-electrode dry Ag/AgCl cap** (custom textile + free_dry_electrodes PCBs); cap is part of the project          |
| **Connector stack**             | Cap → custom breakout PCB → Omnetics nano-strip → RHD headstage → SPI cable to Open Ephys board | 128× 1.5 mm DIN → brain-box → ADC PCB (alpha) / → multipole quick-disconnect → belt-pack (beta)                                   |
| **Reference / ground**          | EEG-cap convention (e.g., CMS/DRL, Cz, earlobe) — configurable via breakout                       | **CP1 = reference, CP2 = ground** (hard-wired at cap; no on-board flexibility)                                                   |
| **Isolation**                   | Partial — Intan chip is biocompatible, but the Open Ephys board is USB-mains-referenced unless isolated upstream | **Full medical-grade isolation** on-board: ADuM3160 USB + ADuM1402 UART + 2× ISO7341C SPI + SN6505B+xfmr isolated DC-DC → **our advantage** |
| **Form factor**                 | Desk/rack — Open Ephys board is a lab instrument, not wearable                                    | **Belt-pack wearable** target (see ENCLOSURE.md)                                                                                 |
| **Stimulus sync**               | Via Open Ephys digital inputs (8 DI + 8 DO + 8 ADC + 8 DAC) — excellent                           | Currently none; beta plan adds TTL via ADuM1402 spare lane + Labstreamer                                                         |
| **Logging**                     | Open Ephys GUI → host disk                                                                        | USB to host; beta adds device-side SD + WiFi                                                                                     |
| **Software**                    | Open Ephys GUI (mature plugin architecture, Bonsai integration)                                   | Paper's custom tool (closed); we are rewriting. Target: BrainFlow + LSL + OpenViBE.                                              |
| **Total cost**                  | ~$2000-3500 (Open Ephys board ~$2000 + 2× RHD2164 headstages + breakout + cap)                    | ~$500-1000 BOM estimate for FreeEEG128-alpha (16× ADS131M08 + H743 + 130 dry electrodes). **Our cost advantage**                |
| **Hardware license**            | **CC BY-NC-SA 3.0 IGO** (non-commercial) on Open Ephys board                                      | AGPL-3.0 upstream; we recommend **CERN-OHL-S-v2** for beta → **our licensing advantage (commercial-use OK)**                     |
| **Validation benchmark**        | Eyes-closed 8-14 Hz alpha, side-by-side vs **BrainVision actiCHamp** — "similar average power and SNR" | Not yet done. **Must reproduce Black 2017's exact protocol** on our unit as acceptance gate.                                    |

### What FreeEEG128 inherits from Black 2017

1. **Validation protocol**: eyes-closed 8-14 Hz alpha vs a clinical-grade actiCHamp is the minimum bar to call anything "beta". Same paradigm, same window, same metric (average power + SNR).
2. **Commercial-cap adapter path**: their breakout PCB from an EasyCap-class connector to an Omnetics-to-Intan headstage is a model for how we could offer a FreeEEG128-amp variant that takes *any* commercial EEG cap. Worth prototyping as a sister product.
3. **Desk-vs-wearable split**: Black's board is desk-tethered; ours is belt-pack. Not a deficit, just a different target. Document the distinction in our marketing.
4. **Plugin-GUI integration**: Open Ephys GUI has the best plugin ecosystem in open-source EEG. **Write an Open-Ephys GUI plugin** for FreeEEG128 (equivalent to their "Rhythm Node") so their users can swap in our amp without changing pipeline.
5. **MNE-CPP / MNE Scan plugin**: the C++ half of the MNE ecosystem has the same plugin architecture as Open Ephys GUI. Supporting both gets us into the two dominant open real-time acquisition stacks. BSD-3 licensed, upstream-accepting. Stage 1 (LSL loopback) lands free via P2; Stage 2 (native `freeeeg128adapter`) is a 1-2 week PR to mne-tools/mne-cpp.
6. **FIFF output**: make `mne.io.read_raw_fif()` work on our captures so MNE-Python users don't translate formats. ~50 lines in the Python host.

### Where FreeEEG128 should beat Black 2017

- **+8 bits resolution** (24-bit vs 16-bit) — real noise-floor improvement for small-signal paradigms (ERN, SSVEP at low contrast, intracranial-analogue imagined speech).
- **Full isolation barrier on-board** — Black 2017 inherits the Open Ephys board's isolation situation, which is not medical-grade by default.
- **No FPGA** — cheaper BOM, simpler firmware story (we stay in STM32 land).
- **Wearable form factor** — Black 2017 is a lab rig; we're targeting mobile.
- **Commercial license** — our CERN-OHL-S plan removes the NC barrier to clinical / commercial deployment.

### Acceptance gate before calling anything "beta"

- [ ] Reproduce Black et al. 2017 Fig. ? (eyes-closed alpha vs actiCHamp) on our unit.
- [ ] Publish raw data + protocol in `docs/validation/` at the same moment we publish the beta schematic.
- [ ] Write an Open Ephys GUI plugin that ingests FreeEEG128's USB stream.

---

---

## VHD-EEG state-of-the-art: g.Pangolin (1024-channel ceiling)

The open-hardware landscape table above sits *below* the commercial
very-high-density (VHD / uHD) frontier. As of 2024, the SOTA for
non-invasive scalp EEG is **g.tec's g.Pangolin**, built around flexible-
PCB active-wet electrode grids feeding up to four g.HIamp 256-channel
amplifiers.

| Axis | g.Pangolin (g.tec, 2023-) | FreeEEG128 (this project) |
| --- | --- | --- |
| Channels | up to **1024** (4× 256-ch g.HIamp) | 128 |
| Electrode technology | Active wet, flex-PCB grids (16 ch per grid) | Passive dry Ag/AgCl (130 electrodes, 10/5 cap) |
| Inter-electrode distance | 8.6 mm | ~20 mm (standard 10/5 at 128 channels) |
| Electrode diameter | 5.9 mm | 12 mm |
| Pre-amplification | On-grid pre-amp, fixed gain 10 | None (passive → ADS131M08 gain 32 in-chip) |
| Sample rate | up to 38.4 kHz per channel | 250 Hz default (chip supports 32 kHz) |
| ADC resolution | 24-bit | 24-bit |
| Application | Clinical / research VHD, neurosurgical mapping, BCI | Open-hardware research, teaching, wearable EEG |
| Form factor | Desk-tethered, amp-on-belt with cables | Belt-pack wearable (see `ENCLOSURE.md`) |
| License | Proprietary (g.tec) | AGPL-3.0 + planned CERN-OHL-S-v2 |
| Cost | Likely >USD 100 000 for full 1024-ch system (unverified) | ~USD 500-1000 BOM |
| Primary paper | Schreiner et al. 2024, *Sci Rep* 14, doi:10.1038/s41598-024-57167-y | this project |
| Demonstrated validation | 95.2% anterior/posterior-to-CS classification accuracy via SSEP phase reversal — matches invasive ECoG | Planned: Black 2017 eyes-closed alpha replication |

**Key takeaway**: g.Pangolin at 256-ch density achieves localization
comparable to invasive intracranial recording. That's the frontier
FreeEEG128 is not chasing; instead, we target the "open, affordable, 128-
channel wearable" niche that has no current peer. A natural upgrade path
exists for a hypothetical `FreeEEG256` on the same STM32H743 + ADS131M08
chassis, but that is explicitly not within the current roadmap.

---

## Lessons from Cardona-Álvarez et al. 2023 (OpenBCI framework)

Reference: Cardona-Álvarez et al., *Sensors* **23**, 3763 (2023), doi:10.3390/s23073763. The most detailed published architecture reference for a production open-hardware BCI framework — worth reading before writing our own P2-P2c components.

### What they built

- OpenBCI Cyton (ADS1299, 8 ch; 16 ch with Daisy) with **custom low-level drivers** replacing the deprecated official Python layer.
- **Raspberry Pi as acquisition server** (validates our Pi Zero 2W companion choice).
- **Three-layer driver architecture**: low-level board I/O → high-level stream abstraction → application UI (PySide6 GUI).
- **Distributed computing via Apache Kafka** for multi-consumer message streaming.
- Stimulus delivery via **Brython-Radiant** (browser-based HTML/CSS/JS).
- Marker synchronization validated against a **Light-Dependent Resistor (LDR)** → the same technique we plan with Labstreamer + in-band photodiode.
- Open-source repos: <https://github.com/UN-GCPDS/openbci-stream>, <https://github.com/UN-GCPDS/BCI-framework>, docs at <https://docs.bciframework.org/>.

### Benchmarking methodology we can copy

Their Table 6 compares three systems on two metrics:

| System | Latency | Jitter | Communication |
| --- | --- | --- | --- |
| OpenBCI (theirs) | 56 % relative (100-sample block @ 1 kHz) | **5.7 ms** | Wireless |
| BCI2000 + g.USBamp | 14-48 % relative | 5.91 ms | Wired |
| OpenViBE + TMSi | 100.4 % relative | 3.07 ms | Optical |

Adopt this exact table for FreeEEG128's validation section: column 1 = system, column 2 = relative latency, column 3 = jitter, column 4 = transport. Directly comparable to our LSL bench p50 / p95 / max measurements (currently 12.8 / 12.9 / 14.8 ms on Pi Zero 2W, all tighter than their wireless OpenBCI numbers).

### Three sample-integrity detection methods

They cross-check stream completeness with:

1. Device-side **timestamp** on each sample
2. **Test-signal mode** (ADS chip-internal known waveform) to detect insertion/deletion
3. **Sample-index counter** (our `seq` field)

Our protocol has (1) via `ts_us` and (3) via `seq`, but **not (2) test-signal mode**. Add a `SELF_TEST` / `SET_MUX` pair to our command protocol that lets host validate stream integrity against the ADS131M08's test patterns. Already on the list as `CmdId.SELF_TEST` / `CmdId.SET_MUX` — this paper validates the need.

### Explicit criticisms of stock OpenBCI we can frame against

They enumerate OpenBCI pain points that our design must not inherit:

- *"Need for more effective communication between computers and peripheral devices"* — addressed in our **host command protocol** (v1 locked in `docs/command-protocol.md`).
- *"[Stock GUI] does not allow for data acquisition under specific parameters"* — addressed by our `SET_RATE` / `SET_GAIN` / `SET_MUX` commands.
- **Deprecated Python drivers** (historical) — replaced by BrainFlow. We target BrainFlow native from day one.
- **Cyton + Daisy interleave artifact**: expanding 8→16 channels alternates samples between two boards, requiring host-side interpolation that introduces phase error. **FreeEEG128's 16× ADS131M08 on a TIM1/TIM8-synchronized DMA cascade eliminates this artifact entirely** — all 128 channels are genuinely simultaneously sampled. This is one of the strongest technical arguments for our architecture over OpenBCI's.

### Paradigm gap we can fill

Their validation covered **motor imagery only** (cue-based left/right arrow paradigm). No P300, SSVEP, N170, MMN, or alpha rhythm. Combined with Black et al. 2017's eyes-closed alpha reference, FreeEEG128's planned validation battery — Black-style alpha *plus* P300 latency *plus* SSVEP spectrum *plus* optional N170 — materially expands the open-hardware EEG validation literature.

### What we will *not* copy from them

- **Apache Kafka** — overkill for single-subject recording with ≤10 consumers. Our LSL + BrainFlow stack covers the message-fan-out use case with far lower operational overhead. Revisit Kafka only if we grow into multi-device hyperscanning.
- **Brython-Radiant** stimulus delivery — we use PsychoPy / Labstreamer, which are the clinical-research standard.

---

### Supporting VHD-EEG literature

- **Schreiner et al. 2024** — introduces g.Pangolin; demonstrates 256-ch
  VHD EEG delineating the central sulcus at intracranial-comparable
  accuracy. (Primary comparison paper.)
- **Shirazi, Onton & Makeig 2025** (*bioRxiv*) — simulates scalp EEG from
  ultra-high-density ECoG to quantify cortex-to-scalp projection patterns.
  Motivates the spatial-Nyquist case for VHD EEG.
- **Liu, Ganzetti, Wenderoth & Mantini 2018** (*Front. Neuroinformatics*)
  — systematic study of how electrode density, head modeling, and source
  localization interact when detecting large-scale brain networks;
  methodological justification for the density race.
- **Fiedler et al. 2022** — 256-channel dry cap for VHD-EEG. Shows the
  dry-electrode path is viable at 256 channels, relevant to a possible
  FreeEEG256 direction.
- **Grover & Venkatesh** (cited in Schreiner 2024) — information-theoretic
  analysis of EEG spatial bandwidth arguing for thousands of sensors.

---

## Open questions to resolve before beta freeze

- Do we commit to **BrainFlow + LSL** as the primary host protocol, with Cyton-compatible binary as a secondary compatibility shim? (Recommend: yes.)
- Do we publish the validation dataset on OpenNeuro + HuggingFace, or only one? (Recommend: both — OpenNeuro for BIDS, HF for ML.)
- Do we license hardware as **CERN-OHL-S-v2** even though upstream NeuroIDSS uses AGPL-3.0? (Requires explicit relicensing discussion; the AGPL on hardware is a known issue.)
- Which ADS131M08 lead-off detection mode do we use for impedance, and at what drive current? (Needs bench measurement on the alpha.)
