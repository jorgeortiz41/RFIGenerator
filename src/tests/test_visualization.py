# test_visualization.py
# ============================================================
# Unit tests for the Visualization module.
# ============================================================

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.mixer.signal_mixer import MixerResult
from src.visualization.plots import (
    generate_visualization_products,
    plot_frequency_spectrum,
    plot_time_domain,
    plot_time_frequency,
)


def make_visualization_config(output_dir: str) -> dict:
    """
    Create a small visualization config for testing.
    """

    return {
        "run": {
            "output_prefix": "pytest_viz",
        },
        "visualization": {
            "enabled": True,
            "save_figures": True,
            "figure_directory": output_dir,
            "products": {
                "time_domain": True,
                "frequency_spectrum": True,
                "spectrogram": True,
            },
        },
    }


def make_mixer_result() -> MixerResult:
    """
    Create a small MixerResult object for visualization testing.
    """

    n_samples = 50

    time = pd.date_range(
        "2026-01-01 00:00:00",
        periods=n_samples,
        freq="1s",
    )

    clean_df = pd.DataFrame(
        {
            "Date/Time": time,
            "Az(deg)": np.zeros(n_samples),
            "El(deg)": np.ones(n_samples) * 90.0,
            "22.000": 180.0 + np.random.normal(0, 0.2, n_samples),
            "22.234": 181.0 + np.random.normal(0, 0.2, n_samples),
            "25.000": 175.0 + np.random.normal(0, 0.2, n_samples),
            "30.000": 170.0 + np.random.normal(0, 0.2, n_samples),
        }
    )

    contaminated_df = clean_df.copy()
    contaminated_df.loc[:, "22.234"] = contaminated_df["22.234"] + 5.0
    contaminated_df.loc[:, "25.000"] = contaminated_df["25.000"] + 2.0

    rfi_matrix = np.zeros((n_samples, 4))
    rfi_matrix[:, 1] = 5.0
    rfi_matrix[:, 2] = 2.0

    return MixerResult(
        clean_df=clean_df,
        contaminated_df=contaminated_df,
        rfi_matrix=rfi_matrix,
        channel_cols=["22.000", "22.234", "25.000", "30.000"],
        channel_freqs_ghz=np.array([22.000, 22.234, 25.000, 30.000]),
        metadata={
            "seed": 12345,
            "sources": [],
            "total_rfi": {
                "max_rfi_k": 5.0,
            },
        },
    )


def test_plot_time_domain_creates_png(tmp_path):
    mixer_result = make_mixer_result()

    output_path = tmp_path / "time_domain.png"

    saved_path = plot_time_domain(
        clean_df=mixer_result.clean_df,
        contaminated_df=mixer_result.contaminated_df,
        channel_col="22.234",
        output_path=output_path,
    )

    assert Path(saved_path).exists()
    assert Path(saved_path).suffix == ".png"


def test_plot_frequency_spectrum_creates_png(tmp_path):
    mixer_result = make_mixer_result()

    output_path = tmp_path / "frequency_spectrum.png"

    saved_path = plot_frequency_spectrum(
        clean_df=mixer_result.clean_df,
        contaminated_df=mixer_result.contaminated_df,
        channel_cols=mixer_result.channel_cols,
        channel_freqs_ghz=mixer_result.channel_freqs_ghz,
        output_path=output_path,
    )

    assert Path(saved_path).exists()
    assert Path(saved_path).suffix == ".png"


def test_plot_time_frequency_creates_png(tmp_path):
    mixer_result = make_mixer_result()

    output_path = tmp_path / "time_frequency.png"

    saved_path = plot_time_frequency(
        contaminated_df=mixer_result.contaminated_df,
        channel_cols=mixer_result.channel_cols,
        channel_freqs_ghz=mixer_result.channel_freqs_ghz,
        output_path=output_path,
    )

    assert Path(saved_path).exists()
    assert Path(saved_path).suffix == ".png"


def test_generate_visualization_products_creates_all_enabled_figures(tmp_path):
    mixer_result = make_mixer_result()
    config = make_visualization_config(output_dir=str(tmp_path))

    figure_files = generate_visualization_products(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_viz",
    )

    assert "time_domain" in figure_files
    assert "frequency_spectrum" in figure_files
    assert "time_frequency" in figure_files

    for path in figure_files.values():
        assert Path(path).exists()
        assert Path(path).suffix == ".png"


def test_generate_visualization_products_respects_disabled_visualization(tmp_path):
    mixer_result = make_mixer_result()
    config = make_visualization_config(output_dir=str(tmp_path))

    config["visualization"]["enabled"] = False

    figure_files = generate_visualization_products(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_viz",
    )

    assert figure_files == {}


def test_generate_visualization_products_respects_disabled_save_figures(tmp_path):
    mixer_result = make_mixer_result()
    config = make_visualization_config(output_dir=str(tmp_path))

    config["visualization"]["save_figures"] = False

    figure_files = generate_visualization_products(
        mixer_result=mixer_result,
        config=config,
        output_prefix="pytest_viz",
    )

    assert figure_files == {}