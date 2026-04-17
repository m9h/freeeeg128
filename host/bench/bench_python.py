"""Python / NumPy baseline.  Sanity check that the host can do the arithmetic."""

from __future__ import annotations

import numpy as np

from . import emit, timed


def main() -> None:
    # 1) complex FFT on a 128 x 25_000 block  (5 min of 128-ch @ ~83 Hz; representative of online work)
    a = np.random.randn(128, 25_000).astype(np.complex64)
    with timed("python.fft_128x25000_complex64"):
        np.fft.fft(a)

    # 2) real large dot product — memory-bandwidth proxy
    x = np.random.randn(2_000_000).astype(np.float32)
    y = np.random.randn(2_000_000).astype(np.float32)
    with timed("python.dot_2M_float32"):
        x @ y

    # 3) log of ones (pure ALU)
    z = np.ones(1_000_000, dtype=np.float64)
    with timed("python.log_1M_float64"):
        np.log(z)

    emit("python.numpy_version", float(np.__version__.split(".")[1]), "minor")


if __name__ == "__main__":
    main()
