"""FreeEEG128 host Python package.

Implements the wire protocol spec in docs/packet-format.md and the host
command set in docs/command-protocol.md.  Transport-agnostic: reads and
writes framed byte sequences which can ride on USB-CDC (real device),
pipes (testing), or loopback (synthetic).
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import protocol, synthetic

__all__ = ["protocol", "synthetic"]
