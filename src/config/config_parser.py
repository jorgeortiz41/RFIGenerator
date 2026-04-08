from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


DEFAULTS: Dict[str, Any] = {
    "project": {
        "name": "RFIGen",
        "version": "0.1.0",
        "profile": "default",
    },
    "run": {
        "seed": 12345,
        "n_samples": 4096,
        "sample_rate_hz": 1_000_000,
        "duration_s": 0.004096,
        "output_prefix": "run_001",
    },
    "frequency": {
        "band": {
            "min_ghz": 18.0,
            "max_ghz": 27.0,
        },
        "center_ghz": 22.235,
        "span_mhz": 200.0,
    },
    "radiometry": {
        "baseline_type": "atmospheric_brightness",
        "mean_tb_k": 180.0,
        "variability_tb_k": 4.5,
        "instrument_noise_std_k": 0.35,
        "drift_per_second_k": 0.05,
    },
    "composition": {
        "inject_rfi": True,
        "contamination_target": "both",
        "amplitude_scaling_mode": "linear",
        "spectral_overlap_policy": "add_power",
        "domain_match": "frequency",
        "snr_db": 18.0,
        "normalize_output": True,
    },
    "dataset": {
        "dataset_name": "kband_synthetic_demo",
        "records": 100,
        "save_clean": True,
        "save_contaminated": True,
        "save_metadata": True,
    },
    "export": {
        "directory": "outputs/",
        "formats": {
            "csv": True,
            "json_metadata": True,
            "mp3000a_style": False,
            "npy": True,
        },
        "overwrite": False,
    },
    "visualization": {
        "enabled": True,
        "save_figures": True,
        "figure_directory": "outputs/figures/",
        "products": {
            "time_domain": True,
            "frequency_spectrum": True,
            "spectrogram": True,
        },
    },
    "interfaces": {
        "cli": {
            "enabled": True,
            "allow_parameter_overrides": True,
        },
        "gui": {
            "enabled": False,
            "realtime_preview": False,
        },
    },
    "validation": {
        "enforce_k_band_limits": True,
        "require_physical_plausibility": True,
        "fail_on_invalid_ranges": True,
    },
    "rfi_sources": [],
}

ALLOWED_RFI_TYPES = {
    "narrowband",
    "broadband",
    "pulsed",
    "bursty",
    "time_varying_frequency",
    "amplitude_modulated",
}

ALLOWED_MODULATION_TYPES = {"none", "amplitude", "frequency", "phase"}

ALLOWED_CONTAMINATION_TARGETS = {"both", "clean_only", "contaminated_only"}
ALLOWED_SCALING_MODES = {"linear", "db"}
ALLOWED_DOMAIN_MATCH = {"time", "frequency", "time_frequency"}
ALLOWED_OVERLAP_POLICIES = {"add_power", "overwrite", "clip"}


class ConfigValidationError(Exception):
    """Raised when config validation fails."""


