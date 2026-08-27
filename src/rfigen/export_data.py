"""Dataset export utilities."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from rfigen.dataset import Dataset


def export_dataset(dataset: Dataset, output_dir: str | Path, include_csv: bool = True, include_npz: bool = True) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    _write_metadata(dataset, output_path / "metadata.json")
    if include_npz:
        np.savez_compressed(
            output_path / "dataset.npz",
            time_s=dataset.time_s,
            frequency_ghz=dataset.frequency_ghz,
            clean=dataset.clean,
            rfi=dataset.rfi,
            contaminated=dataset.contaminated,
            azimuth_deg=dataset.azimuth_deg if dataset.azimuth_deg is not None else np.array([]),
            elevation_deg=dataset.elevation_deg if dataset.elevation_deg is not None else np.array([]),
        )
    if include_csv:
        _write_matrix_csv(output_path / "clean.csv", dataset.time_s, dataset.frequency_ghz, dataset.clean)
        _write_matrix_csv(output_path / "rfi.csv", dataset.time_s, dataset.frequency_ghz, dataset.rfi)
        _write_matrix_csv(output_path / "contaminated.csv", dataset.time_s, dataset.frequency_ghz, dataset.contaminated)
    return output_path


def _write_metadata(dataset: Dataset, path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(dataset.metadata, handle, indent=2)


def _write_matrix_csv(path: Path, time_s: np.ndarray, frequency_ghz: np.ndarray, values: np.ndarray) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s/frequency_ghz", *[f"{item:.6f}" for item in frequency_ghz]])
        for timestamp, row in zip(time_s, values, strict=True):
            writer.writerow([f"{timestamp:.6f}", *[f"{item:.8f}" for item in row]])
