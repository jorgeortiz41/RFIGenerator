# signal_mixer.py
# ============================================================
# Signal Composition Module
# ------------------------------------------------------------
# This module combines clean radiometric data with synthetic RFI.
#
# Input:
#   - clean radiometric DataFrame
#   - validated configuration dictionary
#
# Output:
#   - contaminated DataFrame
#   - metadata describing the injected RFI
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class MixerResult:
    """Container for the signal mixer output."""

    clean_df: pd.DataFrame
    contaminated_df: pd.DataFrame
    rfi_matrix: np.ndarray
    channel_cols: list[str]
    channel_freqs_ghz: np.ndarray
    metadata: dict[str, Any]


# ============================================================
# CHANNEL DETECTION
# ============================================================

def find_frequency_channels(
    df: pd.DataFrame,
    fmin_ghz: float = 22.0,
    fmax_ghz: float = 30.0,
) -> tuple[list[str], np.ndarray]:
    """
    Find radiometer frequency columns in a DataFrame.

    Supports columns like:
        "22.000"
        "22.234"
        "Ch  22.000"

    Returns
    -------
    channel_cols:
        Column names that correspond to frequency channels.
    channel_freqs_ghz:
        Frequencies as float values in GHz.
    """

    channel_cols: list[str] = []
    channel_freqs: list[float] = []

    for col in df.columns:
        name = str(col).strip()

        # Ignore known non-frequency columns
        if name in {"Date/Time", "Az(deg)", "El(deg)", "TkBB(K)", "Record"}:
            continue

        # Handle "Ch  22.000"
        if name.lower().startswith("ch"):
            parts = name.split()
            if len(parts) >= 2:
                candidate = parts[-1]
            else:
                continue
        else:
            candidate = name

        try:
            freq = float(candidate)
        except ValueError:
            continue

        if fmin_ghz <= freq <= fmax_ghz:
            channel_cols.append(col)
            channel_freqs.append(freq)

    if not channel_cols:
        raise ValueError(
            f"No frequency channels were found in the range {fmin_ghz}-{fmax_ghz} GHz."
        )

    # Sort channels by frequency
    order = np.argsort(np.array(channel_freqs, dtype=float))
    sorted_cols = [channel_cols[i] for i in order]
    sorted_freqs = np.array([channel_freqs[i] for i in order], dtype=float)

    return sorted_cols, sorted_freqs


# ============================================================
# TIME STEP ESTIMATION
# ============================================================

def estimate_dt_seconds(df: pd.DataFrame) -> float:
    """
    Estimate the median time step in seconds using the Date/Time column.
    If Date/Time is missing or invalid, return 1 second.
    """

    if "Date/Time" not in df.columns:
        return 1.0

    try:
        t = pd.to_datetime(df["Date/Time"], errors="coerce")
        t = t[t.notna()]

        if len(t) < 2:
            return 1.0

        dt = t.diff().dt.total_seconds().dropna()
        if len(dt) == 0:
            return 1.0

        median_dt = float(dt.median())
        if not np.isfinite(median_dt) or median_dt <= 0:
            return 1.0

        return median_dt

    except Exception:
        return 1.0


# ============================================================
# RFI FREQUENCY MODEL
# ============================================================

