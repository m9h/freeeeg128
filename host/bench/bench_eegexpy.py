"""EEG-ExPy VisualP300 pipeline, synthetic backend.

If eeg-expy is not installed we emit a 'skipped' metric and exit 0.  This lets
``make bench`` keep going.
"""

from __future__ import annotations

import importlib.util
import time

from . import emit


def main() -> None:
    if importlib.util.find_spec("eegnb") is None:
        emit("eegexpy.status", 0, "skipped")
        return

    # We import lazily so the module stays optional.
    import eegnb  # noqa: F401

    # eeg-expy's experiment loop uses pygame for stimulus and BrainFlow synthetic
    # for data; under headless Pi OS we set SDL to the dummy driver and skip
    # if that still fails.
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    try:
        from eegnb.experiments.visual_p300 import p300
    except Exception as exc:  # pragma: no cover
        emit("eegexpy.import_status", 0, "failed")
        emit("eegexpy.import_error_len", len(str(exc)), "chars")
        return

    duration = 30  # short run
    t0 = time.perf_counter()
    try:
        p300.present(duration=duration, eeg=None, save_fn=None)
        ok = 1
    except Exception:
        ok = 0
    wall = time.perf_counter() - t0
    emit("eegexpy.p300_status", ok, "bool")
    emit("eegexpy.p300_wall_s", round(wall, 2), "s")


if __name__ == "__main__":
    main()
