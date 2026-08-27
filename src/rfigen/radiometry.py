"""Clean radiometric signal simulation."""

from __future__ import annotations

import numpy as np

from rfigen.config import RadiometryConfig


def simulate_clean_radiometry(
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    config: RadiometryConfig,
    rng: np.random.Generator,
    azimuth_deg: np.ndarray | None = None,
    elevation_deg: np.ndarray | None = None,
) -> np.ndarray:
    """Return an MP-3000A-like brightness temperature profile field in Kelvin."""

    time_norm = time_s / max(float(time_s[-1]) if time_s.size > 1 else 1.0, 1.0)
    freq_norm = (frequency_ghz - frequency_ghz.min()) / np.ptp(frequency_ghz)

    if azimuth_deg is None:
        azimuth_deg = np.zeros(time_s.size)
    if elevation_deg is None:
        elevation_deg = np.full(time_s.size, 19.8)

    direction_scale = _direction_scale(azimuth_deg, elevation_deg, config)
    weather = config.atmospheric_variation_k * np.sin(2 * np.pi * (time_norm * 0.65 + 0.08))
    drift = 0.7 * config.atmospheric_variation_k * np.sin(2 * np.pi * time_norm * 0.08)

    decay = config.spectral_slope_k * (freq_norm ** 0.82)
    water_vapor_shoulders = config.profile_bump_k * np.exp(-0.5 * ((frequency_ghz - 22.35) / 0.55) ** 2)
    weak_27ghz_lift = 4.0 * np.exp(-0.5 * ((frequency_ghz - 27.4) / 0.25) ** 2)
    profile = config.baseline_k + decay + water_vapor_shoulders + weak_27ghz_lift

    baseline = direction_scale[:, None] * profile[None, :] + weather[:, None] + drift[:, None]
    noise = rng.normal(0.0, config.receiver_noise_k, size=baseline.shape)
    spikes = _profile_spikes(time_s.size, frequency_ghz.size, config, rng)
    return baseline + noise + spikes


def _direction_scale(
    azimuth_deg: np.ndarray,
    elevation_deg: np.ndarray,
    config: RadiometryConfig,
) -> np.ndarray:
    scale = np.ones(elevation_deg.size, dtype=float)
    scale[np.isclose(elevation_deg, 90.0)] = config.zenith_scale
    scale[elevation_deg > 100.0] = config.high_elevation_scale
    scale += 0.045 * np.sin(np.deg2rad(azimuth_deg * 1.7))
    return scale


def _profile_spikes(
    samples: int,
    channels: int,
    config: RadiometryConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    if config.spike_probability <= 0:
        return np.zeros((samples, channels), dtype=float)
    spikes = np.zeros((samples, channels), dtype=float)
    mask = rng.random(samples) < config.spike_probability
    for row in np.flatnonzero(mask):
        channel = int(rng.integers(0, channels))
        width = max(1, int(rng.integers(1, 3)))
        start = max(0, channel - width)
        stop = min(channels, channel + width + 1)
        spikes[row, start:stop] += config.spike_power_k
    return spikes
