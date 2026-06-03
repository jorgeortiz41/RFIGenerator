# test_signal_mixer.py
# ============================================================
# Unit tests for the Signal Mixer module.
# ============================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.mixer.signal_mixer import (
    find_frequency_channels,
    mix_clean_with_rfi,
)


def make_test_config(inject_rfi: bool = True) -> dict:
    """
    Create a small test configuration for the signal mixer.
    """

    return {
        "run": {
            "seed": 12345,
            "n_samples": 100,
            "sample_rate_hz": 1_000_000,
            "duration_s": 0.0001,
            "output_prefix": "test",
        },
        "frequency": {
            "band": {
                "min_ghz": 22.0,
                "max_ghz": 30.0,
            },
            "center_ghz": 22.235,
            "span_mhz": 200.0,
        },
        "composition": {
            "inject_rfi": inject_rfi,
            "contamination_target": "both",
            "amplitude_scaling_mode": "linear",
            "spectral_overlap_policy": "add_power",
            "domain_match": "frequency",
            "snr_db": 18.0,
            "normalize_output": True,
        },
        "rfi_sources": [
            {
                "id": "test_rfi_001",
                "type": "narrowband",
                "enabled": True,
                "center_offset_mhz": 12.0,
                "bandwidth_mhz": 2.0,
                "power_dbm": -72.0,
                "persistence": 1.0,
                "modulation": "none",
            }
        ],
    }


def make_clean_dataframe(n_samples: int = 100) -> pd.DataFrame:
    """
    Create a small clean radiometric dataframe with MP-3000A-like channels.
    """

    rng = np.random.default_rng(42)

    freqs = [
        "22.000",
        "22.234",
        "22.500",
        "23.000",
        "23.834",
        "25.000",
        "26.234",
        "28.000",
        "30.000",
    ]

    df = pd.DataFrame(
        {
            "Date/Time": pd.date_range(
                "2026-01-01 00:00:00",
                periods=n_samples,
                freq="1s",
            ),
            "Az(deg)": np.zeros(n_samples),
            "El(deg)": np.ones(n_samples) * 90.0,
        }
    )

    for freq in freqs:
        df[freq] = 180.0 + rng.normal(0.0, 0.5, size=n_samples)

    return df


def test_find_frequency_channels_detects_kband_columns():
    df = make_clean_dataframe()

    channel_cols, channel_freqs = find_frequency_channels(df)

    assert len(channel_cols) == 9
    assert len(channel_freqs) == 9
    assert channel_cols[0] == "22.000"
    assert channel_cols[-1] == "30.000"
    assert np.isclose(channel_freqs[0], 22.000)
    assert np.isclose(channel_freqs[-1], 30.000)


def test_mixer_preserves_dataframe_shape():
    df = make_clean_dataframe()
    config = make_test_config(inject_rfi=True)

    result = mix_clean_with_rfi(df, config)

    assert result.clean_df.shape == df.shape
    assert result.contaminated_df.shape == df.shape


def test_rfi_matrix_has_correct_shape():
    df = make_clean_dataframe()
    config = make_test_config(inject_rfi=True)

    result = mix_clean_with_rfi(df, config)

    assert result.rfi_matrix.shape[0] == len(df)
    assert result.rfi_matrix.shape[1] == len(result.channel_cols)


def test_contaminated_data_changes_when_rfi_is_enabled():
    df = make_clean_dataframe()
    config = make_test_config(inject_rfi=True)

    result = mix_clean_with_rfi(df, config)

    clean_values = result.clean_df[result.channel_cols].to_numpy(float)
    contaminated_values = result.contaminated_df[result.channel_cols].to_numpy(float)

    assert not np.allclose(clean_values, contaminated_values)
    assert np.nanmax(result.rfi_matrix) > 0


def test_contaminated_data_does_not_change_when_rfi_is_disabled():
    df = make_clean_dataframe()
    config = make_test_config(inject_rfi=False)

    result = mix_clean_with_rfi(df, config)

    clean_values = result.clean_df[result.channel_cols].to_numpy(float)
    contaminated_values = result.contaminated_df[result.channel_cols].to_numpy(float)

    assert np.allclose(clean_values, contaminated_values)
    assert np.nanmax(result.rfi_matrix) == 0


def test_metadata_is_created():
    df = make_clean_dataframe()
    config = make_test_config(inject_rfi=True)

    result = mix_clean_with_rfi(df, config)

    assert "seed" in result.metadata
    assert "sources" in result.metadata
    assert "total_rfi" in result.metadata
    assert len(result.metadata["sources"]) == 1


def test_error_when_no_frequency_channels_are_found():
    df = pd.DataFrame(
        {
            "Date/Time": pd.date_range("2026-01-01", periods=10, freq="1s"),
            "Az(deg)": np.zeros(10),
            "El(deg)": np.ones(10) * 90.0,
        }
    )

    config = make_test_config(inject_rfi=True)

    with pytest.raises(ValueError):
        mix_clean_with_rfi(df, config)