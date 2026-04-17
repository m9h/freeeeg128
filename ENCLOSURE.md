# Enclosure, Battery, Cable & Connector Notes

Design notes for FreeEEG128 physical form factor. **Key finding: this is
not a head-worn device.** The 130-lead cap harness plus amp PCB plus
battery exceeds a reasonable head-mount mass and volume budget. The
realistic form factor is:

```
CAP (head-worn)
 ├── 130 dry Ag/AgCl electrodes
 ├── 130× 1.5 mm DIN leads (keep — subject-contact safety)
 └── BRAIN-BOX (cap-mounted passive fan-out)
      └── 1-2 multipole quick-disconnect (LEMO / Omnetics / HD D-sub)
           │
           ▼ shielded bundle (30-60 cm)
           │
    AMP BOX (belt-pack / shoulder-pack / desk)
     ├── FreeEEG128 PCB (STM32H743 + 16× ADS131M08)
     ├── battery
     └── USB out to host (or WiFi via ESP32-S3 on beta)
```

This matches how BrainProducts (actiCHamp), ANT Neuro (eego), BioSemi
(ActiveTwo), and high-channel-count research rigs are physically organized.

> ⚠️ Live-data caveat: the research agent compiling this had no WebSearch
> access. Part numbers, prices, and vendor links below are training-data
> estimates (Jan 2026 cutoff) — re-quote on Digi-Key / Mouser before any
> BOM commit.

---

## 1. Existing on-board power & isolation topology

From the KiCAD BOM, the analog chain is already galvanically isolated and
very well regulated — **the battery/USB upstream is a non-critical rail**:

- **Analog LDOs**: 3× `LP5907QMFX-3.3Q1` (TI, 6.5 µV-RMS 10 Hz-100 kHz, ~82 dB PSRR @ 1 kHz). BOM shows `ADP7118AUJZ-3.3` (ADI, 1.6 µV-RMS, ~88 dB PSRR) as an alternative. Both genuinely world-class for 24-bit Δ-Σ.
- **Vref**: `REF2025AIDDC` → ADS131M08 Vref 1.25 V, gain 32.
- **Isolation barrier**: ADuM1402 (SPI), ADuM3160 (USB), 2× ISO7341C (SPI/misc), SN6505B + 750315371 push-pull transformer → isolated analog supply.

**Consequence**: whatever powers the digital/host side just has to feed the
SN6505 input without monstrous ripple. Subsequent stages reject it. This is
why the paper's "USB power bank" works — the ADuM3160 breaks the USB
ground loop and the SN6505 + LP5907/ADP7118 stack rejects the rest at
audio frequencies.

---

## 2. Battery chemistry options

Target session: 4-6 h at ~300-500 mA total board draw.

| Option | V | Practical capacity | Weight | Notes |
|---|---|---|---|---|
| **USB power bank** (what paper uses) | 5 V | 5-10 kmAh trivial | 150-300 g | Zero design work, hot-swappable. Watch for 50-100 mA idle-cutout silently disconnecting — budget a dummy load or LiPo buffer cap. |
| **1S LiPo 3.7 V + boost to 5 V** | 3.0-4.2 V | 2.5-3.5 Ah pouch (Adafruit 2011, SparkFun 13856 class) | 40-50 g | Boost switcher injects ripple — use TPS61230A / TPS61099 with a trailing LP5907. |
| **2S Li-ion 18650** (Samsung 35E, Panasonic NCR18650GA, LG MJ1) | 6.0-8.4 V | 3.4-3.5 Ah/cell | ~90 g (2 cells) | **Best measured noise**: enough headroom to use LT3045 (0.8 µV-RMS gold-standard LDO) as a linear regulator down to 5 V. |
| **1S 21700** (Samsung 40T, Molicel P42A) | 3.0-4.2 V | 4-4.5 Ah | 65-70 g | Same boost story as LiPo, slightly larger cell with better energy density. |
| **LiFePO4 1S / 2S** | 3.2 / 6.4 V flat | 1.5-3.2 Ah | variable | Thermally safest. Flat discharge curve *helps* LDO dropout budgeting. No measured evidence it's noisier after LDO. |

**What comparable rigs use** (memory, verify):

