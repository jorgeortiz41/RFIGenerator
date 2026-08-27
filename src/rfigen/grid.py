"""Time and frequency grid helpers."""

from __future__ import annotations

import numpy as np

from rfigen.config import DEFAULT_PROFILE_CHANNELS_GHZ, ExperimentConfig


def make_time_axis(config: ExperimentConfig) -> np.ndarray:
    count = max(1, int(round(config.duration_s * config.sample_rate_hz)))
    return np.arange(count, dtype=float) / config.sample_rate_hz


def make_frequency_axis(config: ExperimentConfig) -> np.ndarray:
    if config.frequency_channels_ghz is not None:
        return np.asarray(config.frequency_channels_ghz, dtype=float)
    if (
        np.isclose(config.frequency_start_ghz, 20.0)
        and np.isclose(config.frequency_stop_ghz, 30.0)
        and config.frequency_bins == 21
    ):
        return np.asarray(DEFAULT_PROFILE_CHANNELS_GHZ, dtype=float)
    return np.linspace(
        config.frequency_start_ghz,
        config.frequency_stop_ghz,
        config.frequency_bins,
        dtype=float,
    )


def make_direction_axes(config: ExperimentConfig, samples: int) -> tuple[np.ndarray, np.ndarray]:
    azimuth = np.empty(samples, dtype=float)
    elevation = np.empty(samples, dtype=float)
    for index in range(samples):
        direction = config.scan_directions[index % len(config.scan_directions)]
        azimuth[index] = float(direction["azimuth_deg"])
        elevation[index] = float(direction["elevation_deg"])
    return azimuth, elevation
