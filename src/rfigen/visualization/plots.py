"""Matplotlib visualizations for RFIGen datasets."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "rfigen_matplotlib"))

import matplotlib.pyplot as plt
import numpy as np

from rfigen.dataset import Dataset


def plot_time_series(dataset: Dataset, frequency_ghz: float | None = None):
    index = _nearest_frequency_index(dataset.frequency_ghz, frequency_ghz)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(dataset.time_s, dataset.clean[:, index], label="Clean", linewidth=1.6)
    ax.plot(dataset.time_s, dataset.contaminated[:, index], label="Contaminated", linewidth=1.2)
    ax.set_title(f"Time Domain at {dataset.frequency_ghz[index]:.3f} GHz")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Brightness temperature (K)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_frequency(dataset: Dataset, time_s: float | None = None):
    index = _nearest_time_index(dataset.time_s, time_s)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(dataset.frequency_ghz, dataset.clean[index], label="Clean", linewidth=1.6)
    ax.plot(dataset.frequency_ghz, dataset.contaminated[index], label="Contaminated", linewidth=1.2)
    ax.set_title(f"Frequency Domain at {dataset.time_s[index]:.2f} s")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Brightness temperature (K)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_direction_profiles(dataset: Dataset, field: str = "contaminated"):
    values = getattr(dataset, field)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for azimuth, elevation in _directions(dataset):
        mask = _direction_mask(dataset, azimuth, elevation)
        if not np.any(mask):
            continue
        profile = np.median(values[mask], axis=0)
        ax.plot(dataset.frequency_ghz, profile, linewidth=1.5, label=_direction_label(azimuth, elevation))
    ax.set_title(f"Median Radiometric Profiles by Direction ({_field_label(dataset, field)})")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Brightness temperature (K)")
    ax.grid(True, alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    return fig


def plot_profile_for_direction(
    dataset: Dataset,
    azimuth_deg: float,
    elevation_deg: float,
    field: str = "contaminated",
    statistic: str = "median",
):
    values = getattr(dataset, field)
    mask = _direction_mask(dataset, azimuth_deg, elevation_deg)
    if not np.any(mask):
        raise ValueError(f"direction not found: az={azimuth_deg}, el={elevation_deg}")
    if statistic == "first":
        clean_profile = dataset.clean[mask][0]
        field_profile = values[mask][0]
    else:
        clean_profile = np.median(dataset.clean[mask], axis=0)
        field_profile = np.median(values[mask], axis=0)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(dataset.frequency_ghz, clean_profile, label="Baseline", linewidth=1.8)
    ax.plot(dataset.frequency_ghz, field_profile, label=_field_label(dataset, field).capitalize(), linewidth=1.4)
    ax.set_title(f"Radiometric Profile - {_direction_label(azimuth_deg, elevation_deg)}")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Brightness temperature (K)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_spectrogram(dataset: Dataset, field: str = "contaminated"):
    values = getattr(dataset, field)
    fig, ax = plt.subplots(figsize=(9, 5.4))
    mesh = ax.pcolormesh(dataset.frequency_ghz, dataset.time_s, values, shading="auto", cmap="viridis")
    ax.set_title(f"{field.capitalize()} Time-Frequency View")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Time (s)")
    fig.colorbar(mesh, ax=ax, label="Brightness temperature (K)")
    fig.tight_layout()
    return fig


def plot_direction_spectrogram(dataset: Dataset, azimuth_deg: float, elevation_deg: float, field: str = "contaminated"):
    values = getattr(dataset, field)
    mask = _direction_mask(dataset, azimuth_deg, elevation_deg)
    if not np.any(mask):
        raise ValueError(f"direction not found: az={azimuth_deg}, el={elevation_deg}")
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    mesh = ax.pcolormesh(
        dataset.frequency_ghz,
        dataset.time_s[mask],
        values[mask],
        shading="auto",
        cmap="viridis",
    )
    ax.set_title(f"{_field_label(dataset, field).capitalize()} Profiles Over Time - {_direction_label(azimuth_deg, elevation_deg)}")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Time (s)")
    fig.colorbar(mesh, ax=ax, label="Brightness temperature (K)")
    fig.tight_layout()
    return fig


def save_all_plots(dataset: Dataset, output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    figures = {
        "time_domain.png": plot_time_series(dataset),
        "frequency_domain.png": plot_frequency(dataset),
        "profiles_by_direction.png": plot_direction_profiles(dataset),
        "spectrogram_contaminated.png": plot_spectrogram(dataset, "contaminated"),
        "spectrogram_rfi.png": plot_spectrogram(dataset, "rfi"),
    }
    for filename, fig in figures.items():
        fig.savefig(output_path / filename, dpi=160)
        plt.close(fig)
    direction_path = output_path / "directions"
    direction_path.mkdir(exist_ok=True)
    for azimuth, elevation in _directions(dataset):
        stem = f"az_{azimuth:g}_el_{elevation:g}".replace(".", "p")
        for suffix, fig in (
            (f"{stem}_profile.png", plot_profile_for_direction(dataset, azimuth, elevation)),
            (f"{stem}_spectrogram.png", plot_direction_spectrogram(dataset, azimuth, elevation)),
        ):
            fig.savefig(direction_path / suffix, dpi=160)
            plt.close(fig)
    return output_path


def _nearest_frequency_index(axis: np.ndarray, value: float | None) -> int:
    target = float(value) if value is not None else float(axis.mean())
    return int(np.abs(axis - target).argmin())


def _nearest_time_index(axis: np.ndarray, value: float | None) -> int:
    target = float(value) if value is not None else float(axis[len(axis) // 2])
    return int(np.abs(axis - target).argmin())


def _directions(dataset: Dataset) -> list[tuple[float, float]]:
    if dataset.azimuth_deg is None or dataset.elevation_deg is None:
        return [(0.0, 0.0)]
    pairs = {
        (float(azimuth), float(elevation))
        for azimuth, elevation in zip(dataset.azimuth_deg, dataset.elevation_deg, strict=True)
    }
    return sorted(pairs)


def _direction_mask(dataset: Dataset, azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    if dataset.azimuth_deg is None or dataset.elevation_deg is None:
        return np.ones(dataset.time_s.size, dtype=bool)
    return np.isclose(dataset.azimuth_deg, azimuth_deg) & np.isclose(dataset.elevation_deg, elevation_deg)


def _direction_label(azimuth_deg: float, elevation_deg: float) -> str:
    return f"az={azimuth_deg:g}, el={elevation_deg:g}"


def _field_label(dataset: Dataset, field: str) -> str:
    if field == "contaminated" and np.allclose(dataset.rfi, 0.0):
        return "baseline"
    return field
