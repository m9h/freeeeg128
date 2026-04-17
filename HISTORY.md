# A Short History of High-Density EEG

Context for the FreeEEG128 project — the intellectual and engineering
lineage it sits inside. Opens with the theoretical foundations (Nunez) and
the engineering pioneers (Gevins, Tucker/EGI), continues through the
commercial high-density era, and lands at the present open-hardware
generation of which FreeEEG128 is part.

Project owner Morgan Hough was the first software engineering manager at
**Electrical Geodesics, Inc. (EGI)** in the 1990s, where the team built the
**second 256-channel EEG system** in the world. The first was built at
**Neuroscan** by M.E. Pflieger and S.F. Sands, documented in Pflieger &
Sands 1996 [A6] below. The FreeEEG128 design consciously inherits the
EGI / Geodesic Sensor Net approach to high-density acquisition.

---

## 1. Theoretical foundations — Paul Nunez

The modern high-density EEG era is built on Paul Nunez's biophysical
treatment of scalp potentials. His book remains the canonical reference:

> **Nunez, P.L.** *Electric Fields of the Brain: The Neurophysics of EEG*. Oxford University Press (1981). 2nd ed. with **R. Srinivasan**, 2006.

The 2nd edition co-author **Ramesh Srinivasan** bridges the theoretical
(Nunez) and engineering (EGI) sides of the lineage:

