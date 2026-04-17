"""MNE-Python online preprocessing timing.

5-minute 128-channel synthetic epoch: bandpass filter + ICA (15 components).
Representative of the slowest steady-state operation we might ever do on the
Pi during a live session.
"""

from __future__ import annotations

import numpy as np

from . import emit, timed


def main() -> None:
    import mne

    mne.set_log_level("ERROR")

    n_ch = 128
    fs = 250
    duration_s = 300  # 5 minutes
    n_samples = fs * duration_s

    rng = np.random.default_rng(0)
    data = rng.standard_normal((n_ch, n_samples)).astype(np.float32) * 1e-6  # microvolts

    info = mne.create_info(
        ch_names=[f"ch{i:03d}" for i in range(n_ch)],
        sfreq=fs,
        ch_types="eeg",
    )
    raw = mne.io.RawArray(data, info, verbose=False)

    with timed("mne.filter_1_40hz"):
        raw.filter(l_freq=1.0, h_freq=40.0, fir_design="firwin", verbose=False)

    with timed("mne.ica_fit_15"):
        ica = mne.preprocessing.ICA(n_components=15, random_state=0, max_iter=200, verbose=False)
        ica.fit(raw, verbose=False)

    emit("mne.ica_n_components", 15, "count")


if __name__ == "__main__":
    main()
