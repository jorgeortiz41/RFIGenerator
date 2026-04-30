import json

import numpy as np
import pandas as pd
import pytest

from src.export.export_data import save_data, save_file
from src.models.signal_mixer import (
    add_rfi_to_dataframe,
    generate_rfi_sources,
    mix_signals,
)


def sample_dataframe():
    return pd.DataFrame(
        {
            "Az(deg)": [0.0, 0.0, 0.0],
            "El(deg)": [45.0, 45.0, 45.0],
            "Ch 22.000": [100.0, 100.0, 100.0],
            "Ch 23.000": [100.0, 100.0, 100.0],
            "Ch 24.000": [100.0, 100.0, 100.0],
        }
    )


def sample_source(**overrides):
    source = {
        "source_class": "test",
        "center_ghz": 23.0,
        "bandwidth_ghz": 2.0,
        "avg_power_K": 5.0,
        "peak_power_K": 20.0,
        "az_deg": 0.0,
        "el_deg": 45.0,
        "sigma_deg": 5.0,
        "modulation": "continuous",
        "spectral_shape": "flat",
    }
    source.update(overrides)
    return source


def test_generate_rfi_sources_returns_requested_count():
    rng = np.random.default_rng(123)

    sources = generate_rfi_sources(3, ["satellite", "aircraft"], rng)

    assert len(sources) == 3
    assert {source["source_class"] for source in sources}.issubset(
        {"satellite", "aircraft"}
    )


def test_add_rfi_to_dataframe_updates_channel_values_and_metadata():
    rng = np.random.default_rng(123)
    df = sample_dataframe()

    updated_df, infos = add_rfi_to_dataframe(df, [sample_source()], rng)

    assert updated_df[["Ch 22.000", "Ch 23.000", "Ch 24.000"]].to_numpy().min() > 100.0
    assert infos == [
        {
            "center_ghz": 23.0,
            "bandwidth_ghz": 2.0,
            "power": 20.0,
            "avg_coupling": pytest.approx(1.0),
        }
    ]


def test_add_rfi_to_dataframe_rejects_data_without_frequency_channels():
    df = pd.DataFrame({"Az(deg)": [0.0], "El(deg)": [45.0]})

    with pytest.raises(ValueError, match="No frequency channels"):
        add_rfi_to_dataframe(df, [sample_source()], np.random.default_rng(123))


def test_mix_signals_preserves_single_dataframe_return_shape():
    mixed_df, infos = mix_signals(
        sample_dataframe(),
        [sample_source()],
        np.random.default_rng(123),
    )

    assert isinstance(mixed_df, pd.DataFrame)
    assert len(infos) == 1
    assert len(infos[0]) == 1


def test_save_data_writes_string_dataframe_and_json(tmp_path):
    text_path = save_data("hello", tmp_path / "text.txt")
    csv_path = save_data(sample_dataframe(), tmp_path / "data.csv")
    json_path = save_data({"ok": True}, tmp_path / "data.json")

    assert text_path.read_text(encoding="utf-8") == "hello"
    assert pd.read_csv(csv_path).shape == sample_dataframe().shape
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"ok": True}


def test_save_file_copies_to_requested_path(tmp_path):
    source_path = tmp_path / "source.txt"
    output_path = tmp_path / "nested" / "copied.txt"
    source_path.write_text("content", encoding="utf-8")

    saved_path = save_file(source_path, output_path)

    assert saved_path == output_path
    assert output_path.read_text(encoding="utf-8") == "content"
