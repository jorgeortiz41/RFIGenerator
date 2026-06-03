# plots.py
# ============================================================
# Visualization Module
# ------------------------------------------------------------
# Generates time-domain, frequency-domain, and time-frequency
# plots from clean and contaminated radiometric datasets.
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def _get_output_figure_dir(config: dict[str, Any]) -> Path:
    """
    Get figure output directory from config.
    """

    viz_cfg = config.get("visualization", {})
    figure_dir = viz_cfg.get("figure_directory", "outputs/figures")

    path = Path(figure_dir)
    path.mkdir(parents=True, exist_ok=True)

    return path


def _select_time_channel(channel_cols: list[str]) -> str:
    """
    Select a default frequency channel for time-domain plotting.
    Uses the middle channel when possible.
    """

    if not channel_cols:
        raise ValueError("No channel columns available for plotting.")

    return channel_cols[len(channel_cols) // 2]


def plot_time_domain(
    clean_df: pd.DataFrame,
    contaminated_df: pd.DataFrame,
    channel_col: str,
    output_path: Path,
    max_points: int = 2000,
) -> str:
    """
    Plot clean vs contaminated brightness temperature over time
    for one selected frequency channel.
    """

    if channel_col not in clean_df.columns:
        raise ValueError(f"Channel not found in clean dataframe: {channel_col}")

    if channel_col not in contaminated_df.columns:
        raise ValueError(f"Channel not found in contaminated dataframe: {channel_col}")

    n = min(len(clean_df), max_points)

    if "Date/Time" in clean_df.columns:
        x = pd.to_datetime(clean_df["Date/Time"].iloc[:n], errors="coerce")
        xlabel = "Time"
    else:
        x = np.arange(n)
        xlabel = "Sample"

    y_clean = clean_df[channel_col].iloc[:n].to_numpy(float)
    y_cont = contaminated_df[channel_col].iloc[:n].to_numpy(float)

    plt.figure(figsize=(10, 5))
    plt.plot(x, y_clean, label="Clean", linewidth=1.5)
    plt.plot(x, y_cont, label="Contaminated", linewidth=1.2)
    plt.title(f"Time Domain — {channel_col} GHz")
    plt.xlabel(xlabel)
    plt.ylabel("Brightness Temperature (K)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    return str(output_path)


def plot_frequency_spectrum(
    clean_df: pd.DataFrame,
    contaminated_df: pd.DataFrame,
    channel_cols: list[str],
    channel_freqs_ghz: np.ndarray,
    output_path: Path,
) -> str:
    """
    Plot mean brightness temperature vs frequency.
    """

    clean_values = clean_df[channel_cols].to_numpy(float)
    contaminated_values = contaminated_df[channel_cols].to_numpy(float)

    clean_mean = np.nanmean(clean_values, axis=0)
    contaminated_mean = np.nanmean(contaminated_values, axis=0)

    plt.figure(figsize=(10, 5))
    plt.plot(channel_freqs_ghz, clean_mean, marker="o", label="Clean")
    plt.plot(channel_freqs_ghz, contaminated_mean, marker="o", label="Contaminated")
    plt.title("Frequency Spectrum — Mean Brightness Temperature")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Brightness Temperature (K)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    return str(output_path)


def plot_time_frequency(
    contaminated_df: pd.DataFrame,
    channel_cols: list[str],
    channel_freqs_ghz: np.ndarray,
    output_path: Path,
    max_time_samples: int = 1000,
) -> str:
    """
    Create a time-frequency image using contaminated brightness temperature.

    X-axis: frequency
    Y-axis: time/sample
    Color: brightness temperature
    """

    n = min(len(contaminated_df), max_time_samples)

    data = contaminated_df[channel_cols].iloc[:n].to_numpy(float)

    plt.figure(figsize=(10, 6))
    plt.imshow(
        data,
        aspect="auto",
        origin="lower",
        extent=[
            float(np.nanmin(channel_freqs_ghz)),
            float(np.nanmax(channel_freqs_ghz)),
            0,
            n,
        ],
    )
    plt.colorbar(label="Brightness Temperature (K)")
    plt.title("Time-Frequency Representation — Contaminated Data")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Sample Index")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    return str(output_path)


def generate_visualization_products(
    mixer_result: Any,
    config: dict[str, Any],
    output_prefix: str | None = None,
) -> dict[str, str]:
    """
    Generate all enabled visualization products from config.

    Returns
    -------
    dict
        Paths to saved figure files.
    """

    viz_cfg = config.get("visualization", {})

    if not viz_cfg.get("enabled", True):
        return {}

    if not viz_cfg.get("save_figures", True):
        return {}

    products = viz_cfg.get("products", {})

    figure_dir = _get_output_figure_dir(config)

    if output_prefix is None:
        output_prefix = str(config.get("run", {}).get("output_prefix", "run_001"))

    generated: dict[str, str] = {}

    channel_cols = mixer_result.channel_cols
    channel_freqs = mixer_result.channel_freqs_ghz

    time_channel = _select_time_channel(channel_cols)

    if products.get("time_domain", True):
        path = figure_dir / f"{output_prefix}_time_domain.png"
        generated["time_domain"] = plot_time_domain(
            clean_df=mixer_result.clean_df,
            contaminated_df=mixer_result.contaminated_df,
            channel_col=time_channel,
            output_path=path,
        )

    if products.get("frequency_spectrum", True):
        path = figure_dir / f"{output_prefix}_frequency_spectrum.png"
        generated["frequency_spectrum"] = plot_frequency_spectrum(
            clean_df=mixer_result.clean_df,
            contaminated_df=mixer_result.contaminated_df,
            channel_cols=channel_cols,
            channel_freqs_ghz=channel_freqs,
            output_path=path,
        )

    if products.get("spectrogram", True):
        path = figure_dir / f"{output_prefix}_time_frequency.png"
        generated["time_frequency"] = plot_time_frequency(
            contaminated_df=mixer_result.contaminated_df,
            channel_cols=channel_cols,
            channel_freqs_ghz=channel_freqs,
            output_path=path,
        )

    return generated