# FreeEEG128-beta — schematic and layout change list

Design document for the `FreeEEG128-beta` revision. Starting point is the
KiCAD 10 baseline committed in [`README.md`](README.md) (upstream
NeuroIDSS alpha, format-upgraded only, zero design changes yet).

**MCU decision already settled**: STM32H743ZIT6 retained. STM32N6 deferred
to a future v2 — see the MCU-choice memory and [`../ROADMAP.md`](../ROADMAP.md)
§B0.1.

This doc is the plan-of-record before any schematic or layout edit. Every
change below lists:

- **Why**: the lesson / bug / goal driving it
- **Where**: which sheet(s) of the hierarchical schematic are touched
- **What**: the specific component swap / addition
- **Layout impact**: the footprint / edge / routing consequence
- **Proposed MPN**: a concrete part to spec (subject to 2026 availability check)

---

## 1. Connector upgrades (the alpha failure mode)

### 1.1 USB Micro-B → USB-C on both J99 and J103

**Why.** Both alpha units we've tested fail to enumerate on any host. The
unused plastic-wrapped FreeEEG32 fails identically. The common factor is
the SMT Micro-B receptacle (Molex 105017-1001) — notoriously fragile
solder joints and loose mechanical coupling. USB-C is the 2026 standard,
has far more robust mechanical retention, and is reversible.

**Where.** `USB_DATA.kicad_sch` (J99) and `USB_POWER.kicad_sch` (J103).

**What.** Replace the two `USB_Micro-B_Molex-105017-0001` footprints with
a USB-C 2.0 receptacle (sink only; we don't need USB-PD since the board
draws <5 W).

**Layout impact.** USB-C receptacle is physically larger (~8.9 × 7.3 mm
SMT mid-mount) than Micro-B (~6 × 5 mm). The board edge near the USB
ports needs ~3-4 mm more clearance per connector. Verify the octagonal
outline still hosts both connectors back-to-back — we may need to grow
one facet of the octagon by 4-5 mm.

**Proposed MPN.**

- Preferred: `GCT USB4125-GF-A-180` — USB-C 2.0, 16-pin, SMT mid-mount,
  through-hole board-lock posts, ~$0.50 @ qty 100. Well stocked on
  Digi-Key / Mouser / LCSC.
- Alt: `Amphenol 10118194-0001LF` — similar class, widely available.
- Alt (medical-grade): `Wuerth 632723100011` — shielded top-mount.

**Wiring.** USB-C 2.0 → USB 2.0 uses pins A4/A5 VBUS, A6/A7 D+/D-, A1/A12
GND, B6/B7 D+/D- (mirrored), B1/B12 GND. Tie VBUS pairs, GND pairs, D+
pairs, D- pairs together on the board. CC1/CC2 each need a 5.1 kΩ
pull-down to GND to advertise as a UFP (sink) — no CC-logic chip needed
for USB 2.0 only.

### 1.2 Debug header: 2×5 0.1″ → STDC14 fine-pitch 1.27 mm

**Why.** Modern ST-Link V3 (our planned firmware-rewrite debugger) ships
with an STDC14 (Samtec FTSH 2×7 1.27 mm) cable as its default. The alpha's
2×5 0.1″ header is legacy hobbyist pitch and needs a $10 adapter in every
session. STDC14 also routes SWDIO/SWCLK/SWO, 3.3 V, GND, TX/RX, NRST, and
extra IO in one shrouded connector — future-proof.

**Where.** `MCU.kicad_sch` (the SWD header near the STM32).

**What.** Replace `PinSocket_2x05_P2.54mm_Vertical` with
`Samtec_FTSH-107-01-x-DV_2x07_P1.27mm_Vertical`.

**Layout impact.** STDC14 is ~10.4 × 4.8 mm vs ~13.0 × 7.6 mm for the old
2×5 0.1″ — *saves* PCB real estate. Routing is cleaner (shrouded).

**Proposed MPN.** `Samtec FTSH-107-01-L-DV-K-TR` (surface-mount, keyed).

---

## 2. Status LEDs (the "is it alive?" problem)

