"""BrainFlow SYNTHETIC_BOARD stream: the stand-in for real FreeEEG128 data.

When the FreeEEG128 firmware is ready, we swap the board id for our new one;
the rest of the pipeline stays identical.
"""

from __future__ import annotations

import time

from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams

from . import emit


def main() -> None:
    params = BrainFlowInputParams()
    board_id = BoardIds.SYNTHETIC_BOARD.value
    board = BoardShim(board_id, params)

    duration_s = 60
    expected_rate = BoardShim.get_sampling_rate(board_id)

    board.prepare_session()
    board.start_stream()
    t0 = time.perf_counter()
    time.sleep(duration_s)
    data = board.get_board_data()
    wall = time.perf_counter() - t0
    board.stop_stream()
    board.release_session()

    n_samples = data.shape[1]
    expected = expected_rate * duration_s
    drop_frac = max(0.0, (expected - n_samples) / expected)

    emit("brainflow.rows", int(data.shape[0]), "count")
    emit("brainflow.samples_captured", int(n_samples), "count")
    emit("brainflow.samples_expected", int(expected), "count")
    emit("brainflow.drop_fraction", round(drop_frac, 6), "frac")
    emit("brainflow.wall_s", round(wall, 2), "s")


if __name__ == "__main__":
    main()
