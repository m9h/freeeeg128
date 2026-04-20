#!/usr/bin/env python3
"""Convenience launcher for the quality dashboard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from freeeeg128.dashboard import main

if __name__ == "__main__":
    main()
