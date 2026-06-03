# test_dataset_builder.py
# ============================================================
# Unit tests for the Dataset Builder module.
# ============================================================

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.data.dataset_builder import build_dataset, generate_clean_radiometric_record


def make_dataset_config(output_dir: str = "outputs/test_tmp") -> dict:
    """
    Create a small config for dataset builder testing.
    """

    return {
        "run": {
            "seed": 12345,
            "n_samples": 32,
            "sample_rate_hz": 1_000_000,
            "duration_s": 0.000032,
            "output_prefix": "pytest_dataset",
        },
        "frequency": {
            "band": {
                "min_ghz": 22.0,
                "max_ghz": 30.0,
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
            "dataset_name": "pytest_dataset",
            "records": 2,
            "save_clean": True,
            "save_contaminated": True,
            "save_metadata": True,
        },
        "export": {
            "directory": output_dir,
            "formats": {
                "csv": True,
                "json_metadata": True,
                "mp3000a_style": False,
                "npy": True,
            },
            "overwrite": True,
        },
        "rfi_sources": [
            {
                "id": "pytest_rfi_001",
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


def test_generate_clean_radiometric_record_shape():
    config = make_dataset_config()

    df = generate_clean_radiometric_record(
        config=config,
        record_id=0,
        seed=12345,
    )

    assert df.shape[0] == 32
    assert "Date/Time" in df.columns
    assert "Az(deg)" in df.columns
    assert "El(deg)" in df.columns
    assert "22.000" in df.columns
    assert "30.000" in df.columns


def test_build_dataset_creates_expected_number_of_rows():
    config = make_dataset_config()

    dataset_result, exported_files = build_dataset(
        config=config,
        records_override=2,
        output_prefix="pytest_dataset",
        export=False,
    )

    assert dataset_result.clean_df.shape[0] == 64
    assert dataset_result.contaminated_df.shape[0] == 64
    assert dataset_result.rfi_matrix.shape[0] == 64
    assert exported_files == {}


def test_build_dataset_preserves_clean_and_contaminated_shapes():
    config = make_dataset_config()

    dataset_result, _ = build_dataset(
        config=config,
        records_override=2,
        output_prefix="pytest_dataset",
        export=False,
    )

    assert dataset_result.clean_df.shape == dataset_result.contaminated_df.shape


def test_build_dataset_rfi_matrix_matches_channel_count():
    config = make_dataset_config()

    dataset_result, _ = build_dataset(
        config=config,
        records_override=2,
        output_prefix="pytest_dataset",
        export=False,
    )

    assert dataset_result.rfi_matrix.shape[1] == len(dataset_result.channel_cols)
    assert dataset_result.rfi_matrix.shape[1] == len(dataset_result.channel_freqs_ghz)


def test_build_dataset_metadata_is_created():
    config = make_dataset_config()

    dataset_result, _ = build_dataset(
        config=config,
        records_override=2,
        output_prefix="pytest_dataset",
        export=False,
    )

    assert "dataset_name" in dataset_result.metadata
    assert "records" in dataset_result.metadata
    assert "record_metadata" in dataset_result.metadata
    assert dataset_result.metadata["records"] == 2
    assert len(dataset_result.metadata["record_metadata"]) == 2


def test_build_dataset_export_creates_files(tmp_path):
    config = make_dataset_config(output_dir=str(tmp_path))

    dataset_result, exported_files = build_dataset(
        config=config,
        records_override=1,
        output_prefix="pytest_export",
        export=True,
    )

    assert dataset_result.clean_df.shape[0] == 32

    assert "clean_csv" in exported_files
    assert "contaminated_csv" in exported_files
    assert "rfi_matrix_npy" in exported_files
    assert "metadata_json" in exported_files

    for path in exported_files.values():
        assert Path(path).exists()


def test_contaminated_dataset_differs_from_clean_dataset():
    config = make_dataset_config()

    dataset_result, _ = build_dataset(
        config=config,
        records_override=1,
        output_prefix="pytest_dataset",
        export=False,
    )

    clean_values = dataset_result.clean_df[dataset_result.channel_cols].to_numpy(float)
    contaminated_values = dataset_result.contaminated_df[dataset_result.channel_cols].to_numpy(float)

    assert not np.allclose(clean_values, contaminated_values)