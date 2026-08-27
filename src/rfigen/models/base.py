"""Synthetic RFI signal models."""

from __future__ import annotations

import numpy as np

from rfigen.config import RFIConfig


def generate_rfi(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    model = config.type.lower()
    if model == "narrowband":
        return narrowband(config, time_s, frequency_ghz, rng)
    if model == "broadband":
        return broadband(config, time_s, frequency_ghz, rng)
    if model == "pulsed":
        return pulsed(config, time_s, frequency_ghz, rng)
    if model == "bursty":
        return bursty(config, time_s, frequency_ghz, rng)
    if model == "chirp":
        return chirp(config, time_s, frequency_ghz, rng)
    if model == "am":
        return amplitude_modulated(config, time_s, frequency_ghz, rng)
    raise ValueError(f"unsupported RFI model: {config.type}")


def narrowband(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    center = _center_frequency(config, frequency_ghz)
    envelope = _gaussian_band(frequency_ghz, center, config.bandwidth_mhz)
    temporal = _persistence_mask(time_s.size, config.persistence, rng)
    phase = config.phase_rad + rng.uniform(0.0, 2 * np.pi)
    flicker = 1.0 + 0.08 * np.sin(2 * np.pi * 0.07 * time_s + phase)
    return config.power_k * temporal[:, None] * flicker[:, None] * envelope[None, :]


def broadband(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    center = _center_frequency(config, frequency_ghz)
    envelope = _raised_band(frequency_ghz, center, config.bandwidth_mhz)
    temporal = _persistence_mask(time_s.size, config.persistence, rng)
    texture = rng.lognormal(mean=-0.05, sigma=0.18, size=(time_s.size, frequency_ghz.size))
    return config.power_k * temporal[:, None] * envelope[None, :] * texture


def pulsed(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    center = _center_frequency(config, frequency_ghz)
    envelope = _gaussian_band(frequency_ghz, center, config.bandwidth_mhz)
    phase = rng.uniform(0.0, config.pulse_period_s)
    pulse_position = np.mod(time_s + phase, config.pulse_period_s) / config.pulse_period_s
    pulses = (pulse_position < config.duty_cycle).astype(float)
    pulses *= _persistence_mask(time_s.size, config.persistence, rng)
    pulse_shape = 0.8 + 0.4 * rng.random(time_s.size)
    return config.power_k * pulses[:, None] * pulse_shape[:, None] * envelope[None, :]


def bursty(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    center = _center_frequency(config, frequency_ghz)
    envelope = _raised_band(frequency_ghz, center, config.bandwidth_mhz)
    bursts = np.zeros(time_s.size)
    expected_bursts = max(1, int(config.persistence * max(time_s[-1], 1.0) / max(config.pulse_period_s, 0.1)))
    starts = rng.choice(time_s.size, size=min(expected_bursts, time_s.size), replace=False)
    width = max(1, int(config.duty_cycle * config.pulse_period_s * _sample_rate(time_s)))
    for start in starts:
        stop = min(time_s.size, start + width)
        bursts[start:stop] = np.maximum(bursts[start:stop], np.hanning((stop - start) * 2)[: stop - start])
    texture = 0.75 + 0.5 * rng.random((time_s.size, frequency_ghz.size))
    return config.power_k * bursts[:, None] * envelope[None, :] * texture


def chirp(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    start = config.start_frequency_ghz or frequency_ghz.min()
    stop = config.stop_frequency_ghz or frequency_ghz.max()
    sweep = np.linspace(start, stop, time_s.size)
    if rng.random() < 0.5:
        sweep = sweep[::-1]
    field = np.zeros((time_s.size, frequency_ghz.size), dtype=float)
    temporal = _persistence_mask(time_s.size, config.persistence, rng)
    for idx, center in enumerate(sweep):
        field[idx] = _gaussian_band(frequency_ghz, center, config.bandwidth_mhz)
    return config.power_k * temporal[:, None] * field


def amplitude_modulated(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    center = _center_frequency(config, frequency_ghz)
    envelope = _gaussian_band(frequency_ghz, center, config.bandwidth_mhz)
    depth = np.clip(config.modulation_depth, 0.0, 1.0)
    modulation = 1.0 + depth * np.sin(2 * np.pi * config.modulation_frequency_hz * time_s + config.phase_rad)
    temporal = _persistence_mask(time_s.size, config.persistence, rng)
    noise = 1.0 + rng.normal(0.0, 0.03, size=time_s.size)
    return config.power_k * temporal[:, None] * modulation[:, None] * noise[:, None] * envelope[None, :]


def _center_frequency(config: RFIConfig, frequency_ghz: np.ndarray) -> float:
    return config.center_frequency_ghz if config.center_frequency_ghz is not None else float(frequency_ghz.mean())


def _bandwidth_ghz(bandwidth_mhz: float) -> float:
    return bandwidth_mhz / 1000.0


def _gaussian_band(frequency_ghz: np.ndarray, center_ghz: float, bandwidth_mhz: float) -> np.ndarray:
    sigma = max(_bandwidth_ghz(bandwidth_mhz) / 2.355, 1e-6)
    return np.exp(-0.5 * ((frequency_ghz - center_ghz) / sigma) ** 2)


def _raised_band(frequency_ghz: np.ndarray, center_ghz: float, bandwidth_mhz: float) -> np.ndarray:
    half_width = max(_bandwidth_ghz(bandwidth_mhz) / 2.0, 1e-6)
    distance = np.abs(frequency_ghz - center_ghz) / half_width
    return np.clip(0.5 * (1.0 + np.cos(np.pi * np.clip(distance, 0.0, 1.0))), 0.0, 1.0)


def _persistence_mask(size: int, persistence: float, rng: np.random.Generator) -> np.ndarray:
    if persistence >= 1.0:
        return np.ones(size)
    if persistence <= 0.0:
        return np.zeros(size)
    raw = rng.random(size) < persistence
    if size < 3:
        return raw.astype(float)
    smoothed = np.convolve(raw.astype(float), np.ones(3) / 3.0, mode="same")
    return (smoothed > 0.25).astype(float)


def _sample_rate(time_s: np.ndarray) -> float:
    if time_s.size < 2:
        return 1.0
    step = float(np.median(np.diff(time_s)))
    return 1.0 / step if step > 0 else 1.0
