# test_export_data.py
# ============================================================
# Unit tests for the Export Data module.
# ============================================================

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.export.export_data import export_mixer_result, make_json_serializable
from src.mixer.signal_mixer import MixerResult


def make_export_config(output_dir: str) -> dict:
    """
    Create a small export config for testing.
    """

    return {
        "run": {
            "seed": 12345,
            "output_prefix": "pytest_export",
        },
        "dataset": {
            "dataset_name": "pytest_export_dataset",
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
    }


def make_mixer_result() -> MixerResult:
    """
    Create a small MixerResult object for export testing.
    """

    n_samples = 10

    clean_df = pd.DataFrame(
        {
            "Date/Time": pd.date_range("2026-01-01", periods=n_samples, freq="1s"),
            "Az(deg)": np.zeros(n_samples),
            "El(deg)": np.ones(n_samples) * 90.0,
            "22.000": np.ones(n_samples) * 180.0,
            "22.234": np.ones(n_samples) * 181.0,
            "30.000": np.ones(n_samples) * 170.0,
        }
    )

    contaminated_df = clean_df.copy()
    contaminated_df.loc[:, "22.234"] = contaminated_df["22.234"] + 5.0

    rfi_matrix = np.zeros((n_samples, 3))
    rfi_matrix[:, 1] = 5.0

    return MixerResult(
        clean_df=clean_df,
        contaminated_df=contaminated_df,
        rfi_matrix=rfi_matrix,
        channel_cols=["22.000", "22.234", "30.000"],
        channel_freqs_ghz=np.array([22.000, 22.234, 30.000]),
        metadata={
            "seed": 12345,
            "sources": [
                {
                    "id": "test_source",
                    "type": "narrowband",
                    "center_ghz": 22.234,
                }
            ],
            "total_rfi": {
                "max_rfi_k": 5.0,
                "mean_rfi_k": 1.6667,
            },
        },
    )


def test_make_json_serializable_converts_numpy_objects():
    data = {
        "array": np.array([1.0, 2.0, 3.0]),
        "integer": np.int64(5),
        "floating": np.float64(2.5),
        "boolean": np.bool_(True),
    }

    converted = make_json_serializable(data)

    assert converted["array"] == [1.0, 2.0, 3.0]
    assert converted["integer"] == 5
    assert converted["floating"] == 2.5
    assert converted["boolean"] is True


def test_export_mixer_result_creates_expected_files(tmp_path):
    config = make_export_config(output_dir=str(tmp_path))
    mixer_result = make_mixer_result()

    exported_files = export_mixer_result(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_export",
    )

    assert "clean_csv" in exported_files
    assert "contaminated_csv" in exported_files
    assert "rfi_matrix_npy" in exported_files
    assert "metadata_json" in exported_files

    for path in exported_files.values():
        assert Path(path).exists()


def test_exported_csv_files_can_be_read(tmp_path):
    config = make_export_config(output_dir=str(tmp_path))
    mixer_result = make_mixer_result()

    exported_files = export_mixer_result(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_export",
    )

    clean_df = pd.read_csv(exported_files["clean_csv"])
    contaminated_df = pd.read_csv(exported_files["contaminated_csv"])

    assert clean_df.shape == mixer_result.clean_df.shape
    assert contaminated_df.shape == mixer_result.contaminated_df.shape


def test_exported_rfi_matrix_can_be_loaded(tmp_path):
    config = make_export_config(output_dir=str(tmp_path))
    mixer_result = make_mixer_result()

    exported_files = export_mixer_result(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_export",
    )

    loaded_rfi = np.load(exported_files["rfi_matrix_npy"])

    assert loaded_rfi.shape == mixer_result.rfi_matrix.shape
    assert np.nanmax(loaded_rfi) == 5.0


def test_exported_metadata_json_can_be_read(tmp_path):
    config = make_export_config(output_dir=str(tmp_path))
    mixer_result = make_mixer_result()

    exported_files = export_mixer_result(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_export",
    )

    with open(exported_files["metadata_json"], "r", encoding="utf-8") as f:
        metadata = json.load(f)

    assert metadata["dataset_name"] == "pytest_export_dataset"
    assert metadata["output_prefix"] == "pytest_export"
    assert metadata["channel_columns"] == ["22.000", "22.234", "30.000"]
    assert "mixer_metadata" in metadata
    assert metadata["mixer_metadata"]["seed"] == 12345


def test_export_respects_disabled_csv_format(tmp_path):
    config = make_export_config(output_dir=str(tmp_path))
    config["export"]["formats"]["csv"] = False

    mixer_result = make_mixer_result()

    exported_files = export_mixer_result(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_export",
    )

    assert "clean_csv" not in exported_files
    assert "contaminated_csv" not in exported_files
    assert "rfi_matrix_npy" in exported_files
    assert "metadata_json" in exported_files