**Why.** The alpha has zero LEDs. Today's diagnostic session spent 90
minutes proving it wasn't a power issue with no visual indicator to
confirm anything. Status LEDs are cheap ($0.05 per LED) and save hours of
debugging over the lifetime of the platform.

**Where.** Various sheets — grouped per supply rail and function.

**What to add (6 LEDs):**

| Ref  | Color  | Driven by                        | Meaning                     | Sheet                       |
| ---- | ------ | -------------------------------- | --------------------------- | --------------------------- |
| D_PG_H | red    | USB_DATA VBUS (host side)        | "host USB plugged in"       | `USB_DATA.kicad_sch`        |
| D_PG_I | green  | isolated 5 V after SN6505        | "isolated power good"       | `POWER.kicad_sch`           |
| D_AVDD | green  | AVDD 3.3 V rail post-LT3045      | "analog supply up"          | `AVDD.kicad_sch`            |
| D_VDD  | green  | VDD 3.3 V rail post-LP5907       | "digital supply up"         | `VDD.kicad_sch`             |
| D_USR1 | blue   | STM32 GPIO                       | firmware-controlled (CDC active) | `MCU.kicad_sch`        |
| D_USR2 | blue   | STM32 GPIO                       | firmware-controlled (SD activity / fault) | `MCU.kicad_sch` |

**Layout impact.** Six 0603 footprints + six 0603 resistors = ~0.5 cm² per
LED+resistor pair. Place the power-good LEDs on the *same face as their
rail's connector* so you can see them at a glance while debugging.

**Proposed MPN.** Any standard 0603 LED family — Kingbright
`APT2012SRCPRV` (red), `APT2012LSECK` (green), `APT2012QBC-D` (blue),
with `RC0603JR-074K7L` 4.7 kΩ current-limit resistors (≈0.7 mA from
3.3 V; dim but enough to see and low power).

---

## 3. Isolated TTL trigger input for Labstreamer

**Why.** The alpha has no stimulus-sync input at all. The Labstreamer
(already on hand) speaks TTL on BNC. Adding a proper isolated trigger
input lets us drop Labstreamer markers directly into the EEG stream and
pass the Black 2017 validation gate (eyes-closed alpha + later P300
latency).

**Where.** New subsheet `TRIGGER.kicad_sch`. Panel-mount connector on the
amp-box enclosure, wires through an isolator into a spare STM32 GPIO.

**What.**

1. Panel-mount connector on the enclosure face: **3.5 mm TRS** (CUI
   `SJ-3523-SMT`) — compact, common on clinical amps, or **BNC** if we
   want lab-standard and don't mind the volume.
2. Input ESD protection: `SP0503BAHTG` (already in BOM).
3. Schmitt-trigger input buffer: `74LVC1G17` (single Schmitt, SC-70) for
   clean logic edges from the TTL source.
4. Isolation across the medical barrier: one spare ADuM1402 channel
   (isolator already on the board has 4 channels; the ISO_UART sheet
   uses 2 for TX/RX; 2 remain — use one of them).
5. Terminate at an STM32 GPIO with EXTI capability (TIM input-capture
   GPIO preferred for timestamping in firmware).

**Layout impact.** ~1 cm² for the Schmitt + isolator-channel wiring,
plus the panel connector (which can be a fly-lead rather than on the
PCB if enclosure geometry demands).

**Note on Labstreamer integration.** The Labstreamer has multiple TTL
out lines (BNC). Wire its "event strobe" output → 3.5 mm → ESD → Schmitt →
ADuM1402 spare channel → STM32 EXTI / TIM input capture. Firmware
timestamps the rising edge with µs precision and emits a marker packet
in-band with the EEG stream.

---

## 4. Lock USB to Full-Speed in the hardware + firmware

**Why.** The alpha's `.ioc` configures both `USB_DEVICE` (FS) and
`USB_OTG_HS` simultaneously, with PB14/PB15 as `Device_Only_FS`. The
ADuM3160 isolator is **FS-only** (12 Mbps max) — HS cannot pass through
it. This is a firmware-side cleanup: remove `USB_OTG_HS` from the pin
allocations, route any freed pins to other uses.

**Where.** `MCU.kicad_sch` (pin labels), firmware `.ioc`.