def parse_and_validate_config(raw_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge defaults into a raw config and validate the result."""
    config = _deep_merge(deepcopy(DEFAULTS), raw_config)

    _require_sections(
        config,
        required=["project", "run", "frequency", "radiometry", "composition", "dataset", "export"],
    )

    _validate_run(config["run"])
    _validate_frequency(config["frequency"], enforce_k_band=config["validation"]["enforce_k_band_limits"])
    _validate_radiometry(config["radiometry"])
    _validate_composition(config["composition"])
    _validate_dataset(config["dataset"])
    _validate_export(config["export"])
    _validate_visualization(config["visualization"])
    _validate_interfaces(config["interfaces"])
    _validate_rfi_sources(config["rfi_sources"], config["frequency"])

    _check_duration_consistency(config["run"])

    return config


def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _require_sections(config: Dict[str, Any], required: List[str]) -> None:
    missing = [name for name in required if name not in config]
    if missing:
        raise ConfigValidationError(f"Missing required config sections: {', '.join(missing)}")


def _validate_run(run_cfg: Dict[str, Any]) -> None:
    _require_positive_int(run_cfg, "seed", allow_zero=True)
    _require_positive_int(run_cfg, "n_samples")
    _require_positive_number(run_cfg, "sample_rate_hz")
    _require_positive_number(run_cfg, "duration_s")

    if not isinstance(run_cfg.get("output_prefix"), str) or not run_cfg["output_prefix"].strip():
        raise ConfigValidationError("run.output_prefix must be a non-empty string.")


def _validate_frequency(freq_cfg: Dict[str, Any], enforce_k_band: bool) -> None:
    if "band" not in freq_cfg or not isinstance(freq_cfg["band"], dict):
        raise ConfigValidationError("frequency.band must exist and be a dictionary.")

    band = freq_cfg["band"]
    _require_number(band, "min_ghz")
    _require_number(band, "max_ghz")
    _require_number(freq_cfg, "center_ghz")
    _require_positive_number(freq_cfg, "span_mhz")

    min_ghz = band["min_ghz"]
    max_ghz = band["max_ghz"]
    center_ghz = freq_cfg["center_ghz"]

    if min_ghz >= max_ghz:
        raise ConfigValidationError("frequency.band.min_ghz must be less than frequency.band.max_ghz.")

    if not (min_ghz <= center_ghz <= max_ghz):
        raise ConfigValidationError("frequency.center_ghz must fall within frequency.band limits.")

    if enforce_k_band and (min_ghz < 22.0 or max_ghz > 30.0):
        raise ConfigValidationError("Frequency band must remain within MP3000A K-band limits (22-30 GHz).")


def _validate_radiometry(radio_cfg: Dict[str, Any]) -> None:
    if not isinstance(radio_cfg.get("baseline_type"), str) or not radio_cfg["baseline_type"].strip():
        raise ConfigValidationError("radiometry.baseline_type must be a non-empty string.")

    for field in ("mean_tb_k", "variability_tb_k", "instrument_noise_std_k", "drift_per_second_k"):
        _require_number(radio_cfg, field)

    if radio_cfg["instrument_noise_std_k"] < 0:
        raise ConfigValidationError("radiometry.instrument_noise_std_k must be >= 0.")
    if radio_cfg["variability_tb_k"] < 0:
        raise ConfigValidationError("radiometry.variability_tb_k must be >= 0.")


def _validate_composition(comp_cfg: Dict[str, Any]) -> None:
    _require_boolean(comp_cfg, "inject_rfi")
    _require_boolean(comp_cfg, "normalize_output")
    _require_number(comp_cfg, "snr_db")

    if comp_cfg["contamination_target"] not in ALLOWED_CONTAMINATION_TARGETS:
        raise ConfigValidationError(
            f"composition.contamination_target must be one of {sorted(ALLOWED_CONTAMINATION_TARGETS)}."
        )
    if comp_cfg["amplitude_scaling_mode"] not in ALLOWED_SCALING_MODES:
        raise ConfigValidationError(
            f"composition.amplitude_scaling_mode must be one of {sorted(ALLOWED_SCALING_MODES)}."
        )
    if comp_cfg["domain_match"] not in ALLOWED_DOMAIN_MATCH:
        raise ConfigValidationError(
            f"composition.domain_match must be one of {sorted(ALLOWED_DOMAIN_MATCH)}."
        )
    if comp_cfg["spectral_overlap_policy"] not in ALLOWED_OVERLAP_POLICIES:
        raise ConfigValidationError(
            f"composition.spectral_overlap_policy must be one of {sorted(ALLOWED_OVERLAP_POLICIES)}."
        )


def _validate_dataset(dataset_cfg: Dict[str, Any]) -> None:
    if not isinstance(dataset_cfg.get("dataset_name"), str) or not dataset_cfg["dataset_name"].strip():
        raise ConfigValidationError("dataset.dataset_name must be a non-empty string.")

    _require_positive_int(dataset_cfg, "records")
    for field in ("save_clean", "save_contaminated", "save_metadata"):
        _require_boolean(dataset_cfg, field)

    if "split" in dataset_cfg:
        split_cfg = dataset_cfg["split"]
        if not isinstance(split_cfg, dict):
            raise ConfigValidationError("dataset.split must be a dictionary.")
        expected_keys = {"train", "validation", "test"}
        if set(split_cfg.keys()) != expected_keys:
            raise ConfigValidationError("dataset.split must contain exactly: train, validation, test.")
        total = 0.0
        for key in expected_keys:
            _require_number(split_cfg, key)
            if split_cfg[key] < 0:
                raise ConfigValidationError(f"dataset.split.{key} must be >= 0.")
            total += split_cfg[key]
        if abs(total - 1.0) > 1e-6:
            raise ConfigValidationError("dataset.split values must sum to 1.0.")


def _validate_export(export_cfg: Dict[str, Any]) -> None:
    if not isinstance(export_cfg.get("directory"), str) or not export_cfg["directory"].strip():
        raise ConfigValidationError("export.directory must be a non-empty string.")
    _require_boolean(export_cfg, "overwrite")

    formats = export_cfg.get("formats")
    if not isinstance(formats, dict):
        raise ConfigValidationError("export.formats must be a dictionary.")

    for key in ("csv", "json_metadata", "mp3000a_style", "npy"):
        _require_boolean(formats, key)


def _validate_visualization(viz_cfg: Dict[str, Any]) -> None:
    _require_boolean(viz_cfg, "enabled")
    _require_boolean(viz_cfg, "save_figures")

    if "figure_directory" in viz_cfg and not isinstance(viz_cfg["figure_directory"], str):
        raise ConfigValidationError("visualization.figure_directory must be a string.")

    products = viz_cfg.get("products")
    if not isinstance(products, dict):
        raise ConfigValidationError("visualization.products must be a dictionary.")

    for key in ("time_domain", "frequency_spectrum", "spectrogram"):
        _require_boolean(products, key)


def _validate_interfaces(interface_cfg: Dict[str, Any]) -> None:
    for top_key, nested_key in (("cli", "enabled"), ("gui", "enabled")):
        if top_key not in interface_cfg or not isinstance(interface_cfg[top_key], dict):
            raise ConfigValidationError(f"interfaces.{top_key} must be a dictionary.")
        _require_boolean(interface_cfg[top_key], nested_key)

    _require_boolean(interface_cfg["cli"], "allow_parameter_overrides")
    _require_boolean(interface_cfg["gui"], "realtime_preview")


def _validate_rfi_sources(rfi_sources: List[Dict[str, Any]], freq_cfg: Dict[str, Any]) -> None:
    if not isinstance(rfi_sources, list):
        raise ConfigValidationError("rfi_sources must be a list.")

    center_ghz = freq_cfg["center_ghz"]
    band_min = freq_cfg["band"]["min_ghz"]
    band_max = freq_cfg["band"]["max_ghz"]

    for i, source in enumerate(rfi_sources):
        if not isinstance(source, dict):
            raise ConfigValidationError(f"rfi_sources[{i}] must be a dictionary.")

        if not isinstance(source.get("id"), str) or not source["id"].strip():
            raise ConfigValidationError(f"rfi_sources[{i}].id must be a non-empty string.")

        if source.get("type") not in ALLOWED_RFI_TYPES:
            raise ConfigValidationError(
                f"rfi_sources[{i}].type must be one of {sorted(ALLOWED_RFI_TYPES)}."
            )

        _require_boolean(source, "enabled")
        _require_number(source, "center_offset_mhz")
        _require_positive_number(source, "bandwidth_mhz")
        _require_number(source, "power_dbm")
        _require_number(source, "persistence")

        if not (0.0 <= source["persistence"] <= 1.0):
            raise ConfigValidationError(f"rfi_sources[{i}].persistence must be between 0 and 1.")

        modulation = source.get("modulation", "none")
        if modulation not in ALLOWED_MODULATION_TYPES:
            raise ConfigValidationError(
                f"rfi_sources[{i}].modulation must be one of {sorted(ALLOWED_MODULATION_TYPES)}."
            )

        absolute_center_ghz = center_ghz + source["center_offset_mhz"] / 1000.0
        if not (band_min <= absolute_center_ghz <= band_max):
            raise ConfigValidationError(
                f"rfi_sources[{i}] center frequency falls outside the configured band."
            )

        rfi_type = source["type"]
        if rfi_type == "pulsed":
            _require_fraction_or_percent(source, "duty_cycle", i)
            _require_positive_number(source, "pulse_period_ms")
        elif rfi_type == "bursty":
            _require_positive_number(source, "burst_rate_hz")
            _require_positive_number(source, "burst_duration_ms")


def _check_duration_consistency(run_cfg: Dict[str, Any]) -> None:
    expected_duration = run_cfg["n_samples"] / run_cfg["sample_rate_hz"]
    actual_duration = run_cfg["duration_s"]

    if abs(expected_duration - actual_duration) > 1e-9:
        raise ConfigValidationError(
            "run.duration_s is inconsistent with run.n_samples / run.sample_rate_hz. "
            f"Expected {expected_duration}, got {actual_duration}."
        )


def _require_number(cfg: Dict[str, Any], key: str) -> None:
    if key not in cfg or not isinstance(cfg[key], (int, float)) or isinstance(cfg[key], bool):
        raise ConfigValidationError(f"{key} must be a number.")


def _require_positive_number(cfg: Dict[str, Any], key: str) -> None:
    _require_number(cfg, key)
    if cfg[key] <= 0:
        raise ConfigValidationError(f"{key} must be > 0.")


def _require_positive_int(cfg: Dict[str, Any], key: str, allow_zero: bool = False) -> None:
    if key not in cfg or not isinstance(cfg[key], int) or isinstance(cfg[key], bool):
        raise ConfigValidationError(f"{key} must be an integer.")
    if allow_zero:
        if cfg[key] < 0:
            raise ConfigValidationError(f"{key} must be >= 0.")
    else:
        if cfg[key] <= 0:
            raise ConfigValidationError(f"{key} must be > 0.")


def _require_boolean(cfg: Dict[str, Any], key: str) -> None:
    if key not in cfg or not isinstance(cfg[key], bool):
        raise ConfigValidationError(f"{key} must be a boolean.")


def _require_fraction_or_percent(source: Dict[str, Any], key: str, index: int) -> None:
    _require_number(source, key)
    if not (0.0 < source[key] <= 1.0):
        raise ConfigValidationError(f"rfi_sources[{index}].{key} must be in the range (0, 1].")
