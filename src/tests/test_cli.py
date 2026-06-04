# test_cli.py
# ============================================================
# Integration tests for the RFIGen CLI.
# ============================================================

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_test_config(tmp_path: Path) -> Path:
    """
    Create a temporary YAML config file for CLI testing.
    """

    output_dir = (tmp_path / "outputs").as_posix()
    figure_dir = (tmp_path / "figures").as_posix()

    config_text = f"""
project:
  name: RFIGen
  version: "0.1.0"
  profile: pytest_cli

run:
  seed: 12345
  n_samples: 32
  sample_rate_hz: 1000000
  duration_s: 0.000032
  output_prefix: pytest_cli

frequency:
  band:
    min_ghz: 22.0
    max_ghz: 30.0
  center_ghz: 22.235
  span_mhz: 200.0

radiometry:
  baseline_type: atmospheric_brightness
  mean_tb_k: 180.0
  variability_tb_k: 4.5
  instrument_noise_std_k: 0.35
  drift_per_second_k: 0.05

composition:
  inject_rfi: true
  contamination_target: both
  amplitude_scaling_mode: linear
  spectral_overlap_policy: add_power
  domain_match: frequency
  snr_db: 18.0
  normalize_output: true

dataset:
  dataset_name: pytest_cli_dataset
  records: 1
  save_clean: true
  save_contaminated: true
  save_metadata: true

export:
  directory: "{output_dir}"
  formats:
    csv: true
    json_metadata: true
    mp3000a_style: false
    npy: true
  overwrite: true

visualization:
  enabled: true
  save_figures: true
  figure_directory: "{figure_dir}"
  products:
    time_domain: true
    frequency_spectrum: true
    spectrogram: true

interfaces:
  cli:
    enabled: true
    allow_parameter_overrides: true
  gui:
    enabled: false
    realtime_preview: false

validation:
  enforce_k_band_limits: true
  require_physical_plausibility: true
  fail_on_invalid_ranges: true

rfi_sources:
  - id: pytest_cli_rfi_001
    type: narrowband
    enabled: true
    center_offset_mhz: 12.0
    bandwidth_mhz: 2.0
    power_dbm: -72.0
    persistence: 1.0
    modulation: none
"""

    config_path = tmp_path / "pytest_cli_config.yaml"
    config_path.write_text(config_text, encoding="utf-8")

    return config_path


def test_cli_generates_dataset_and_figures(tmp_path):
    config_path = write_test_config(tmp_path)

    command = [
        sys.executable,
        "src/cli/rfigen_cli.py",
        "--config",
        str(config_path),
        "--records",
        "1",
        "--output-prefix",
        "pytest_cli",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Dataset generated successfully." in result.stdout
    assert "Exported files:" in result.stdout
    assert "Figure files:" in result.stdout

    output_dir = tmp_path / "outputs"
    figure_dir = tmp_path / "figures"

    assert (output_dir / "pytest_cli_clean.csv").exists()
    assert (output_dir / "pytest_cli_contaminated.csv").exists()
    assert (output_dir / "pytest_cli_rfi_matrix.npy").exists()
    assert (output_dir / "pytest_cli_metadata.json").exists()

    assert (figure_dir / "pytest_cli_time_domain.png").exists()
    assert (figure_dir / "pytest_cli_frequency_spectrum.png").exists()
    assert (figure_dir / "pytest_cli_time_frequency.png").exists()


def test_cli_respects_no_export_and_no_plots(tmp_path):
    config_path = write_test_config(tmp_path)

    command = [
        sys.executable,
        "src/cli/rfigen_cli.py",
        "--config",
        str(config_path),
        "--records",
        "1",
        "--output-prefix",
        "pytest_cli_no_output",
        "--no-export",
        "--no-plots",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "Dataset generated successfully." in result.stdout
    assert "No files exported because --no-export was used." in result.stdout
    assert "No figures generated because --no-plots was used." in result.stdout

    output_dir = tmp_path / "outputs"
    figure_dir = tmp_path / "figures"

    assert not (output_dir / "pytest_cli_no_output_clean.csv").exists()
    assert not (output_dir / "pytest_cli_no_output_contaminated.csv").exists()
    assert not (figure_dir / "pytest_cli_no_output_time_domain.png").exists()