def build_frequency_shape(
    freqs_ghz: np.ndarray,
    center_ghz: float,
    bandwidth_ghz: float,
    rfi_type: str,
) -> np.ndarray:
    """
    Build the RFI spectral shape across frequency channels.

    This is the frequency-domain part of the RFI model.
    """

    freqs = np.asarray(freqs_ghz, dtype=float)
    bandwidth_ghz = max(float(bandwidth_ghz), 1e-6)

    x = (freqs - center_ghz) / (bandwidth_ghz / 2.0)

    if rfi_type == "narrowband":
        shape = np.exp(-0.5 * (x / 0.45) ** 2)

    elif rfi_type == "broadband":
        shape = np.where(np.abs(x) <= 1.0, 1.0, 0.10 * np.exp(-np.abs(x)))

    elif rfi_type == "pulsed":
        shape = np.exp(-0.5 * (x / 0.60) ** 2)

    elif rfi_type == "bursty":
        shape = np.exp(-0.5 * (x / 0.80) ** 2)

    elif rfi_type == "time_varying_frequency":
        shape = np.exp(-0.5 * (x / 0.70) ** 2)

    elif rfi_type == "amplitude_modulated":
        shape = np.exp(-0.5 * (x / 0.75) ** 2)

    else:
        shape = np.exp(-0.5 * x**2)

    max_value = np.nanmax(shape)

    if max_value <= 0 or not np.isfinite(max_value):
        return np.zeros_like(freqs)

    return shape / max_value


# ============================================================
# RFI TEMPORAL MODEL
# ============================================================

