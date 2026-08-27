"""Dataset generation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import numpy as np

from rfigen.config import ExperimentConfig
from rfigen.grid import make_direction_axes, make_frequency_axis, make_time_axis
from rfigen.mixer import mix_signals
from rfigen.models import generate_rfi
from rfigen.radiometry import simulate_clean_radiometry


@dataclass(slots=True)
class Dataset:
    time_s: np.ndarray
    frequency_ghz: np.ndarray
    clean: np.ndarray
    rfi: np.ndarray
    contaminated: np.ndarray
    metadata: dict
    azimuth_deg: np.ndarray | None = None
    elevation_deg: np.ndarray | None = None


def build_dataset(config: ExperimentConfig) -> Dataset:
    config.validate()
    rng = np.random.default_rng(config.seed)
    time_s = make_time_axis(config)
    frequency_ghz = make_frequency_axis(config)
    azimuth_deg, elevation_deg = make_direction_axes(config, time_s.size)

    clean = simulate_clean_radiometry(time_s, frequency_ghz, config.radiometry, rng, azimuth_deg, elevation_deg)
    rfi_signals = []
    for index, rfi_config in enumerate(config.rfi):
        model_seed = rfi_config.seed if rfi_config.seed is not None else int(rng.integers(0, 2**32 - 1))
        model_rng = np.random.default_rng(model_seed)
        rfi_signals.append(generate_rfi(rfi_config, time_s, frequency_ghz, model_rng))

    contaminated, rfi = mix_signals(clean, rfi_signals)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": config.seed,
        "duration_s": config.duration_s,
        "sample_rate_hz": config.sample_rate_hz,
        "frequency_start_ghz": float(frequency_ghz.min()),
        "frequency_stop_ghz": float(frequency_ghz.max()),
        "frequency_bins": int(frequency_ghz.size),
        "frequency_channels_ghz": [float(item) for item in frequency_ghz],
        "radiometry": asdict(config.radiometry),
        "scan_directions": config.scan_directions,
        "rfi": [asdict(item) for item in config.rfi],
        "shape": {
            "time": int(time_s.size),
            "frequency": int(frequency_ghz.size),
        },
    }
    return Dataset(time_s, frequency_ghz, clean, rfi, contaminated, metadata, azimuth_deg, elevation_deg)