- **OpenBCI Cyton**: 4× AA (6 V) or 1S LiPo + LP5907-class LDO.
- **OpenBCI Ganglion / WiFi Shield**: 500-1200 mAh LiPo.
- **Intan RHD2000 USB eval**: USB-bus powered with same ADuM + isolated-DC/DC topology as our board.
- **Cognionics Quick-20 / Quick-30**: internal LiPo, ~8 h advertised.
- **g.tec g.Nautilus / g.USBamp**: proprietary packs; g.USBamp uses LT-series ultra-low-noise LDOs.
- **ANT Neuro eego sports**: LiPo in the amp pack.
- **Emotiv EPOC X**: ~640 mAh LiPo, ~9 h.

**Recommendation**:

- **Alpha (now)**: keep USB power bank. It's free and the isolation barrier already handles the noise.
- **Beta**: make the input accept 4.5-5.25 V USB range; add a `PMEG6020ETR` ideal-diode or `LTC4413` auto-OR between USB-C input and an optional on-board 1S LiPo with a `MAX17227` boost. Don't touch the analog rails — they're already right.

---

## 3. Battery noise floor, honestly

- Switching-regulator ripple at 100 kHz-2 MHz does NOT show up in EEG band (0.1-50 Hz) when the analog LDO has ≥60 dB PSRR at switcher frequency. LP5907 and ADP7118 both clear this.
- TI's SBAA201/SBAA202 app notes: ADS131xx at gain 32 → ~30 nV/√Hz input-referred → ~0.5 µV-RMS over 250 Hz BW. Any of the above chemistries + LDO stack hits this.
- **Honest unknown**: no published peer-reviewed comparison of battery chemistry noise floors *at the electrode* for a 24-bit EEG system. If we need this claim in a paper, measure it on our unit.

---

## 4. Form factor: why not head-worn

Real 128-ch rigs ship the amp **off the head**. The options are:

| Philosophy | Examples | Channels feasible | Notes |
|---|---|---|---|
| **Enclosure = the cap** (molded plastic / fabric) | Cognionics Quick-20/30, Emotiv EPOC X, g.tec g.Nautilus puck | up to ~30-40 | Cap fabric IS the strain relief. Only works at lower ch counts. |
| **Amp-on-belt, shielded bundle to cap** | ANT Neuro eego, BrainProducts actiCHamp, BioSemi ActiveTwo | **64-256+** | **Our target pattern.** Moves weight off head; lets us use a real enclosure. |
| **Bare PCB + heat-shrink** | Intan RHD headstage, PiEEG | — | Research-only, not wearable long-term. |

At 128 channels, option 2 is the only viable path unless we redesign the
cap-to-box connector (see §6).

---

## 5. Enclosure for the amp box

| Option | Verdict for FreeEEG128 |
|---|---|
| **Off-the-shelf extruded aluminum** (Hammond 1455, Takachi MXA/MX, Bud) | **Recommended**. ~$15-25 USD. Drill yourself for connectors. 40 dB RF shielding for free. Downside: machining the connector face is the real cost. |
| **3D-printed PETG or PC** | Fine for prototyping. PETG is tougher than PLA, sweat-resistant. Nylon SLS for lanyard flex. No shielding, but we don't need it (board is isolated). |
| **CNC aluminum custom** | Correct long-term answer. $200-600 one-off from SendCutSend / Protolabs. Shielding nice-to-have, not must-have. |
| **Resin (SLA)** | Avoid — brittle, UV-degrades, not sweat-safe. |

**Shielding necessity**: low. The ADuM3160 breaks USB ground, SN6505 +
LP5907/ADP7118 stack gives 80-90 dB PSRR. 50/60 Hz line noise, if you see
any, is coming in through **electrode leads**, not the enclosure. Spend
shielding budget on the 0.6 mm electrode-cable drain termination, not
on the box.

**Wearability**:

- **Belt pack / fanny pack** — 300-400 g is fine on a belt. Easiest path.
- **Shoulder-strap amp bag** (ANT-style) — best balance. $20 off-the-shelf from any tactical-gear vendor.
- **Neck lanyard** — only if <150 g, unrealistic with 130 connectors.

---

## 6. Connectors — the 1.5 mm DIN problem

The 128× individual 1.5 mm DIN touch-proof field dominates the current
alpha's form factor. Each plug is ~8 × 25 mm; 128 of them is a brick.
**Keep the 1.5 mm DIN at the electrode end** (subject-contact safety is
non-negotiable), but **break the harness at the cap-mounted brain-box**
with a single multipole quick-disconnect to the amp.

