"""Tests for the RTTOV Level-1 generator and its bridge to the legacy mixer.

The config-driven RTTOV path was dead before the RFIGen_1/RFIGen_2 merge: the
pipeline called ``main(config)`` on a ``main()`` that took no arguments, and even
past that, RTTOV's tidy/long output has no ``Ch <freq>`` columns for the mixer.
These cover both halves of that fix.
"""

import pandas as pd
import pytest

from rfigen.legacy.rttov import (
    K_BAND_CHANNELS_GHZ,
    generate_level1,
    generate_level1_from_config,
    level1_to_wide_frame,
)
from rfigen.legacy.signal_mixer import generate_rfi_sources, mix_signals


@pytest.fixture()
def level1_csv(tmp_path):
    return generate_level1(tmp_path / "lv1.csv", hours=0.2, step_seconds=120, seed=3)


def test_generate_level1_writes_scan_rows(level1_csv):
    frame = pd.read_csv(level1_csv)
    scans = frame[frame["record_type"] == 51]
    assert not scans.empty
    assert scans["tb_k"].between(20.0, 400.0).all(), "brightness temperatures stay physical"
    assert len(scans["frequency_ghz"].unique()) == len(K_BAND_CHANNELS_GHZ) + 14


def test_generate_level1_rejects_bad_arguments(tmp_path):
    with pytest.raises(ValueError):
        generate_level1(tmp_path / "a.csv", hours=0)
    with pytest.raises(ValueError):
        generate_level1(tmp_path / "b.csv", step_seconds=0)


def test_level1_to_wide_frame_matches_mp3000a_layout(level1_csv):
    wide = level1_to_wide_frame(level1_csv)
    channels = [column for column in wide.columns if column.startswith("Ch ")]

    assert len(channels) == len(K_BAND_CHANNELS_GHZ)
    assert [float(column.split()[1]) for column in channels] == K_BAND_CHANNELS_GHZ
    for required in ("Record", "Date/Time", "Az(deg)", "El(deg)", "TkBB(K)"):
        assert required in wide.columns


def test_wide_frame_feeds_the_legacy_mixer(level1_csv):
    """The reshape exists so this call works; it raised ValueError before."""
    import numpy as np

    wide = level1_to_wide_frame(level1_csv)
    rng = np.random.default_rng(0)
    sources = generate_rfi_sources(3, ["satellite", "ground"], rng)
    mixed, infos = mix_signals(wide, sources, rng)

    channels = [column for column in wide.columns if column.startswith("Ch ")]
    assert len(infos[0]) == 3
    assert (mixed[channels].values >= wide[channels].values).all(), "RFI is additive"


def test_generate_level1_from_config_honours_export_directory(tmp_path):
    config = {
        "run": {"seed": 11},
        "radiometry": {"rttov_hours": 0.1, "rttov_step_seconds": 180},
        "export": {"directory": str(tmp_path)},
    }
    output = generate_level1_from_config(config)
    assert output.exists()
    assert output.parent == tmp_path
