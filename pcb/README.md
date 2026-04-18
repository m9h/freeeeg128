# FreeEEG128 PCB — KiCAD project

**Baseline**: upstream NeuroIDSS FreeEEG128-alpha (September 2021,
KiCAD 5.99), upgraded to **KiCAD 10.0.1 format** on 2026-04-17 via
`kicad-cli sch upgrade` / `kicad-cli pcb upgrade`.

This is the starting point for the `FreeEEG128-beta` revision planned in
[`../ROADMAP.md`](../ROADMAP.md). See `CHANGES-beta.md` (upcoming) for the
specific schematic/layout deltas.

## Contents

- `kicad/` — KiCAD 10 project: 32 hierarchical schematics + 4-layer PCB +
  local libraries + 3D models
- `out/` — Fab-ready artefacts freshly generated from the upgraded project:
  - `gerbers/` — 4-layer gerbers + drill file (18 files, ~3.5 MB)
  - `pos.csv` — pick-and-place (centroid) data
  - `bom.csv` — bill of materials with MPNs
- `reports/` — ERC/DRC reports from the upgraded-but-unmodified baseline
  - `erc-baseline.rpt` — 2,328 ERC violations (mostly global-label
    cross-sheet connections flagged by KiCAD 10 stricter rules + library
    cache mismatches from the 5.99 era; design is electrically complete)
  - `drc-baseline.rpt` — 1,129 DRC violations (**0 unconnected items** —
    the critical metric; remainder is silkscreen / soldermask / drill-size
    issues from modern fab rule defaults)

## Upstream attribution

The alpha design is © NeuroIDSS (David Vivancos) and upstream at
<https://github.com/neuroidss/FreeEEG128-alpha>, licensed AGPL-3.0.
Local copy in this repo has been upgraded to KiCAD 10 format; no schematic
or layout changes have been made at this commit.

## Regenerating the fab package

From `pcb/kicad/`:

```bash
# gerbers + drill
kicad-cli pcb export gerbers FreeEEG128-alpha.kicad_pcb --output ../out/gerbers/
kicad-cli pcb export drill   FreeEEG128-alpha.kicad_pcb --output ../out/gerbers/

# pick-and-place
kicad-cli pcb export pos FreeEEG128-alpha.kicad_pcb --output ../out/pos.csv --format csv

# BOM
kicad-cli sch export bom FreeEEG128-alpha.kicad_sch --output ../out/bom.csv

# re-run checks
kicad-cli sch erc FreeEEG128-alpha.kicad_sch --output ../reports/erc.rpt --severity-error --severity-warning
kicad-cli pcb drc FreeEEG128-alpha.kicad_pcb --output ../reports/drc.rpt --severity-error --severity-warning
```

Flatpak users: prefix with `flatpak run --command=kicad-cli org.kicad.KiCad`.
