"""Tests for the per-channel signal-quality assessor."""

from __future__ import annotations

import numpy as np
import pytest

from freeeeg128 import quality


FS = 250.0


def _sinusoid(hz: float, amp_uv: float, n: int = 500) -> np.ndarray:
    t = np.arange(n) / FS
    return (amp_uv * np.sin(2 * np.pi * hz * t)).astype(np.float64)


def test_flat_is_bad():
    x = np.zeros(500)
    r = quality.assess_channel(x, FS)
    assert r.code == quality.QualityCode.BAD


def test_missing_is_missing():
    r = quality.assess_channel(np.array([]), FS)
    assert r.code == quality.QualityCode.MISSING


def test_alpha_signal_is_good():
    x = _sinusoid(10.0, amp_uv=10.0) + np.random.default_rng(0).standard_normal(500)
    r = quality.assess_channel(x, FS)
    assert r.code == quality.QualityCode.GOOD
    assert 8.0 <= r.dominant_hz <= 12.0
    assert r.alpha_uv_rms > 1.0


def test_saturated_is_bad():
    x = np.full(500, 1e6)  # 1 V — vastly beyond any biological signal
    r = quality.assess_channel(x, FS)
    assert r.code == quality.QualityCode.BAD


def test_low_amplitude_is_marginal():
    # signal below bad_threshold but above flat_threshold
    x = 0.2 * np.sin(2 * np.pi * 10.0 * np.arange(500) / FS)
    r = quality.assess_channel(x, FS)
    assert r.code == quality.QualityCode.MARGINAL


def test_array_shape():
    rng = np.random.default_rng(0)
    data = rng.standard_normal((4, 500)) * 5.0
    results = quality.assess_array(data, FS)
    assert len(results) == 4
    assert all(isinstance(r, quality.QualityResult) for r in results)
