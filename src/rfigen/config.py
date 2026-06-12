"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


K_BAND_MIN_ALLOWED_GHZ = 18.0
K_BAND_MAX_ALLOWED_GHZ = 30.0
DEFAULT_WORKING_START_GHZ = 20.0
DEFAULT_WORKING_STOP_GHZ = 30.0
DEFAULT_PROFILE_CHANNELS_GHZ = [
    22.000,
    22.234,
    22.500,
    23.000,
    23.034,
    23.500,
    23.834,
    24.000,
    24.500,
    25.000,
    25.500,
    26.000,
    26.234,
    26.500,
    27.000,
    27.500,
    28.000,
    28.500,
    29.000,
    29.500,
    30.000,
]


@dataclass(slots=True)
class RadiometryConfig:
    baseline_k: float = 95.0
    atmospheric_variation_k: float = 2.0
    receiver_noise_k: float = 0.65
    spectral_slope_k: float = -38.0
    zenith_scale: float = 0.42
    high_elevation_scale: float = 1.08
    profile_bump_k: float = 9.0
    spike_probability: float = 0.0
    spike_power_k: float = 35.0


@dataclass(slots=True)
class RFIConfig:
    type: str
    center_frequency_ghz: float | None = None
    start_frequency_ghz: float | None = None
    stop_frequency_ghz: float | None = None
    bandwidth_mhz: float = 20.0
    power_k: float = 10.0
    duty_cycle: float = 0.5
    pulse_period_s: float = 1.0
    persistence: float = 1.0
    modulation_frequency_hz: float = 0.2
    modulation_depth: float = 0.5
    phase_rad: float = 0.0
    seed: int | None = None


@dataclass(slots=True)
class ExportConfig:
    include_csv: bool = True
    include_npz: bool = True
    include_plots: bool = True


@dataclass(slots=True)
class ExperimentConfig:
    seed: int = 1234
    duration_s: float = 60.0
    sample_rate_hz: float = 2.0
    frequency_start_ghz: float = DEFAULT_WORKING_START_GHZ
    frequency_stop_ghz: float = DEFAULT_WORKING_STOP_GHZ
    frequency_bins: int = 21
    frequency_channels_ghz: list[float] | None = None
    scan_directions: list[dict[str, float]] = field(
        default_factory=lambda: [
            {"azimuth_deg": 0.0, "elevation_deg": 19.8},
            {"azimuth_deg": 0.0, "elevation_deg": 90.0},
            {"azimuth_deg": 0.0, "elevation_deg": 160.2},
            {"azimuth_deg": 45.0, "elevation_deg": 19.8},
            {"azimuth_deg": 45.0, "elevation_deg": 160.2},
            {"azimuth_deg": 90.0, "elevation_deg": 19.8},
            {"azimuth_deg": 90.0, "elevation_deg": 160.2},
            {"azimuth_deg": 135.0, "elevation_deg": 19.8},
            {"azimuth_deg": 135.0, "elevation_deg": 160.2},
        ]
    )
    radiometry: RadiometryConfig = field(default_factory=RadiometryConfig)
    rfi: list[RFIConfig] = field(default_factory=list)
    export: ExportConfig = field(default_factory=ExportConfig)

    def validate(self) -> None:
        if self.duration_s <= 0:
            raise ValueError("duration_s must be positive")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.frequency_channels_ghz is not None and len(self.frequency_channels_ghz) < 2:
            raise ValueError("frequency_channels_ghz must contain at least 2 channels")
        if self.frequency_channels_ghz is None and self.frequency_bins < 2:
            raise ValueError("frequency_bins must be at least 2")
        if self.frequency_channels_ghz is not None:
            self.frequency_start_ghz = min(self.frequency_channels_ghz)
            self.frequency_stop_ghz = max(self.frequency_channels_ghz)
            self.frequency_bins = len(self.frequency_channels_ghz)
        if self.frequency_start_ghz < K_BAND_MIN_ALLOWED_GHZ:
            raise ValueError("frequency_start_ghz must be within or above the supported K-band start")
        if self.frequency_stop_ghz > K_BAND_MAX_ALLOWED_GHZ:
            raise ValueError("frequency_stop_ghz must be within or below the supported upper K-band channel")
        if self.frequency_start_ghz >= self.frequency_stop_ghz:
            raise ValueError("frequency_start_ghz must be below frequency_stop_ghz")
        if not self.scan_directions:
            raise ValueError("scan_directions must contain at least one direction")
        for item in self.rfi:
            validate_rfi_config(item, self.frequency_start_ghz, self.frequency_stop_ghz)


def validate_rfi_config(config: RFIConfig, start_ghz: float, stop_ghz: float) -> None:
    if config.type not in {"narrowband", "broadband", "pulsed", "bursty", "chirp", "am"}:
        raise ValueError(f"unsupported RFI type: {config.type}")
    if config.bandwidth_mhz <= 0:
        raise ValueError("bandwidth_mhz must be positive")
    if config.power_k < 0:
        raise ValueError("power_k must be non-negative")
    if not 0 <= config.duty_cycle <= 1:
        raise ValueError("duty_cycle must be between 0 and 1")
    if not 0 <= config.persistence <= 1:
        raise ValueError("persistence must be between 0 and 1")
    if config.pulse_period_s <= 0:
        raise ValueError("pulse_period_s must be positive")

    frequencies = [
        value
        for value in (
            config.center_frequency_ghz,
            config.start_frequency_ghz,
            config.stop_frequency_ghz,
        )
        if value is not None
    ]
    for frequency in frequencies:
        if frequency < start_ghz or frequency > stop_ghz:
            raise ValueError(f"RFI frequency {frequency} GHz is outside configured band")


def load_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    data = _load_mapping(path)
    config = config_from_mapping(data)
    config.validate()
    return config


def config_from_mapping(data: dict[str, Any]) -> ExperimentConfig:
    radiometry = RadiometryConfig(**data.get("radiometry", {}))
    export = ExportConfig(**data.get("export", {}))
    rfi = [RFIConfig(**item) for item in data.get("rfi", [])]

    top_level = {
        key: value
        for key, value in data.items()
        if key not in {"radiometry", "rfi", "export"}
    }
    return ExperimentConfig(**top_level, radiometry=radiometry, rfi=rfi, export=export)


def _load_mapping(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml
            except ImportError as exc:
                raise RuntimeError("PyYAML is required to read YAML configs") from exc
            data = yaml.safe_load(handle)
        else:
            data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("configuration file must contain a mapping/object")
    return data
