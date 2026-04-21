# FreeEEG128 — PCB fabrication submission packet

Checklist + packet description for sending the current KiCAD-10-format
design out to a fab-and-assembly (PCBA) house. Intended state:
**KiCAD 10 as-is, no beta-rev schematic edits applied yet**. The
`CHANGES-beta.md` edits (USB-C, LEDs, TTL trigger, STDC14, LT3045,
etc.) are out of scope for this packet — this is the alpha-upgraded
baseline.

See `CHANGES-beta.md` §10 for design-time decisions that precede the
beta-rev schematic edits (different scope from this packet).

## 1. What a fab house gets

```
pcb/out/gerbers/              — 18 gerber files + drill (.drl)
pcb/out/pos.csv               — pick-and-place (centroid) data
pcb/out/bom.csv               — BOM with refs/values/footprints/quantities
pcb/README.md                 — one-page project description
pcb/FAB-SUBMISSION.md         — this file; cover letter + decisions
pcb/reports/drc-baseline.rpt  — optional; DRC summary (0 unconnected)
```

Zip everything under `pcb/out/` plus this file before uploading.

## 2. Board basics

- **Size**: octagonal PCB, ~100 mm across (exact from `Edge_Cuts.gm1`)
- **Layers**: 4 (F_Cu / In1_Cu / In2_Cu / B_Cu)
- **Copper**: 1 oz default; request 1 oz both sides
- **Finish**: **ENIG** (gold-plated pads) — critical for the low-noise analog front end, superior flatness vs HASL
- **Minimum trace / spacing**: check `pcb/reports/drc-baseline.rpt`; fab default is typically 5 mil / 5 mil; JLCPCB supports 4 mil
- **Minimum drill**: 0.2 mm (see drill file T1C0.200)
- **Via**: use vias 0.4 mm (drill) / 0.6 mm (pad)
- **Soldermask**: green (any colour works; green is cheapest)
- **Silkscreen**: white, both sides
- **Stackup**: standard 4-layer FR4; **request controlled impedance** if the fab offers it — 50 Ω single-ended on the SPI fabric is ideal for the sample-sync cascade. (Most fabs default to ~50 Ω on 4-layer FR4 with default stackup, so this is often a no-op.)
- **Castellated / plated half-holes**: none required
- **Panelization**: individual boards for qty ≤10; panel at assembly time if requested

## 3. BOM audit — 2026 availability notes

Based on MPN state as of early 2026. **This is a quick read, not a live
distributor pull — re-verify each part on Digi-Key / Mouser / LCSC
before placing an order.**

### Known-active, low risk (most of the BOM)