- Currently **Professor of Cognitive Sciences and Biomedical Engineering** at UC Irvine, directing the Human Neuroscience Laboratory (<https://hnl.ss.uci.edu/>).
- Was an early part of **Electrical Geodesics, Inc. (EGI)** — so the Nunez-Srinivasan biophysical framework was wired directly into EGI's product line and montaging software during the formative years when Morgan was there as software engineering manager. That is not a coincidence — it is why EGI's systems shipped with Laplacian and averaged-reference options as first-class features.
- Co-authored extensively with Nunez; continues to publish on EEG source localization, coherence, and large-scale neural dynamics.

Key arguments that still shape hardware design today:

- Scalp potential is spatially low-pass-filtered relative to cortical sources — the skull acts as a ~2-3 cm smoothing kernel. This is the **justification for >100 electrodes** (Nyquist-like spatial sampling argument).
- **Reference electrode choice is not neutral.** Any common reference adds a (usually unknown) time-varying term; the surface Laplacian or average reference are preferred for source-localization work.
- Volume conduction means no scalp sensor sees a single source — every decoder has to contend with this.

The specific paper the user flagged with DOI `10.1007/BF01187712` is:

> **Nunez, P.L. & Westdorp, A.F.** "The surface Laplacian, high resolution EEG and controversies." *Brain Topography* **6**, 221-226 (1994). doi:10.1007/BF01187712.

Reading this paper is effectively the entry fee to working on high-density
EEG hardware. Surface Laplacian and related "deblurring" transforms motivate
the channel-count race of the 1990s — without >64 electrodes the math
doesn't pay off.

---

## 2. Engineering pioneer — Alan Gevins

In parallel with Nunez's theoretical work, Alan Gevins built the first
serious engineering practice of high-resolution EEG.

- Founded **EEG Systems Laboratory** (1980, San Francisco; later San Francisco Brain Research Institute / SFBRI), then **SAM Technology** (1986).
- BS MIT 1967; PhD cognitive science 1971. Laboratory director at Langley Porter Neuropsychiatric Institute EEG Lab from 1974.
- **100+ peer-reviewed publications** (5 in *Science*), **19 US patents**, continuous NIH / NSF / AFRL / NRL / DARPA / NASA funding from 1972.
- Reference page: <https://www.eeg.com/alan_gevins.php>

Gevins' engineering-side contributions that matter to FreeEEG128:

- Early systems pushed toward **64 and 128 channels in the late 1980s / early 1990s**, when the commercial norm was 19-32.
- Developed **"deblurring"** methods — combining MRI-derived skull/scalp geometry with scalp EEG to estimate cortical surface potential. This predates modern source-localization and remains an active methodology.
- **MANSCAN** (Mental Attentiveness Neural Signal Coherence ANalysis) and related neurocognitive-pattern-recognition work set the protocol template for sustained-attention and mental-workload studies that the field still uses.
- Demonstrated that **continuous real-time analysis**, not just post-hoc, was feasible with 90s-era hardware — motivating lower-latency acquisition designs.

---

## 3. The engineering breakthrough — Don Tucker & Electrical Geodesics, Inc. (EGI)

The direct ancestor of the FreeEEG128 design philosophy.

- Founded by **Don Tucker** at the University of Oregon (~1992); commercialized the **Geodesic Sensor Net** — a quick-application (~5 min) saline-sponge electrode array wrapped around the head on a tension-distributed elastic polymer scaffold, arranged in a geodesic polyhedron layout for uniform spatial sampling.
- **Second 256-channel EEG system** in the world (after Neuroscan). FreeEEG128's project owner was first software engineering manager at EGI during this era.
- **Ramesh Srinivasan** (Nunez's co-author on *Electric Fields of the Brain* 2nd ed.; now Prof. Cognitive Sciences & Biomedical Engineering at UCI) was an early part of EGI. This is the conduit by which Nunez-style biophysical thinking — surface Laplacian, average reference, volume-conduction–aware montaging — was built directly into EGI's montaging software and product philosophy from the start.
- Key Tucker paper:

  > **Tucker, D.M.** "Spatial sampling of head electrical fields: the geodesic sensor net." *Electroencephalography and Clinical Neurophysiology* **87**, 154-163 (1993).

- Acquired by Philips (2017). The modern NA300 / GTEN lineage comes from this work.
- Design patterns that directly influence FreeEEG128:
  - **>100-channel density is only useful with a practical application workflow** — EGI solved this with saline sponges + elastic scaffold, letting non-specialists apply in ~5 min vs 60+ min for paste-based systems.
  - **Desk/belt-tethered amp + bundled cable to cap** — the form factor we already concluded is correct for 128 ch (see `ENCLOSURE.md`).
  - **Average-reference and vertex-reference montaging in software**, with the physical "reference" electrode treated as just another channel — a design choice that lets users pick references post-hoc.
  - **Per-channel impedance check** shown to the operator before acquisition. This is exactly the gap we've noted in the FreeEEG128 rewrite (see `COMPARISON.md` lessons §4).

---

## 4. The commercial high-density era (1990s - 2010s)

| Vendor | System | Channels | Era | Notes |
|---|---|---|---|---|
| **Neuroscan** | SynAmps / Quik-Cap | up to 256 | early-mid 1990s | **First 256-channel EEG system.** Built by **M.E. Pflieger and S.F. Sands** (principals at Neuroscan); documented in Pflieger & Sands 1996 [A6]. |
| **EGI** | Net Amps / Geodesic Sensor Net | 64 / 128 / 256 | 1992- | Tucker's geodesic scaffold + saline sponges. **Second 256-channel system in the world** — FreeEEG128 project owner Morgan Hough was first software engineering manager during this build. |
| **BioSemi** | ActiveTwo | up to 256 | late 1990s- | **First HD-EEG system with active electrodes** — on-electrode unity-gain buffer eliminates cable capacitance + movement-artifact coupling. The reference choice that defined a generation: BioSemi-vs-BrainVision is still the main "active vs passive" benchmark comparison in most validation studies. |
| BrainProducts | actiCHamp / actiCAP | up to 256 | 2000s- | BrainVision Recorder ecosystem; benchmark for open systems. |
| ANT Neuro | eego / Waveguard | up to 256 | 2000s- | Belt-pack amp + dry-alt caps. |
| Compumedics Neuroscan | SynAmps2 / SynAmps RT | up to 512 | 2000s- | Research / clinical mainstay. |
| g.tec | g.USBamp / g.Nautilus | up to 256 | 2000s- | Modular headbox design. |
| **g.tec** | **g.Pangolin / g.HIamp** | **up to 1024** | **2023-** | **VHD-EEG state-of-the-art.** Flex-PCB active-wet electrode grids, 8.6 mm spacing. 256-ch density achieves 95.2% CS localization vs invasive ECoG (Schreiner et al. 2024). |

Common themes of this era that our project inherits or explicitly moves past:

- **Proprietary everything** — cap, connector, amp, software. Locked ecosystem.
- **Desk-tethered** amps dominate; belt-pack (ANT, BrainProducts LiveAmp) emerges later.
- **Active electrodes at HD scale** — **BioSemi was first**, with the ActiveTwo in the late 1990s. On-electrode unity-gain buffering eliminated cable-capacitance and movement-artifact coupling, and set the standard every later system is compared against. We keep this on the FreeEEG128 v2 roadmap (alpha/beta are passive Ag/AgCl).
- **Per-channel impedance + reference flexibility** become standard — table stakes for the beta.

---

## 4b. The very-high-density frontier — g.Pangolin and 1024-channel EEG (2020s)

A second revolution has been quietly underway since roughly 2020: the move
from "HD-EEG" (64-128 channels) to **ultra- or very-high-density EEG**
(VHD-EEG / uHD-EEG, 256-1024+ channels). The theoretical driver is a
refinement of Nunez's spatial-Nyquist argument — Grover and Venkatesh
(cited in Schreiner et al. 2024) propose on information-theoretic grounds
that the scalp's spatial bandwidth demands not hundreds but *thousands*
of electrode positions to capture all of the information it carries.

The **state-of-the-art commercial VHD system is g.tec's g.Pangolin** — a
1024-channel-capable uHD-EEG platform that Schreiner et al. (2024,
*Scientific Reports*) use to demonstrate non-invasive central-sulcus
mapping at intracranial-comparable accuracy. Key specifications:

- **Up to 1024 channels** via 4× g.HIamp 256-channel amplifiers
- **8.6 mm inter-electrode distance**, **5.9 mm electrode diameter**
- **Flexible printed-circuit electrode grids** (16 channels per grid) with
  gold-plated electrode points
- **Active pre-amplifier** per grid (fixed gain 10) before the g.HIamp
- **Wet electrodes** with conductive paste (e.g., Elefix) applied under an
  adhesive layer designed to prevent bridging and crosstalk
- **24-bit ADC resolution, up to 38.4 kHz sample rate per channel**
- Authors of Schreiner et al. 2024 include **Christoph Guger** (founder of
  g.tec) among g.tec-affiliated researchers

The Schreiner et al. study demonstrates that the g.Pangolin at 256-channel
density can **classify channels as anterior or posterior to the central
sulcus with 95.2% accuracy using SSEP phase-reversal analysis** — a level
of functional precision previously only achievable with surgically
implanted ECoG.

Closely related theoretical and methodological work includes Shirazi,
Onton & Makeig (2025, *bioRxiv*), who simulate scalp EEG from
ultra-high-density ECoG to quantify cortex-to-scalp projection; and Liu
et al. (2018, *Frontiers in Neuroinformatics*), who establish the
systematic benefits of density, head modeling, and source localization
for reconstructing large-scale brain networks. Fiedler et al.'s
256-channel dry cap (2022, *Human Brain Mapping*) covers the
dry-electrode side of the VHD spectrum.

**Where FreeEEG128 sits in this landscape.** We are deliberately not
claiming VHD-EEG status — the open-hardware frontier at 256+ channels
remains commercial-only as of April 2026. FreeEEG128 occupies the
"affordable mid-density open-hardware" niche: higher channel count than
OpenBCI (8-16) and Open Ephys + EEG / Black 2017 (64-128), lower than
g.Pangolin (1024), at roughly one to two orders of magnitude lower cost
than commercial HD systems. A natural upgrade path (`FreeEEG256`) on the
same STM32H743 + ADS131M08 chassis is plausible — 32 ADCs across six SPI
buses plus a second-stage cable design — and would put open hardware
meaningfully closer to the VHD threshold.

## 5. The open-hardware generation (2010s-)

FreeEEG128 sits in this lineage:

| Project | Year | Key move |
|---|---|---|
| **OpenBCI** Cyton | 2014 | First mass-open 8-ch ADS1299 amp. Gave the community a packet format the whole ecosystem adopted. |
| **Open Ephys** acquisition board (Siegle et al.) | 2017 | Plug-in-based GUI + generic Intan-headstage board. 512-ch capacity. |
| **Open Ephys + EEG** (Black et al.) | 2017 | Adapts commercial EEG caps onto Open Ephys. **Primary comparison benchmark for FreeEEG128** (see `COMPARISON.md`). |
| **HackEEG** (Feuer) | ~2018 | 8-32 ch ADS1299 + Arduino Due; dual JSON/MessagePack protocol. |
| **BIOADC** (Gargiulo) | 2019 | First fully open-access 32-ch EEG with full schematic + firmware + electrode release. |
| **PiEEG / IronBCI** | 2020s | Pi-HAT and STM32F4 + ADS1299; explicit FreeEEG32 successor. Validation preprint vs BioSemi. |
| **FreeEEG32-beta** (NeuroIDSS / Vivancos) | 2021 | Proved ADS131M08 (vs industry-default ADS1299) hits research-grade noise. |
| **FreeEEG128-alpha** (NeuroIDSS) | 2023 | 16× ADS131M08 scale-up; STM32H743; ~5 units worldwide. |
| **Neurogate OctaFlow** | 2024 | ESP32-C3 + ADS1299, 8-ch, LSL/WebSocket native. Adafruit-ecosystem-compatible teaching board. |
| **FreeEEG128 beta** (this project) | 2026- | STM32H743 + ESP32-S3 co-processor; cap-mounted brain-box + belt-pack amp; CERN-OHL-S licensing; Open Ephys GUI + BrainFlow + LSL native. |

---

## 6. What FreeEEG128 inherits from each lineage

- **From Nunez**: electrode density justification, reference-scheme agnosticism, surface-Laplacian readiness.
- **From Gevins**: real-time analysis mindset, mental-workload / cognitive-state paradigm library for validation studies.
- **From Tucker / EGI**: practical >100-channel application workflow, desk/belt-tethered form factor, per-channel impedance as a first-class operator-facing feature, software-defined referencing.
- **From BioSemi**: active electrodes at HD scale — BioSemi was the first to productize this combination in the late 1990s, and it remains the gold standard for movement-tolerant recording. Kept on the FreeEEG128 roadmap as a v2 option (our current cap is passive Ag/AgCl).
- **From Open Ephys + EEG (Black 2017)**: plugin-GUI integration path, eyes-closed alpha vs actiCHamp as the validation gate.
- **From OpenBCI**: a shared binary packet format + BrainFlow board identity so the whole open-source toolchain works day-one.
- **From IronBCI**: device-side µs timestamps, published validation vs a clinical amp as the credibility gate.

---

## 7. Open citations to resolve / add

- [ ] Tucker 1993 (Geodesic Sensor Net original paper) — confirm pages / DOI for `REFERENCES.md`.
- [ ] Canonical Gevins "deblurring" paper (likely Gevins et al. 1994 *IEEE EMBS Mag*, or a *Science* paper) — the user may want to name the specific reference.
- [ ] EGI-era Nunez & Srinivasan 2006 2nd ed. citation.
- [ ] Any Morgan-Hough-authored EGI-era publications the user wants surfaced.
