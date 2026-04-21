#!/usr/bin/env python3
"""Convert the NeuroIDSS 2021 BOM CSV into JLCPCB's expected format.

JLCPCB Standard PCBA BOM expects columns:
    Comment, Designator, Footprint, LCSC Part #

plus optional ``Manufacturer Part Number`` which they use to auto-match
against their LCSC catalog.

Our source file (``pcb/out/bom-2021-with-mpns.csv``) has:
    Id, Designator, Package, Quantity, Designation, Supplier and ref,
    Manufacturer Part Number or Seeed SKU, Description, alt, …

Plus a trailing field of empty columns (,,,,,,) that JLCPCB's parser
chokes on.  This script emits a clean UTF-8 CSV in JLCPCB's expected
column order, preserving the first alternate MPN as a comment if present.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def transform(src: Path, dst: Path) -> int:
    rows_out = 0
    with src.open(newline="") as fin, dst.open("w", newline="") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Comment", "Designator", "Footprint",
                         "LCSC Part #", "Manufacturer Part Number"])
        header = next(reader)  # discard the noisy original header
        for row in reader:
            if not row or not row[0].strip():
                continue  # skip blank rows
            # Columns we care about
            designator = row[1].strip().strip('"')
            footprint  = row[2].strip()
            comment    = row[4].strip()   # the "Designation" column (value)
            mpn        = row[6].strip() if len(row) > 6 else ""
            if not designator:
                continue
            writer.writerow([comment, designator, footprint, "", mpn])
            rows_out += 1
    return rows_out


def main() -> None:
    if len(sys.argv) not in (1, 3):
        print(__doc__)
        print("usage: bom_to_jlcpcb.py [input.csv output.csv]")
        sys.exit(2)
    if len(sys.argv) == 3:
        src = Path(sys.argv[1])
        dst = Path(sys.argv[2])
    else:
        root = Path(__file__).resolve().parent.parent.parent
        src = root / "pcb" / "out" / "bom-2021-with-mpns.csv"
        dst = root / "pcb" / "out" / "bom-jlcpcb.csv"
    n = transform(src, dst)
    print(f"wrote {n} rows → {dst}")


if __name__ == "__main__":
    main()