**What.** Mark PB14/PB15 as FS-only in the schematic labels. Any pins
previously allocated to HS PHY get freed for GPIO use (LED drive, trigger
input, etc.).

**Layout impact.** None — pins stay in place, just the net names change.

---

## 5. BOM refresh (2026 availability + small upgrades)

### 5.1 IMU: LSM6DS3TR → LSM6DSOXTR

**Why.** LSM6DSOXTR is newer, still in production through 2030+, lower
power, better temperature stability. Already listed as the first alt MPN
in the 2021 BOM.

**Where.** `ACCEL&GYRO.kicad_sch`.

**What.** Swap `LSM6DS3TR` → `LSM6DSOXTR`. Pin-compatible 14-LGA package;
schematic symbol needs Value edit only; footprint unchanged.

### 5.2 Add LT3045 on AVDD rail

**Why.** The LP5907 on AVDD (6.5 µVrms, 10 Hz-100 kHz) is fine. The
LT3045 is the industry low-noise gold standard: **0.8 µVrms** across
10 Hz-100 kHz, 79 dB PSRR at 1 MHz, 500 mA. An 8× noise improvement on
the analog rail is meaningful for a 24-bit Δ-Σ front-end.

**Where.** `AVDD.kicad_sch`.

**What.** Replace LP5907 on AVDD with LT3045. VDD and IOVDD rails stay
on LP5907 (good enough for digital).

**Layout impact.** LT3045 is 12-lead MSOP (3×3 mm) vs LP5907 SOT-23-5
(1.6×2.9 mm). Slightly larger footprint, needs a ground-pour exposed pad
for thermal dissipation under the part.

**Proposed MPN.** `LT3045EMSE#PBF` (12-MSOP) or `LT3045EDD#PBF` (DFN).
Prefer MSOP for hand-assembly friendliness and visual inspection.

### 5.3 Full BOM pass on 36 line items

To be done separately: verify each MPN on Digi-Key / Mouser / LCSC for
April 2026 availability. Swap any EOL parts for the alt MPNs already
listed in the original BOM (columns 9-12). Specifically to audit:

- STM32H743ZIT6 — should be fine (long lifecycle), but verify stock
- ADS131M08 — verify 16× qty available in one lot
- ADUM3160BRWZ / ADUM1402BRWZ / ISO7341CDW — all current
- SN6505BDBVR — current
- REF2025AIDDC / ADR4525 — both current
- Crystals (EuroQuartz 7B-16.000MEEQ-T, FC-135 32.768 kHz, FXO-SM7) —
  crystal supply is volatile; have alts lined up
- Molex 473521001 (microSD) — current

### 5.4 Consider adding

- **TVS on isolated side power rails** (extra ESD protection on the
  subject-contact side — low cost insurance for a medical-adjacent device).
- **Explicit layer stackup spec** in the PCB fab package: 4-layer FR4,
  controlled-impedance on SPI nets, typical 50 Ω single-ended.

---

## 6. Firmware-facing minor changes

### 6.1 BOOT0 strap — confirm wired through a button

The alpha has a user button near the USB_POWER side (visible in IMG_1612).
Confirm via schematic whether it's a **BOOT0 select** (holds chip in
system DFU bootloader on reset) or a user input. If it's not a BOOT0
strap, add one — lets us enter DFU mode cleanly without TDK pad-poking.

### 6.2 Reset button audit

Confirm a dedicated NRST button exists separate from BOOT0. On alpha
hardware the two are sometimes combined — not great for debugging.

### 6.3 SD-CD (card detect) → GPIO

Wire the microSD's CD switch to a GPIO so firmware knows when a card is
inserted. Saves polling the SDMMC.

---

## 7. What we explicitly keep unchanged

