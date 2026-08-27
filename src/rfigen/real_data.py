"""Load MP-3000A-style level-1 CSV radiometric scan data."""

from __future__ import annotations

import csv
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
import re
from pathlib import Path

import numpy as np

from rfigen.config import ExperimentConfig
from rfigen.dataset import Dataset
from rfigen.mixer import mix_signals
from rfigen.models import generate_rfi


CHANNEL_PATTERN = re.compile(r"Ch\s+([0-9]+(?:\.[0-9]+)?)")


@dataclass(slots=True)
class RealRadiometryData:
    record: np.ndarray
    datetime_text: list[str]
    time_s: np.ndarray
    azimuth_deg: np.ndarray
    elevation_deg: np.ndarray
    tkbb_k: np.ndarray
    frequency_ghz: np.ndarray
    brightness_k: np.ndarray
    data_quality: np.ndarray

    @property
    def directions(self) -> list[tuple[float, float]]:
        pairs = sorted({(float(az), float(el)) for az, el in zip(self.azimuth_deg, self.elevation_deg, strict=True)})
        return pairs


def load_mp3000a_csv(
    path: str | Path,
    min_frequency_ghz: float = 20.0,
    max_frequency_ghz: float = 30.0,
) -> RealRadiometryData:
    """Load record-code 51 scan rows and selected channel columns.

    The observed file format stores schema rows with record code 50 and scan rows with
    record code 51. Scan rows contain one time/direction record per row.
    """

    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    header = _find_scan_header(rows)
    channel_columns = _channel_columns(header, min_frequency_ghz, max_frequency_ghz)
    if not channel_columns:
        raise ValueError(f"no channel columns found between {min_frequency_ghz} and {max_frequency_ghz} GHz")

    records: list[int] = []
    datetimes: list[str] = []
    parsed_datetimes: list[datetime] = []
    azimuth: list[float] = []
    elevation: list[float] = []
    tkbb: list[float] = []
    quality: list[int] = []
    values: list[list[float]] = []

    for row in rows:
        if len(row) < 3 or row[2].strip() != "51":
            continue
        try:
            records.append(int(row[0]))
            datetimes.append(row[1].strip())
            parsed_datetimes.append(_parse_datetime(row[1].strip()))
            azimuth.append(float(row[3]))
            elevation.append(float(row[4]))
            tkbb.append(float(row[5]))
            values.append([float(row[index]) for index, _ in channel_columns])
            quality.append(_quality_value(row, header))
        except (ValueError, IndexError):
            continue

    if not values:
        raise ValueError("no usable record-code 51 rows found")

    time_s = _seconds_since_start(parsed_datetimes, records)
    return RealRadiometryData(
        record=np.asarray(records, dtype=int),
        datetime_text=datetimes,
        time_s=time_s,
        azimuth_deg=np.asarray(azimuth, dtype=float),
        elevation_deg=np.asarray(elevation, dtype=float),
        tkbb_k=np.asarray(tkbb, dtype=float),
        frequency_ghz=np.asarray([frequency for _, frequency in channel_columns], dtype=float),
        brightness_k=np.asarray(values, dtype=float),
        data_quality=np.asarray(quality, dtype=int),
    )


def summarize_mp3000a_csv(path: str | Path, min_frequency_ghz: float = 20.0, max_frequency_ghz: float = 30.0) -> dict:
    data = load_mp3000a_csv(path, min_frequency_ghz, max_frequency_ghz)
    direction_counts = {
        f"az={az:g}, el={el:g}": int(np.sum((data.azimuth_deg == az) & (data.elevation_deg == el)))
        for az, el in data.directions
    }
    return {
        "rows": int(data.brightness_k.shape[0]),
        "channels": int(data.brightness_k.shape[1]),
        "frequency_min_ghz": float(data.frequency_ghz.min()),
        "frequency_max_ghz": float(data.frequency_ghz.max()),
        "frequencies_ghz": [float(item) for item in data.frequency_ghz],
        "direction_count": len(data.directions),
        "direction_rows": direction_counts,
        "time_start": data.datetime_text[0],
        "time_stop": data.datetime_text[-1],
    }


def build_dataset_from_real_csv(
    path: str | Path,
    config: ExperimentConfig,
    min_frequency_ghz: float = 20.0,
    max_frequency_ghz: float = 30.0,
) -> Dataset:
    """Use real radiometer channel data as clean baseline and inject synthetic RFI."""

    real = load_mp3000a_csv(path, min_frequency_ghz, max_frequency_ghz)
    rng = np.random.default_rng(config.seed)
    rfi_signals = []
    for rfi_config in config.rfi:
        model_seed = rfi_config.seed if rfi_config.seed is not None else int(rng.integers(0, 2**32 - 1))
        rfi_signals.append(generate_rfi(rfi_config, real.time_s, real.frequency_ghz, np.random.default_rng(model_seed)))

    contaminated, rfi = mix_signals(real.brightness_k, rfi_signals)
    metadata = {
        "source_file": str(Path(path)),
        "source_format": "MP-3000A-style level-1 CSV",
        "rows": int(real.brightness_k.shape[0]),
        "frequency_channels_ghz": [float(item) for item in real.frequency_ghz],
        "frequency_range_ghz": [float(real.frequency_ghz.min()), float(real.frequency_ghz.max())],
        "directions": [
            {"azimuth_deg": float(az), "elevation_deg": float(el)}
            for az, el in real.directions
        ],
        "rfi": [asdict(item) for item in config.rfi],
        "seed": config.seed,
        "data_quality_values": sorted({int(item) for item in real.data_quality}),
    }
    return Dataset(
        time_s=real.time_s,
        frequency_ghz=real.frequency_ghz,
        clean=real.brightness_k,
        rfi=rfi,
        contaminated=contaminated,
        metadata=metadata,
        azimuth_deg=real.azimuth_deg,
        elevation_deg=real.elevation_deg,
    )


def _find_scan_header(rows: list[list[str]]) -> list[str]:
    for row in rows:
        if len(row) > 2 and row[2].strip() == "50" and any(CHANNEL_PATTERN.search(name) for name in row):
            return row
    raise ValueError("could not find record-code 50 scan header")


def _channel_columns(header: list[str], min_frequency_ghz: float, max_frequency_ghz: float) -> list[tuple[int, float]]:
    columns = []
    for index, name in enumerate(header):
        match = CHANNEL_PATTERN.search(name)
        if match is None:
            continue
        frequency = float(match.group(1))
        if min_frequency_ghz <= frequency <= max_frequency_ghz:
            columns.append((index, frequency))
    return columns


def _parse_datetime(text: str) -> datetime:
    for fmt in ("%m/%d/%y %H:%M:%S", "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError(f"unsupported datetime format: {text}")


def _quality_value(row: list[str], header: list[str]) -> int:
    try:
        index = next(index for index, name in enumerate(header) if name.strip() == "DataQuality")
    except StopIteration:
        return 0
    if index >= len(row) or not row[index].strip():
        return 0
    return int(float(row[index]))


def _seconds_since_start(datetimes: list[datetime], records: list[int]) -> np.ndarray:
    if not datetimes:
        return np.array([], dtype=float)
    start = datetimes[0]
    seconds = np.asarray([(item - start).total_seconds() for item in datetimes], dtype=float)
    # Some files round timestamps to the minute for several direction rows. Add a tiny
    # monotonic offset so plots and RFI model sweeps retain row order without changing
    # the physical scale in a meaningful way.
    offsets = np.linspace(0.0, 0.999, num=len(records), dtype=float) / max(len(records), 1)
    return seconds + offsets
