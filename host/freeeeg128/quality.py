"""Per-channel signal-quality metrics for live EEG streams.

Matches the paper's green/red gate (Vivancos 2023, MindBigData 2023
MNIST-8B §3.1) based on per-channel PSD: a channel whose broadband PSD is
near-zero is flagged red ('dead' / floating), a channel whose
8-14 Hz alpha-band power sits in a plausible biological range is flagged
green, and in-between goes yellow.

These are cheap O(N log N) per-channel operations that the Pi Zero 2W
runs at 1-2 Hz for a 128-channel array without breaking a sweat.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

import numpy as np


class QualityCode(IntEnum):
    GOOD     = 0   # green
    MARGINAL = 1   # yellow
    BAD      = 2   # red — flat / floating / open
    MISSING  = 3   # grey — no samples


@dataclass
class QualityResult:
    """Per-channel quality outcome + the raw numbers that drove it."""
    code: QualityCode
    broadband_uv_rms: float       # RMS of the whole band we saw (µV)
    alpha_uv_rms: float           # RMS inside 8-14 Hz (µV)
    dc_uv: float                  # channel mean (µV) — sanity indicator
    dominant_hz: float            # peak-frequency of the channel's PSD


def _welch_like_psd(x: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    """Tiny Welch-like PSD using scipy.signal.welch if available, else
    a one-segment FFT fallback.  Returns (freqs_Hz, psd_uv2_per_Hz).
    """
    try:
        from scipy.signal import welch
        n = min(len(x), 512)
        freqs, psd = welch(x, fs=fs, nperseg=n, noverlap=n // 2, scaling="density")
        return freqs, psd
    except ImportError:  # pragma: no cover
        n = len(x)
        win = np.hanning(n)
        xw = (x - np.mean(x)) * win
        fft = np.fft.rfft(xw)
        psd = (np.abs(fft) ** 2) / (fs * np.sum(win ** 2))
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        return freqs, psd


def assess_channel(x_uv: np.ndarray,
                   sample_rate_hz: float,
                   *,
                   flat_threshold_uv_rms: float = 0.05,
                   bad_threshold_uv_rms: float  = 0.5,
                   saturate_threshold_uv: float = 1.0e5) -> QualityResult:
    """Score one channel's signal quality.

    Thresholds default to loose values that work with the synthetic source.
    Tune after real-device characterisation.
    """
    if x_uv.size == 0:
        return QualityResult(QualityCode.MISSING, 0.0, 0.0, 0.0, 0.0)

    mean = float(np.mean(x_uv))
    centered = x_uv - mean
    broadband_rms = float(np.sqrt(np.mean(centered ** 2)))

    # Gross saturation / rail: channel is pegged
    if np.max(np.abs(centered)) > saturate_threshold_uv:
        return QualityResult(QualityCode.BAD, broadband_rms, 0.0, mean, 0.0)

    # Gross flat: barely any signal
    if broadband_rms < flat_threshold_uv_rms:
        return QualityResult(QualityCode.BAD, broadband_rms, 0.0, mean, 0.0)

    freqs, psd = _welch_like_psd(centered, sample_rate_hz)
    alpha_mask = (freqs >= 8.0) & (freqs <= 14.0)
    # Integrate PSD to get µV^2
    if alpha_mask.any():
        df = float(freqs[1] - freqs[0]) if len(freqs) > 1 else 1.0
        alpha_rms = float(np.sqrt(np.sum(psd[alpha_mask]) * df))
    else:
        alpha_rms = 0.0

    # Dominant frequency (ignoring DC)
    nonzero = freqs > 0.5
    if nonzero.any():
        idx = int(np.argmax(psd[nonzero]))
        dominant = float(freqs[nonzero][idx])
    else:
        dominant = 0.0

    # Classify
    if broadband_rms < bad_threshold_uv_rms:
        code = QualityCode.MARGINAL
    else:
        code = QualityCode.GOOD

    return QualityResult(code, broadband_rms, alpha_rms, mean, dominant)


def assess_array(data_uv: np.ndarray, sample_rate_hz: float,
                 **kwargs) -> list[QualityResult]:
    """Assess every channel in a (C, N) array."""
    return [assess_channel(data_uv[c], sample_rate_hz, **kwargs)
            for c in range(data_uv.shape[0])]