- STM32H743ZIT6 acquisition MCU (settled)
- 16× ADS131M08 analog front-end (the whole reason for the design)
- Six SPI buses (SPI1-SPI6) routing plan
- ADuM3160 USB-FS isolator
- ADuM1402 UART isolator
- 2× ISO7341C SPI isolators
- SN6505B + Würth 750315371 transformer push-pull isolated DC-DC
- REF2025 / ADR4525 precision references
- 3× LP5907 LDOs for VDD/IOVDD (keep) — AVDD is the only rail moving to LT3045
- Octagonal board outline (ideally — see §1.1 note about possible edge growth)
- 10/5 cap connector scheme (1.5 mm DIN touch-proof at electrode end
  remains; beta connector work is at the brain-box ↔ amp break — see
  [`../ENCLOSURE.md`](../ENCLOSURE.md), HD D-Sub HD78)

---

## 8. Layout implications summary

| Change                       | Δ Area      | Δ Routing                  |
| ---------------------------- | ----------- | -------------------------- |
| USB-C x2 (was Micro-B x2)    | **+4-5 mm** on one edge | D+/D- and VBUS/GND repoured |
| STDC14 header                | **−20 %** on MCU edge header | tighter SWD trace group |
| 6 × status LEDs              | +3 cm² total, distributed | 6 × short GPIO / rail traces |
| TTL trigger chain            | +1-2 cm² near edge | 1 × Schmitt + isolator channel |
| LT3045 on AVDD               | +3 mm² vs LP5907 | slightly larger thermal pad |
| LSM6DS3 → LSM6DSOXTR         | 0           | 0 (pin-compat)              |
| BOOT0 button + SD-CD wiring  | 0           | 2 × short GPIO              |

**Net PCB area change**: likely +5-8 % on one edge of the octagonal
outline to absorb the USB-C footprint growth. Everything else is within
existing keepout / silkscreen budget.

---

## 9. Sequencing

1. **Schematic edits** (§1-4, 6): in KiCAD Schematic Editor on the NUC.
   Can do most symbol swaps and additions via the GUI. ERC baseline
   should come down significantly once library links are resolved.
2. **Symbol / footprint setup**: add new footprints for USB-C, STDC14,
   LT3045 to a local `beta.pretty` library; verify pin mapping against
   datasheets.
3. **PCB layout edits** (§1, 2, 3, 5.2): in KiCAD PCB Editor. Largest
   lift is the USB-C re-layout near the board edge. Preserve the six
   SPI-bus analog routing carefully — don't let the USB-C work disturb
   it.
4. **DRC + ERC** clean pass. Target: 0 unconnected, 0 errors, warnings
   reviewed and dismissed only if justified.
5. **Regenerate fab artefacts** via `kicad-cli` (same commands as
   [`README.md`](README.md)).
6. **BOM rebuild**: full 2026 availability audit + new parts priced.
7. **Fab quote** from 2-3 houses (JLCPCB, PCBWay, MacroFab). Decide
   qty and timeline.
8. **Review the design** at the quote stage against the validation gate
   (can we reproduce Black 2017 eyes-closed alpha with this rev?).

---

## 10. Open decisions for the user

Before any edit starts:

- [ ] TTL trigger input connector: **3.5 mm TRS** (compact) or **BNC**
  (lab-standard)?
- [ ] LT3045 package preference: **MSOP** (hand-solderable) or **DFN**
  (smaller, reflow-only)?
- [ ] Keep the octagonal board outline, or make it a simple rectangle if
  the USB-C edge growth breaks the 8-fold symmetry? (Octagonal is
  distinctive and matches the "geodesic" brand heritage; rectangle is
  easier to pack into a belt-pack enclosure.)
- [ ] Target fab quantity: 5, 10, 20?
- [ ] Target fab house: JLCPCB (cheap, Chinese), PCBWay (mid), MacroFab
  (US-assembled), or Seeed Fusion?
- [ ] Any additional must-haves before fab? (RTC battery backup? Extra
  user IO? External flash for firmware large-binary storage?)

---

## 11. Done when

- New schematic compiles under `kicad-cli sch erc` with < 50 remaining
  violations (down from 2,328), all justified.
- New PCB passes `kicad-cli pcb drc` with 0 unconnected items, 0 errors,
  < 100 warnings (down from 1,129), all silk/mask cosmetic.
- Full fab bundle regenerates cleanly into `pcb/out-beta/`.
- `CHANGES-beta.md` ticks every checkbox in §10.
- Fab quote in hand from at least two vendors.
