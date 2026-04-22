from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


DEFAULTS: Dict[str, Any] = {
    "project": {
        "name": "RFIGen",
        "version": "0.1.0",
    },
    "run": {
        "seed": 12345,
        "n_datasets": 5,
        "n_records_per_dataset": 1000,
    },
    "radiometry": {
        "use_rttov": False,
        "noise_std_k": 0.5,
    },
    "composition": {
        "inject_rfi": True,
    },
    "export": {
        "directory": "outputs/",
    },
    "interfaces": {
        "cli": {"enabled": True},
        "gui": {"enabled": False},
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


class ConfigValidationError(Exception):
    """Raised when config validation fails."""


def parse_and_validate_config(raw_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge defaults into a raw config and validate the result."""
    config = _deep_merge(deepcopy(DEFAULTS), raw_config)

    _validate_run(config.get("run", {}))
    _validate_radiometry(config.get("radiometry", {}))
    _validate_composition(config.get("composition", {}))
    _validate_export(config.get("export", {}))
    _validate_rfi_sources(config.get("rfi_sources", []))

    return config

def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def _validate_run(run_cfg: Dict[str, Any]) -> None:
    if not isinstance(run_cfg.get("seed"), int):
        raise ConfigValidationError("run.seed must be an integer.")
    if not isinstance(run_cfg.get("n_datasets"), int) or run_cfg.get("n_datasets", 0) <= 0:
        raise ConfigValidationError("run.n_datasets must be a positive integer.")
    if not isinstance(run_cfg.get("n_records_per_dataset"), int) or run_cfg.get("n_records_per_dataset", 0) <= 0:
        raise ConfigValidationError("run.n_records_per_dataset must be a positive integer.")

def _validate_radiometry(radio_cfg: Dict[str, Any]) -> None:
    if not isinstance(radio_cfg.get("use_rttov"), bool):
        raise ConfigValidationError("radiometry.use_rttov must be a boolean.")
    if not isinstance(radio_cfg.get("noise_std_k"), (int, float)) or radio_cfg.get("noise_std_k", 0) < 0:
        raise ConfigValidationError("radiometry.noise_std_k must be a non-negative number.")

def _validate_composition(comp_cfg: Dict[str, Any]) -> None:
    if not isinstance(comp_cfg.get("inject_rfi"), bool):
        raise ConfigValidationError("composition.inject_rfi must be a boolean.")

def _validate_export(export_cfg: Dict[str, Any]) -> None:
    if not isinstance(export_cfg.get("directory"), str) or not export_cfg.get("directory", "").strip():
        raise ConfigValidationError("export.directory must be a non-empty string.")

def _validate_rfi_sources(rfi_sources: List[Dict[str, Any]]) -> None:
    if not isinstance(rfi_sources, list):
        raise ConfigValidationError("rfi_sources must be a list.")

    for i, source in enumerate(rfi_sources):
        if not isinstance(source, dict):
            raise ConfigValidationError(f"rfi_sources[{i}] must be a dictionary.")

        if not isinstance(source.get("id"), str) or not source["id"].strip():
            raise ConfigValidationError(f"rfi_sources[{i}].id must be a non-empty string.")

        if source.get("type") not in ALLOWED_RFI_TYPES:
            raise ConfigValidationError(f"rfi_sources[{i}].type must be one of {sorted(ALLOWED_RFI_TYPES)}.")

        if not isinstance(source.get("enabled"), bool):
            raise ConfigValidationError(f"rfi_sources[{i}].enabled must be a boolean.")

        if not isinstance(source.get("center_offset_mhz"), (int, float)):
            raise ConfigValidationError(f"rfi_sources[{i}].center_offset_mhz must be a number.")

        if not isinstance(source.get("bandwidth_mhz"), (int, float)) or source["bandwidth_mhz"] <= 0:
            raise ConfigValidationError(f"rfi_sources[{i}].bandwidth_mhz must be a positive number.")

        if not isinstance(source.get("power_dbm"), (int, float)):
            raise ConfigValidationError(f"rfi_sources[{i}].power_dbm must be a number.")

        if not isinstance(source.get("persistence"), (int, float)) or not (0.0 <= source["persistence"] <= 1.0):
            raise ConfigValidationError(f"rfi_sources[{i}].persistence must be between 0 and 1.")

        if source.get("modulation") and source["modulation"] not in ALLOWED_MODULATION_TYPES:
            raise ConfigValidationError(f"rfi_sources[{i}].modulation must be one of {sorted(ALLOWED_MODULATION_TYPES)}.")

        rfi_type = source.get("type")
        if rfi_type == "pulsed":
            if not isinstance(source.get("duty_cycle"), (int, float)) or not (0 < source["duty_cycle"] <= 1.0):
                raise ConfigValidationError(f"rfi_sources[{i}].duty_cycle must be in range (0, 1].")
            if not isinstance(source.get("pulse_period_ms"), (int, float)) or source["pulse_period_ms"] <= 0:
                raise ConfigValidationError(f"rfi_sources[{i}].pulse_period_ms must be positive.")
        elif rfi_type == "bursty":
            if not isinstance(source.get("burst_rate_hz"), (int, float)) or source["burst_rate_hz"] <= 0:
                raise ConfigValidationError(f"rfi_sources[{i}].burst_rate_hz must be positive.")
            if not isinstance(source.get("burst_duration_ms"), (int, float)) or source["burst_duration_ms"] <= 0:
                raise ConfigValidationError(f"rfi_sources[{i}].burst_duration_ms must be positive.")