def build_time_envelope(
    n_time: int,
    dt_seconds: float,
    source_cfg: dict[str, Any],
    amplitude_k: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Build the time-domain RFI envelope.

    The envelope controls when the RFI is active and how strong it is in time.
    """

    rfi_type = str(source_cfg.get("type", "narrowband"))
    persistence = float(source_cfg.get("persistence", 1.0))
    persistence = float(np.clip(persistence, 0.0, 1.0))

    envelope = np.zeros(n_time, dtype=float)

    if n_time <= 0:
        return envelope

    # --------------------------------------------------------
    # Continuous / narrowband / broadband
    # --------------------------------------------------------
    if rfi_type in {"narrowband", "broadband", "amplitude_modulated", "time_varying_frequency"}:
        active = rng.random(n_time) < persistence
        envelope[active] = amplitude_k

        if rfi_type == "amplitude_modulated":
            t = np.arange(n_time) * dt_seconds
            modulation = 1.0 + 0.35 * np.sin(2.0 * np.pi * 2.0 * t)
            envelope *= modulation

    # --------------------------------------------------------
    # Pulsed RFI
    # --------------------------------------------------------
    elif rfi_type == "pulsed":
        duty_cycle = float(source_cfg.get("duty_cycle", 0.10))
        duty_cycle = float(np.clip(duty_cycle, 0.001, 1.0))

        pulse_period_ms = float(source_cfg.get("pulse_period_ms", 10.0))
        pulse_period_s = max(pulse_period_ms / 1000.0, dt_seconds)

        period_samples = max(1, int(round(pulse_period_s / dt_seconds)))
        pulse_samples = max(1, int(round(duty_cycle * period_samples)))

        for start in range(0, n_time, period_samples):
            if rng.random() <= persistence:
                end = min(start + pulse_samples, n_time)
                envelope[start:end] = amplitude_k

    # --------------------------------------------------------
    # Bursty RFI
    # --------------------------------------------------------
    elif rfi_type == "bursty":
        burst_rate_hz = float(source_cfg.get("burst_rate_hz", 2.0))
        burst_duration_ms = float(source_cfg.get("burst_duration_ms", 5.0))

        burst_duration_s = max(burst_duration_ms / 1000.0, dt_seconds)
        burst_samples = max(1, int(round(burst_duration_s / dt_seconds)))

        total_duration_s = max(n_time * dt_seconds, dt_seconds)
        expected_bursts = max(1, int(round(burst_rate_hz * total_duration_s)))

        for _ in range(expected_bursts):
            if rng.random() > persistence:
                continue

            start = int(rng.integers(0, n_time))
            end = min(start + burst_samples, n_time)
            envelope[start:end] = amplitude_k

    else:
        active = rng.random(n_time) < persistence
        envelope[active] = amplitude_k

    # Small random variation so the envelope is not perfectly flat
    active_mask = envelope > 0
    if np.any(active_mask):
        fluctuation = rng.normal(loc=1.0, scale=0.08, size=np.sum(active_mask))
        envelope[active_mask] *= np.clip(fluctuation, 0.70, 1.30)

    return envelope


# ============================================================
# AMPLITUDE SCALING
# ============================================================

def estimate_rfi_amplitude_k(
    clean_values: np.ndarray,
    source_cfg: dict[str, Any],
    composition_cfg: dict[str, Any],
) -> float:
    """
    Estimate RFI amplitude in Kelvin.

    This first version uses the target SNR from the config and a simple
    relative scaling from power_dbm.

    It is not a hardware-calibrated dBm-to-K conversion.
    It is a controllable synthetic scaling for dataset generation.
    """

    snr_db = float(composition_cfg.get("snr_db", 18.0))
    power_dbm = float(source_cfg.get("power_dbm", -70.0))

    clean_std = float(np.nanstd(clean_values))

    if not np.isfinite(clean_std) or clean_std <= 0:
        clean_std = 1.0

    # Convert SNR from dB to amplitude ratio
    snr_ratio = 10.0 ** (snr_db / 20.0)

    # Relative power factor around -80 dBm reference
    power_factor = 10.0 ** ((power_dbm + 80.0) / 20.0)
    power_factor = float(np.clip(power_factor, 0.25, 10.0))

    amplitude_k = clean_std * snr_ratio * power_factor

    # Keep the first version numerically stable
    amplitude_k = float(np.clip(amplitude_k, 0.1, 500.0))

    return amplitude_k


# ============================================================
# MAIN MIXER FUNCTION
# ============================================================

def mix_clean_with_rfi(
    clean_df: pd.DataFrame,
    config: dict[str, Any],
    channel_cols: list[str] | None = None,
    channel_freqs_ghz: np.ndarray | None = None,
    seed: int | None = None,
) -> MixerResult:
    """
    Combine clean radiometric data with synthetic RFI.

    Parameters
    ----------
    clean_df:
        Clean radiometric data.
    config:
        Validated configuration dictionary.
    channel_cols:
        Optional list of frequency channel columns.
    channel_freqs_ghz:
        Optional frequency array in GHz.
    seed:
        Optional seed. If None, uses config["run"]["seed"].

    Returns
    -------
    MixerResult
        Contains clean data, contaminated data, RFI matrix, channels, frequencies, and metadata.
    """

    if clean_df.empty:
        raise ValueError("clean_df is empty.")

    run_cfg = config.get("run", {})
    freq_cfg = config.get("frequency", {})
    composition_cfg = config.get("composition", {})
    rfi_sources = config.get("rfi_sources", [])

    if seed is None:
        seed = int(run_cfg.get("seed", 12345))

    rng = np.random.default_rng(seed)

    fmin_ghz = float(freq_cfg.get("band", {}).get("min_ghz", 22.0))
    fmax_ghz = float(freq_cfg.get("band", {}).get("max_ghz", 30.0))
    center_ghz = float(freq_cfg.get("center_ghz", 22.235))

    if channel_cols is None or channel_freqs_ghz is None:
        channel_cols, channel_freqs_ghz = find_frequency_channels(
            clean_df,
            fmin_ghz=fmin_ghz,
            fmax_ghz=fmax_ghz,
        )

    channel_freqs_ghz = np.asarray(channel_freqs_ghz, dtype=float)

    clean_values = clean_df[channel_cols].to_numpy(dtype=float)
    contaminated_values = clean_values.copy()

    n_time, n_freq = clean_values.shape
    rfi_total = np.zeros((n_time, n_freq), dtype=float)

    dt_seconds = estimate_dt_seconds(clean_df)

    metadata: dict[str, Any] = {
        "seed": seed,
        "dt_seconds": dt_seconds,
        "n_time": n_time,
        "n_freq": n_freq,
        "frequency_min_ghz": float(np.nanmin(channel_freqs_ghz)),
        "frequency_max_ghz": float(np.nanmax(channel_freqs_ghz)),
        "inject_rfi": bool(composition_cfg.get("inject_rfi", True)),
        "sources": [],
    }

    if not composition_cfg.get("inject_rfi", True):
        contaminated_df = clean_df.copy()
        return MixerResult(
            clean_df=clean_df.copy(),
            contaminated_df=contaminated_df,
            rfi_matrix=rfi_total,
            channel_cols=channel_cols,
            channel_freqs_ghz=channel_freqs_ghz,
            metadata=metadata,
        )

    enabled_sources = [
        source for source in rfi_sources
        if bool(source.get("enabled", True))
    ]

    for source_cfg in enabled_sources:
        source_id = str(source_cfg.get("id", "unnamed_source"))
        rfi_type = str(source_cfg.get("type", "narrowband"))

        center_offset_mhz = float(source_cfg.get("center_offset_mhz", 0.0))
        bandwidth_mhz = float(source_cfg.get("bandwidth_mhz", 1.0))

        source_center_ghz = center_ghz + center_offset_mhz / 1000.0
        source_bandwidth_ghz = max(bandwidth_mhz / 1000.0, 1e-6)

        amplitude_k = estimate_rfi_amplitude_k(
            clean_values=clean_values,
            source_cfg=source_cfg,
            composition_cfg=composition_cfg,
        )

        freq_shape = build_frequency_shape(
            freqs_ghz=channel_freqs_ghz,
            center_ghz=source_center_ghz,
            bandwidth_ghz=source_bandwidth_ghz,
            rfi_type=rfi_type,
        )

        time_env = build_time_envelope(
            n_time=n_time,
            dt_seconds=dt_seconds,
            source_cfg=source_cfg,
            amplitude_k=amplitude_k,
            rng=rng,
        )

        source_rfi = time_env[:, None] * freq_shape[None, :]

        # Spectral overlap policy
        overlap_policy = str(composition_cfg.get("spectral_overlap_policy", "add_power"))

        if overlap_policy == "add_power":
            rfi_total += source_rfi

        elif overlap_policy == "overwrite":
            rfi_total = np.where(source_rfi > 0, source_rfi, rfi_total)

        elif overlap_policy == "clip":
            rfi_total += source_rfi
            rfi_total = np.clip(rfi_total, 0.0, 500.0)

        else:
            rfi_total += source_rfi

        metadata["sources"].append(
            {
                "id": source_id,
                "type": rfi_type,
                "center_ghz": source_center_ghz,
                "bandwidth_ghz": source_bandwidth_ghz,
                "center_offset_mhz": center_offset_mhz,
                "bandwidth_mhz": bandwidth_mhz,
                "power_dbm": float(source_cfg.get("power_dbm", -70.0)),
                "persistence": float(source_cfg.get("persistence", 1.0)),
                "amplitude_k_estimate": amplitude_k,
                "max_rfi_k": float(np.nanmax(source_rfi)),
                "mean_rfi_k": float(np.nanmean(source_rfi)),
                "active_fraction": float(np.mean(time_env > 0)),
            }
        )

    contaminated_values = clean_values + rfi_total

    if bool(composition_cfg.get("normalize_output", False)):
        contaminated_values = np.nan_to_num(contaminated_values, nan=0.0)

    contaminated_df = clean_df.copy()
    contaminated_df.loc[:, channel_cols] = contaminated_values

    metadata["total_rfi"] = {
        "max_rfi_k": float(np.nanmax(rfi_total)),
        "mean_rfi_k": float(np.nanmean(rfi_total)),
        "active_fraction": float(np.mean(rfi_total > 0)),
        "source_count": len(enabled_sources),
    }

    return MixerResult(
        clean_df=clean_df.copy(),
        contaminated_df=contaminated_df,
        rfi_matrix=rfi_total,
        channel_cols=channel_cols,
        channel_freqs_ghz=channel_freqs_ghz,
        metadata=metadata,
    )