#!/usr/bin/env python3
"""Rename KiCAD CPL columns to JLCPCB's expected names.

KiCAD kicad-cli emits: ``Ref, Val, Package, PosX, PosY, Rot, Side``
JLCPCB expects:        ``Designator, Mid X, Mid Y, Layer, Rotation``

Also drops the Val/Package columns (JLC doesn't need them — the BOM has
that info) and normalizes ``Side`` to ``Top``/``Bottom`` (title case).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def transform(src: Path, dst: Path) -> int:
    with src.open(newline="") as fin, dst.open("w", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        n = 0
        for row in reader:
            designator = row["Ref"].strip().strip('"')
            side = row["Side"].strip().lower()
            layer = "Top" if side == "top" else "Bottom"
            writer.writerow([designator, row["PosX"], row["PosY"], layer, row["Rot"]])
            n += 1
        return n


def main() -> None:
    if len(sys.argv) not in (1, 3):
        print(__doc__)
        print("usage: pos_to_jlcpcb.py [input.csv output.csv]")
        sys.exit(2)
    if len(sys.argv) == 3:
        src = Path(sys.argv[1])
        dst = Path(sys.argv[2])
    else:
        root = Path(__file__).resolve().parent.parent.parent
        src = root / "pcb" / "out" / "pos.csv"
        dst = root / "pcb" / "out" / "cpl-jlcpcb.csv"
    n = transform(src, dst)
    print(f"wrote {n} rows → {dst}")


if __name__ == "__main__":
    main()