| Connector | Pitch / ch | Disconnect | Robustness | Shielding | Price | Verdict |
|---|---|---|---|---|---|---|
| Current 130× individual 1.5 mm DIN | individual | **very slow** | good | per-lead | $130+ | keep at electrode end only |
| **D-Sub HD78 / HD104** | 1.27 mm, 78-104 pin | fast | very good | **full metal shell** | $20-30 pair | **Budget quick-win.** 2× HD78 covers 130 leads. Known-good shield reference. Any tech can mate them. |
| **Omnetics A79025 80-pin shielded** | 0.635 mm | fast | **excellent** (MIL/medical) | shielded shell | $100-180 pair | MIL-grade, small, proven in Intan headstages. |
| **LEMO EGG.4B multipole** (40-60 pole) | push-pull | instant | **best in class**, medical-grade | excellent | $200-400 pair | Clinical-grade, beautiful, expensive. Worth it for a beta that sits next to clinical amps. |
| Samtec AcceleRate (ERM8/ERF8) | 0.8 mm | ~1 s | good, not harsh | partial | $30-60 pair | OK for dev, not rugged. |
| 0.5 mm FFC (ZIF) | ribbon | instant | poor under repeat | needs separate shield | $2-5 | Avoid — alpha reliability risk. |

**Beta-rev recommendation**: **2× HD D-Sub HD78** at the brain-box break
for the first rev (cheap, rugged, cleanable, familiar). Upgrade to
**LEMO EGG.4B** on a second rev if the project moves toward clinical
validation.

---

## 7. Cable-management discipline (where alpha rigs die)

1. **Strain relief at PCB entry** — every 1.5 mm DIN plug lands in a bulkhead captive to the enclosure, NOT the PCB. Heyco / Essentra strain-relief bushings (~$0.50 each × 130 = $65). Or 3D-print the bulkhead.
2. **Shield drain continuity** — each 0.6 mm shielded lead terminates its drain to a single star point near the REF2025 analog ground island, NOT to chassis. Double-check ADS131M08 AVSS / DVSS split.
3. **ESD at entry** — board already has `SP0503BAHTG` TVS. **Audit**: verify one TVS channel per electrode lead near the connector. If sparse, the alpha-to-beta change is cheap (32× SP0503 = 96 channels).
4. **Boot/bend radius** — 1.5 mm DIN is fragile at cable-to-plug. Add 3D-printed or silicone boots, or dual-wall heat-shrink (3M EPS-300) with internal hot-melt adhesive.
5. **Pull-test standard** — every plug survives 2 N axial tug indefinitely, 20 N once (loose ISO/IEC 60601-1 strain-relief guidance).
6. **Service loop** — 30-40 mm slack inside the enclosure so plugs can be re-seated without stressing PCB pads.

---

## 8. Architecture implications for the beta rev

Moving the "head-worn" boundary from the PCB to the brain-box changes the
beta design significantly:

- **Brain-box** becomes a real subproject (a passive fan-out PCB designed to sit on the cap near the back of the head, with the multipole quick-disconnect on the far side).
- **Amp board** dimensions are no longer constrained by head-mount. Can be larger, can host a proper 2S Li-ion + ESP32-S3 + RF shield can.
- **Cable between them** becomes a first-class spec: 30-60 cm shielded bundle terminated in HD D-Sub HD78 or LEMO EGG.4B; flex-life + shield continuity are design requirements.
- **Battery math** eases: belt-pack can carry 2S 18650 pair (~90 g, ~25 Wh) without ergonomic pain — plenty for 4-6 h at <500 mA and for future higher sample rates.

---

## 9. Open decisions

- [ ] Brain-box: cap-integrated (sewn into textile cap) vs. rigid puck at the back of the head?
- [ ] Amp-to-brain-box connector: HD D-Sub HD78 (now) or LEMO EGG.4B (clinical future)?
- [ ] Battery: keep USB power bank for alpha; decide LiPo vs 18650 vs LiFePO4 at beta-freeze.
- [ ] Enclosure material: aluminum Hammond for beta v1; CNC custom for beta v2.
- [ ] Add a dummy-load resistor or a 100 µF buffer cap to defeat USB-bank idle cutout — bench-test first.
- [ ] Measure battery-chemistry noise floor on our unit before writing any paper.