- All 0402 / 0603 **passives** (Samsung / Yageo / Murata): broadly in stock
- **ADuM3160BRWZ** (USB isolator), **ADuM1402BRWZ** (UART isolator), **ISO7341CDW** (SPI isolators): ADI/TI, active
- **SN6505BDBVR** (transformer driver): TI, active
- **REF2025AIDDC** (1.25 V / 2.5 V precision reference): TI, active
- **LP5907QMFX-3.3Q1** ×3 (ultra-low-noise LDO): TI, active. Alt `ADP7118AUJZ-3.3-R7` (ADI) also active.
- **MBR0520LT1G** (Schottky): ON Semi, active
- **LSM6DSOXTR** (IMU, 6-axis): ST, active (newer than the 2021 spec's LSM6DS3TR — upgrade this)
- **47352-1001** (Molex microSD push-push): active
- **750315371** (Würth isolation transformer): active
- **B3U-1000P** (Omron tactile switch): active
- **FC-135 32.768 kHz** (Epson): active

### Check quantity lead time — medium risk

- **STM32H743ZIT6U** — came out of shortage 2024; verify lead time at qty 5-10. Single source (ST); no drop-in alt. If the qty is tight, switch to `STM32H753ZIT6U` (identical pinout, adds crypto accelerator, same price tier).
- **ADS131M08IRSN** ×16 per board — at qty 5 boards that's 80 chips. Verify Digi-Key / Mouser stock is >80 before ordering. If low, TI's own store has often held stock that distributors don't show.
- **7B-16.000MEEQ-T** (EuroQuartz 16 MHz HSE crystal) — crystal supply has been volatile. Verify; any 16 MHz 10 pF HC-49 / 5032-4 footprint crystal works if this MPN is EOL.
- **CB3LV-3I-8M1920** (CTS 8.192 MHz XO, ADC master clock) — some ±50 ppm variants have EOL'd. Verify, or substitute with Abracon `ASFLMB-8.192MHZ-LC-T` (same 7050 footprint).

### Replace (USB-C swap, beta-rev)

- **105017-1001** (Molex Micro-B USB, ×2) — **this is the mechanical failure mode on both alpha units.** Not fab-blocking for the current packet (the part still works if delicately handled), but on the next rev this becomes a USB-C receptacle (proposed `GCT USB4125-GF-A-180`; see `CHANGES-beta.md` §1.1). Keep Micro-B for this packet only if submitting alpha-as-is.

### Headers — pick one alt each

- **20021121-00040T4LF** (2×20 1.27 mm SMD) — multiple listed alts (Samtec M50-3612042R, FTSH-120-01-F-DV). Verify cheapest in stock.
- **68021-404HLF** (2×2 right-angle) — Samtec/Harwin alts listed.
- **68021-406HLF** (2×3 right-angle) — same.

## 4. Six open decisions — defaults picked (flagged for your review)

From `CHANGES-beta.md` §10. Defaults below are my recommended choices;
**mark with 🔵 anything you want to override**.

| Decision | Default | Rationale |
| --- | --- | --- |
| TTL trigger connector (beta rev) | **3.5 mm TRS** | Compact, common on clinical amps, BNC-pigtail-convertible |
| LT3045 package (beta rev) | **MSOP-12** | Hand-solderable; visual inspection easier |
| Board outline | **Keep octagonal** | Matches the geodesic brand heritage; edge growth from USB-C is ~4 mm on one facet, still fits the shoulder-bag enclosure |
| Fab quantity (first run) | **5 boards** | Enough for destructive bring-up + 2 working units + 2 spares; minimum-price-per-unit hits diminishing returns above ~5 |
| Fab house | **JLCPCB with SMT assembly** (`PCB + Assembly` tier) | Cheapest end-to-end; handles 4-layer + ENIG routinely; BOM-to-order with their parts library or extended library. PCBWay is the next option if JLC parts coverage is bad. |
| Additional must-haves | **None for this packet**; reassess for beta rev | Keep scope tight |

## 5. Fab house comparison (as of April 2026)

Assumptions: **qty 5 boards**, 4-layer ENIG, ~100 mm octagonal, full SMT
assembly (150+ placements incl. 16× ADS131M08 + STM32H743 + 12 isolators/LDOs).

| House | Strengths | Caveats | Ballpark |
| --- | --- | --- | --- |
| **JLCPCB** | cheapest, huge parts library, fast; 4-layer ENIG standard; handles 0402 | US-EU shipping 5-10 days; some specialty MPNs not in their library (extended parts fee $3 each) | **~$100-250 fab** + **~$400-700 parts** + **~$100-200 assembly** = **~$600-1150/run** |
| **PCBWay** | broader parts coverage than JLC (Digi-Key matched), often better quality | ~1.5-2× JLCPCB cost | ~$1000-1800/run |
| **MacroFab** | US-assembled, instant quote, MPN-transparent | ~3-4× JLC | ~$2000-3500/run |
| **Seeed Fusion** | similar tier to JLC | smaller parts library | ~$800-1200/run |
| **Oshpark + external assembly** | premium US-made purple boards | separate BOM sourcing + assembly = complex | split cost, usually $1500+ |

## 6. Pre-submission checklist

Run through this before clicking Submit:

- [ ] Open `pcb/kicad/FreeEEG128-alpha.kicad_pcb` in KiCAD 10 one more time; File → Save (ensures project files are fully up to date)
- [ ] Re-run `kicad-cli pcb drc` — confirm still **0 unconnected items**
- [ ] Re-run `kicad-cli pcb export gerbers ... --output pcb/out/gerbers/` to refresh
- [ ] Zip `pcb/out/gerbers/` into a single `.zip` for upload
- [ ] Verify BOM CSV is readable by the chosen fab's parts matcher (JLCPCB has a specific format — you may need to transform)
- [ ] Verify pick-and-place `pos.csv` column order matches what the fab expects
- [ ] **Parts availability spot check**: open Digi-Key / Mouser / LCSC and verify ≥6 of the medium-risk MPNs are in stock at >qty_needed × 2
- [ ] Confirm you're submitting the alpha-as-is (NOT beta-rev) — the Micro-B connectors in this packet are the weak link
- [ ] Save a copy of the exact submitted gerbers + BOM under `pcb/out-submitted/` with a dated tag, so we know what physically got manufactured

## 7. After submission

- **1-5 days**: fab DFM review. They may flag things (silkscreen too thin, tented via fills, etc.). Respond quickly or waivers may void warranty.
- **5-10 days**: PCB fabrication + SMT assembly.
- **2-7 days**: shipping (JLC → US ~5-7 days via DHL express).
- **On receipt**: visual inspection (bent pins, solder bridges, missing parts), USB enumeration smoke test (P0.1), then full bring-up.

Budget: plan on **~2-3 weeks from order to first bring-up**.

## 8. This packet is the alpha-refreshed, not the beta rev

To emphasize: submitting this packet gets you a new alpha-equivalent board
with the same design including the Micro-B connectors that appear to
have failed mechanically on both existing units. The value is:

- **Validates the fab pipeline** with a known-design (low risk of
  schematic errors biting us on the first rev)
- **Gives a working baseline** to compare the beta rev against later
- **Uses already-verified gerbers**, not a new untested layout

If the goal is "one board that doesn't have the Micro-B problem,"
**do the beta rev first** (see `CHANGES-beta.md`) — that's a GUI
KiCAD session of several hours of work, not the scope of this packet.

## 9. Recommended next step

If moving forward tonight:

1. **Get an instant quote from JLCPCB**: upload `pcb/out/gerbers.zip` to
   their online instant-quote tool. No commitment; takes 2 minutes.
2. **Screenshot the PCB quote + the SMT assembly quote**: the latter
   will flag any BOM parts not in their library.
3. **Paste the uncovered-MPN list here** and we'll source alts from
   Digi-Key / Mouser and decide whether to switch them or submit them
   as manually-supplied parts.

Then we decide whether to order, or whether to pivot to the beta rev
first.
