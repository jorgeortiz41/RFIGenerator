import csv

from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.real_data import build_dataset_from_real_csv, load_mp3000a_csv, summarize_mp3000a_csv


def _write_sample(path):
    rows = [
        ["Record", "Date/Time", "50", "Az(deg)", "El(deg)", "TkBB(K)", " Ch  22.000", " Ch  22.234", " Ch  30.000", " Ch  51.248", "DataQuality"],
        ["1", "3/20/24 0:05", "51", "0", "19.8", "312.0", "130.0", "131.0", "90.0", "250.0", "1"],
        ["2", "3/20/24 0:05", "51", "0", "90", "312.0", "60.0", "61.0", "40.0", "250.0", "1"],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def test_load_mp3000a_csv_selects_20_to_30_ghz(tmp_path):
    path = tmp_path / "sample.csv"
    _write_sample(path)
    data = load_mp3000a_csv(path)
    assert data.brightness_k.shape == (2, 3)
    assert data.frequency_ghz.tolist() == [22.0, 22.234, 30.0]
    assert len(data.directions) == 2


def test_build_dataset_from_real_csv_injects_rfi(tmp_path):
    path = tmp_path / "sample.csv"
    _write_sample(path)
    config = ExperimentConfig(
        rfi=[RFIConfig(type="narrowband", center_frequency_ghz=22.234, bandwidth_mhz=50, power_k=10)]
    )
    dataset = build_dataset_from_real_csv(path, config)
    assert dataset.clean.shape == (2, 3)
    assert dataset.rfi.max() > 0
    assert dataset.azimuth_deg is not None


def test_summarize_mp3000a_csv_reports_directions(tmp_path):
    path = tmp_path / "sample.csv"
    _write_sample(path)
    summary = summarize_mp3000a_csv(path)
    assert summary["direction_count"] == 2
    assert summary["channels"] == 3
