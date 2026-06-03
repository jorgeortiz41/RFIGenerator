# dataset_builder.py
# ============================================================
# Dataset Generator Engine
# ------------------------------------------------------------
# Builds reproducible clean and contaminated radiometric datasets
# using the configuration file, signal mixer, and export module.
# ============================================================

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.mixer.signal_mixer import MixerResult, mix_clean_with_rfi
from src.export.export_data import export_mixer_result


MP3000_KBAND_CHANNELS_GHZ = [
    22.000, 22.234, 22.500, 23.000, 23.034, 23.500,
    23.834, 24.000, 24.500, 25.000, 25.500,
    26.000, 26.234, 26.500, 27.000, 27.500,
    28.000, 28.500, 29.000, 29.500, 30.000
]


def get_kband_channels_from_config(config: dict[str, Any]) -> list[float]:
    """
    Select MP-3000A-like K-band channels using the frequency limits from config.
    """

    freq_cfg = config.get("frequency", {})
    band_cfg = freq_cfg.get("band", {})

    fmin = float(band_cfg.get("min_ghz", 22.0))
    fmax = float(band_cfg.get("max_ghz", 30.0))

    return [
        freq for freq in MP3000_KBAND_CHANNELS_GHZ
        if fmin <= freq <= fmax
    ]


def generate_clean_radiometric_record(
    config: dict[str, Any],
    record_id: int,
    seed: int,
) -> pd.DataFrame:
    """
    Generate one clean synthetic radiometric record.

    This is a simplified radiometric baseline generator.
    Later, this can be replaced or connected with the more detailed
    radiometry.py / RTTOV-like generator.
    """

    run_cfg = config.get("run", {})
    radio_cfg = config.get("radiometry", {})

    n_samples = int(run_cfg.get("n_samples", 4096))
    sample_rate_hz = float(run_cfg.get("sample_rate_hz", 1_000_000))
    duration_s = float(run_cfg.get("duration_s", n_samples / sample_rate_hz))

    mean_tb_k = float(radio_cfg.get("mean_tb_k", 180.0))
    variability_tb_k = float(radio_cfg.get("variability_tb_k", 4.5))
    instrument_noise_std_k = float(radio_cfg.get("instrument_noise_std_k", 0.35))
    drift_per_second_k = float(radio_cfg.get("drift_per_second_k", 0.05))

    rng = np.random.default_rng(seed)

    channels = get_kband_channels_from_config(config)

    if not channels:
        raise ValueError("No K-band channels selected from config frequency limits.")

    dt_seconds = duration_s / max(n_samples, 1)

    start_time = pd.Timestamp("2026-01-01 00:00:00") + pd.to_timedelta(record_id, unit="h")
    time_offsets = pd.to_timedelta(np.arange(n_samples) * dt_seconds, unit="s")

    df = pd.DataFrame({
        "record_id": record_id,
        "Date/Time": start_time + time_offsets,
        "Az(deg)": np.zeros(n_samples),
        "El(deg)": np.ones(n_samples) * 90.0,
    })

    t = np.arange(n_samples) * dt_seconds

    # Slow temporal variation
    temporal_variation = variability_tb_k * 0.20 * np.sin(
        2.0 * np.pi * t / max(duration_s, dt_seconds)
    )

    # Small drift
    drift = drift_per_second_k * t

    for freq in channels:
        col = f"{freq:.3f}"

        # Simple spectral behavior across K-band
        spectral_offset = -0.8 * (freq - 22.0)

        noise = rng.normal(
            loc=0.0,
            scale=instrument_noise_std_k,
            size=n_samples
        )

        df[col] = mean_tb_k + spectral_offset + temporal_variation + drift + noise

    return df


def build_dataset(
    config: dict[str, Any],
    records_override: int | None = None,
    output_prefix: str | None = None,
    export: bool = True,
) -> tuple[MixerResult, dict[str, str]]:
    """
    Build a multi-record clean and contaminated dataset.

    Parameters
    ----------
    config:
        Validated configuration dictionary.
    records_override:
        Optional number of records for testing.
    output_prefix:
        Optional output prefix.
    export:
        If True, save outputs using export_data.py.

    Returns
    -------
    dataset_result:
        MixerResult-like object containing the full dataset.
    exported_files:
        Dictionary of exported file paths.
    """

    run_cfg = config.get("run", {})
    dataset_cfg = config.get("dataset", {})

    base_seed = int(run_cfg.get("seed", 12345))

    n_records = int(dataset_cfg.get("records", 1))
    if records_override is not None:
        n_records = int(records_override)

    if n_records <= 0:
        raise ValueError("Number of records must be greater than zero.")

    clean_parts: list[pd.DataFrame] = []
    contaminated_parts: list[pd.DataFrame] = []
    rfi_parts: list[np.ndarray] = []

    record_metadata: list[dict[str, Any]] = []

    final_channel_cols: list[str] | None = None
    final_channel_freqs: np.ndarray | None = None

    for record_id in range(n_records):
        record_seed = base_seed + record_id

        clean_df = generate_clean_radiometric_record(
            config=config,
            record_id=record_id,
            seed=record_seed,
        )

        mixed = mix_clean_with_rfi(
            clean_df=clean_df,
            config=config,
            seed=record_seed,
        )

        clean_parts.append(mixed.clean_df)
        contaminated_parts.append(mixed.contaminated_df)
        rfi_parts.append(mixed.rfi_matrix)

        final_channel_cols = mixed.channel_cols
        final_channel_freqs = mixed.channel_freqs_ghz

        record_metadata.append({
            "record_id": record_id,
            "seed": record_seed,
            "mixer_metadata": mixed.metadata,
        })

    clean_dataset = pd.concat(clean_parts, ignore_index=True)
    contaminated_dataset = pd.concat(contaminated_parts, ignore_index=True)
    rfi_matrix = np.vstack(rfi_parts)

    if final_channel_cols is None or final_channel_freqs is None:
        raise RuntimeError("Dataset generation failed before producing channel metadata.")

    metadata = {
        "dataset_name": dataset_cfg.get("dataset_name", "unnamed_dataset"),
        "records": n_records,
        "base_seed": base_seed,
        "total_rows": int(len(clean_dataset)),
        "channels": final_channel_cols,
        "record_metadata": record_metadata,
    }

    dataset_result = MixerResult(
        clean_df=clean_dataset,
        contaminated_df=contaminated_dataset,
        rfi_matrix=rfi_matrix,
        channel_cols=final_channel_cols,
        channel_freqs_ghz=final_channel_freqs,
        metadata=metadata,
    )

    exported_files: dict[str, str] = {}

    if export:
        exported_files = export_mixer_result(
            mixer_result=dataset_result,
            config=config,
            output_prefix=output_prefix or str(run_cfg.get("output_prefix", "dataset"))
        )

    return dataset_result, exported_files