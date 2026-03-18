# rfi_gui.py
# ============================================================
# MP-3000 LV1 GUI (22–30 GHz)
# ------------------------------------------------------------
# What this app does:
#   1) Preprocess: converts messy *_lv1.xlsx or *_lv1.csv -> *_lv1_clean.xlsx
#   2) Plot controls using CLEAN data
#   3) Optional: Add synthetic RFI source (plot only)
#      - Source classes:
#          * 5G
#          * Radar Systems
#          * Broadcast Services
#          * ISM Equipment
#          * Unintentional Emitters
#      - Each source class has different spectral/temporal/power behavior
#   4) Save Plot as PNG (300 DPI)
#
# Notes:
#   - Your LV1 "TB" behaves like received power -> RFI is added (sums).
#   - The synthetic RFI is only applied to the plot, never saved to disk.
# ============================================================

from __future__ import annotations

# Standard library imports
import os
import re
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING, Any, Optional, TypeAlias

# Numerical / plotting libraries
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# pandas is optional at import time so the script can show a GUI error
# instead of crashing immediately if pandas is not installed.
try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore

# Type alias for DataFrame so the code still has type hints even if pandas is missing.
if TYPE_CHECKING:
    from pandas import DataFrame as DataFrame
else:
    DataFrame: TypeAlias = Any


# ============================================================
# 1) CONSTANTS + PATTERNS
# ============================================================

# Match columns like "Ch 22.000" or "Ch   22.000"
CHANNEL_PATTERN = re.compile(r"^Ch\s+(\d+(?:\.\d+)?)$")

# Frequency band used by this GUI / radiometer analysis
FREQ_MIN_GHZ = 22.0
FREQ_MAX_GHZ = 30.0

# Tolerance when filtering rows by Az/El direction
DIRECTION_ATOL_DEG = 1e-3

# Available synthetic RFI classes shown in the GUI
RFI_SOURCE_OPTIONS = [
    "5G",
    "Radar Systems",
    "Broadcast Services",
    "ISM Equipment",
    "Unintentional Emitters",
]


# ============================================================
# 2) SMALL UTILITIES
# ============================================================

def require_pandas() -> bool:
    # Stop execution early if pandas/openpyxl are missing.
    if pd is None:
        messagebox.showerror(
            "Missing dependency",
            "This GUI needs pandas + openpyxl.\n\nInstall with:\n  pip install pandas openpyxl"
        )
        return False
    return True


def _clip(x: float, lo: float, hi: float) -> float:
    # Clip a value into a valid numeric range.
    return float(np.clip(x, lo, hi))


def _is_excel_temp_file(path: str) -> bool:
    # Ignore temporary Excel files that start with "~$"
    return os.path.basename(path).startswith("~$")


def _normalize_cols(df: DataFrame) -> DataFrame:
    # Strip spaces from column names so matching is more robust.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _find_datetime_col(df: DataFrame) -> str:
    # Try to find the Date/Time column using common possible names.
    if "Date/Time" in df.columns:
        return "Date/Time"

    lower_map = {str(c).strip().lower(): str(c).strip() for c in df.columns}
    if "date/time" in lower_map:
        return lower_map["date/time"]

    for key in ("datetime", "date time", "timestamp", "time"):
        if key in lower_map:
            return lower_map[key]

    raise ValueError("Could not find a Date/Time column in the file.")


def _estimate_dt_seconds(dt_series) -> float:
    # Estimate the median time step between samples in seconds.
    # This is important for pulse width and repetition modeling.
    try:
        t = pd.to_datetime(dt_series, errors="coerce") if pd is not None else dt_series
        t = np.asarray(t)
        if len(t) < 2:
            return 1.0
        tsec = (t - t[0]) / np.timedelta64(1, "s")
        tsec = np.asarray(tsec, dtype=float)
        d = np.diff(tsec)
        d = d[np.isfinite(d)]
        if d.size == 0:
            return 1.0
        med = float(np.nanmedian(d))
        return med if (np.isfinite(med) and med > 0) else 1.0
    except Exception:
        return 1.0


def _safe_float(value: str, default: float = 0.0) -> float:
    # Convert GUI text to float safely.
    try:
        return float(value)
    except Exception:
        return default


def _ang_diff_deg(a: float, b: float) -> float:
    # Return the smallest angular difference between two angles in degrees.
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _angular_coupling(
    pointing_az_deg: float,
    pointing_el_deg: float,
    source_az_deg: float,
    source_el_deg: float,
    sigma_deg: float
) -> float:
    # Compute how strongly the RFI source couples into the radiometer
    # based on angular mismatch between radiometer pointing and source direction.
    # Smaller sigma -> more directional source.
    sigma_deg = max(0.5, float(sigma_deg))
    d_az = _ang_diff_deg(pointing_az_deg, source_az_deg)
    d_el = abs(pointing_el_deg - source_el_deg)
    d2 = d_az**2 + d_el**2
    return float(np.exp(-0.5 * d2 / (sigma_deg**2)))


# ============================================================
# 3) FILE DISCOVERY + CLEANING
# ============================================================

def find_first_radiometer_file(data_dir: str) -> str:
    # Search for the first usable radiometer file inside the selected folder.
    # Priority:
    #   1) *_lv1.xlsx
    #   2) any .xlsx except clean/temp files
    #   3) *_lv1.csv
    #   4) any .csv except clean files
    if not os.path.isdir(data_dir):
        raise FileNotFoundError("Selected data folder does not exist.")

    lv1_xlsx = sorted(glob.glob(os.path.join(data_dir, "*_lv1.xlsx")))
    lv1_xlsx = [p for p in lv1_xlsx if (not _is_excel_temp_file(p)) and (not p.lower().endswith("_clean.xlsx"))]
    if lv1_xlsx:
        return lv1_xlsx[0]

    any_xlsx = sorted(glob.glob(os.path.join(data_dir, "*.xlsx")))
    any_xlsx = [
        p for p in any_xlsx
        if (not _is_excel_temp_file(p))
        and (not p.lower().endswith("_clean.xlsx"))
    ]
    if any_xlsx:
        return any_xlsx[0]

    lv1_csv = sorted(glob.glob(os.path.join(data_dir, "*_lv1.csv")))
    lv1_csv = [p for p in lv1_csv if (not p.lower().endswith("_clean.csv"))]
    if lv1_csv:
        return lv1_csv[0]

    any_csv = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    any_csv = [p for p in any_csv if (not p.lower().endswith("_clean.csv"))]
    if any_csv:
        return any_csv[0]

    raise FileNotFoundError("No .xlsx or .csv files found in the selected folder.")


def load_clean_xlsx(path: str) -> DataFrame:
    # Load an already-clean Excel file and convert all non-time columns to numeric.
    if pd is None:
        raise ImportError("pandas is required to load Excel files.")

    df = pd.read_excel(path, header=0)
    df = _normalize_cols(df)

    dt_col = _find_datetime_col(df)
    df.rename(columns={dt_col: "Date/Time"}, inplace=True)

    df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
    df = df[df["Date/Time"].notna()].copy()

    for col in df.columns:
        if col != "Date/Time":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.sort_values("Date/Time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def extract_channels_from_clean(df: DataFrame) -> tuple[list[str], np.ndarray]:
    # Find frequency-channel columns in the clean dataframe.
    # Returns:
    #   - list of column names
    #   - numpy array with those frequencies as floats
    cols: list[str] = []
    freqs: list[float] = []

    for c in df.columns:
        s = str(c).strip()
        if s in ("Date/Time", "Az(deg)", "El(deg)", "TkBB(K)"):
            continue
        try:
            f = float(s)
            cols.append(s)
            freqs.append(f)
        except ValueError:
            pass

    freqs_arr = np.array(freqs, dtype=float)
    order = np.argsort(freqs_arr)
    return [cols[i] for i in order], freqs_arr[order]


def select_band(
    cols: list[str],
    freqs: np.ndarray,
    fmin: float = FREQ_MIN_GHZ,
    fmax: float = FREQ_MAX_GHZ
) -> tuple[list[str], np.ndarray]:
    # Keep only channel columns inside the desired frequency band.
    mask = (freqs >= fmin) & (freqs <= fmax)
    sel_cols = [cols[i] for i in np.where(mask)[0]]
    sel_freq = freqs[mask]
    return sel_cols, sel_freq


def _read_lv1_table_any(input_path: str, header_guess: int) -> DataFrame:
    # Read either XLSX or CSV using a guessed header row.
    if pd is None:
        raise ImportError("pandas is required.")

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".xlsx":
        df = pd.read_excel(input_path, header=header_guess)
    elif ext == ".csv":
        df = pd.read_csv(
            input_path,
            header=header_guess,
            sep=None,
            engine="python",
            encoding_errors="ignore"
        )
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return _normalize_cols(df)


def clean_lv1_to_clean_xlsx(
    input_path: str,
    output_xlsx: str,
    fmin: float = FREQ_MIN_GHZ,
    fmax: float = FREQ_MAX_GHZ
) -> None:
    # Convert a raw LV1 file into a clean Excel file.
    #
    # Main steps:
    #   1) read the original file
    #   2) locate Date/Time
    #   3) locate channel columns
    #   4) keep only 22–30 GHz
    #   5) rename channels as numeric strings like "22.000"
    if pd is None:
        raise ImportError("pandas is required to read/write files.")

    last_err: Exception | None = None
    for header_guess in (2, 0):
        try:
            df = _read_lv1_table_any(input_path, header_guess=header_guess)
            dt_col = _find_datetime_col(df)
            df.rename(columns={dt_col: "Date/Time"}, inplace=True)
            break
        except Exception as e:
            last_err = e
            df = None  # type: ignore
    else:
        raise ValueError(f"Failed to read file. Last error: {last_err}")

    # Convert Date/Time to pandas datetime and remove invalid rows.
    df["Date/Time"] = pd.to_datetime(df["Date/Time"], errors="coerce")
    df = df[df["Date/Time"].notna()].copy()

    ch_cols: list[str] = []
    ch_freqs: list[float] = []

    # Detect channel columns either as "Ch XX.XXX" or already numeric names.
    for c in df.columns:
        name = str(c).strip()

        m = CHANNEL_PATTERN.match(name)
        if m:
            f = float(m.group(1))
            if fmin <= f <= fmax:
                ch_cols.append(name)
                ch_freqs.append(f)
            continue

        if name in ("Date/Time", "Az(deg)", "El(deg)", "TkBB(K)"):
            continue
        try:
            f = float(name)
            if fmin <= f <= fmax:
                ch_cols.append(name)
                ch_freqs.append(f)
        except ValueError:
            pass

    if not ch_cols:
        raise ValueError(
            f"No channel columns found in range {fmin}-{fmax} GHz.\n"
            "Expected columns like 'Ch  22.000' or numeric headers like '22.000'."
        )

    # Sort channels by frequency so plots are ordered left-to-right.
    order = np.argsort(np.array(ch_freqs, dtype=float))
    ch_cols = [ch_cols[i] for i in order]
    ch_freqs = [ch_freqs[i] for i in order]

    # Keep only the important base columns + frequency channels.
    base_cols: list[str] = ["Date/Time"]
    for c in ["Az(deg)", "El(deg)", "TkBB(K)"]:
        if c in df.columns:
            base_cols.append(c)

    out = df[base_cols + ch_cols].copy()

    # Convert everything except Date/Time to numeric.
    for c in base_cols:
        if c != "Date/Time":
            out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ch_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # Rename channels to clean numeric strings.
    rename_map = {col: f"{freq:.3f}" for col, freq in zip(ch_cols, ch_freqs)}
    out.rename(columns=rename_map, inplace=True)

    # Drop rows where all channels are NaN.
    chan_names = list(rename_map.values())
    out = out.dropna(subset=chan_names, how="all")

    # Save output as clean Excel file.
    out.to_excel(output_xlsx, index=False)


def clean_first_file_only(data_dir: str, out_dir: str) -> tuple[str, str]:
    # Clean only the first file found in the selected data folder.
    os.makedirs(out_dir, exist_ok=True)

    first = find_first_radiometer_file(data_dir)
    base = os.path.basename(first)
    stem, _ext = os.path.splitext(base)

    out_name = f"{stem}_clean.xlsx"
    out_path = os.path.join(out_dir, out_name)

    clean_lv1_to_clean_xlsx(first, out_path)
    return first, out_path


# ============================================================
# 4) SOURCE MODEL
# ============================================================

def sample_rfi_source(rng: np.random.Generator, source_class: str) -> dict[str, Any]:
    # Generate one random synthetic RFI source.
    #
    # Each source class uses different parameter ranges:
    #   - frequency center / bandwidth
    #   - temporal activity
    #   - power
    #   - directionality / distance
    source_class = source_class.strip()

    # Generic defaults in case a class does not override all values.
    spectral_shape = "gaussian"
    modulation_scheme = "continuous"
    emission_type = "intentional"
    propagation_path = "line_of_sight"
    polarization_type = str(rng.choice(["linear-horizontal", "linear-vertical", "circular", "elliptical"]))
    licensed = True
    compliance = "unknown"

    center_ghz = 26.0
    bandwidth_mhz = 100.0
    duty_cycle = 0.3
    pulse_width_s = 1.0
    repetition_rate_hz = 0.5
    avg_power_K = 200.0
    peak_power_K = 500.0
    rfi_az_deg = float(rng.uniform(0.0, 360.0))
    rfi_el_deg = float(rng.uniform(0.0, 90.0))
    angular_sigma_deg = 12.0
    distance_km = 1.0
    antenna_gain_factor = 1.0
    polarization_factor = float(_clip(rng.normal(loc=0.72, scale=0.22), 0.08, 1.0))

    # 5G source: wide, structured, OFDM-like, bursty/moderate.
    if source_class == "5G":
        spectral_shape = str(rng.choice(["ofdm_like", "flat", "spiky"], p=[0.65, 0.20, 0.15]))
        modulation_scheme = str(rng.choice(["OFDM", "bursty-OFDM", "QAM-OFDM"], p=[0.45, 0.35, 0.20]))
        emission_type = str(rng.choice(["intentional", "spurious"], p=[0.85, 0.15]))
        propagation_path = str(rng.choice(["line_of_sight", "reflected", "scattered"], p=[0.65, 0.25, 0.10]))
        licensed = True
        compliance = str(rng.choice(["compliant", "partially-compliant", "unknown"], p=[0.70, 0.20, 0.10]))

        center_ghz = float(_clip(rng.normal(loc=27.8, scale=0.8), 23.0, 29.5))
        bandwidth_mhz = float(rng.choice([50, 100, 200, 400]))
        duty_cycle = float(_clip(rng.normal(loc=0.28, scale=0.14), 0.03, 0.95))
        pulse_width_s = float(_clip(rng.lognormal(mean=np.log(0.8), sigma=0.7), 0.05, 8.0))
        repetition_rate_hz = float(_clip(rng.normal(loc=0.4, scale=0.22), 0.02, 3.0))
        avg_power_K = float(_clip(rng.normal(loc=260.0, scale=120.0), 40.0, 1500.0))
        peak_power_K = float(_clip(avg_power_K * rng.uniform(1.4, 3.5), avg_power_K, 3500.0))
        angular_sigma_deg = float(_clip(rng.normal(loc=12.0, scale=5.0), 2.0, 40.0))
        distance_km = float(_clip(rng.lognormal(mean=np.log(1.2), sigma=0.9), 0.05, 25.0))
        antenna_gain_factor = float(_clip(rng.normal(loc=1.0, scale=0.35), 0.2, 2.2))

    # Radar: narrow / pulsed / high peak power / directional.
    elif source_class == "Radar Systems":
        spectral_shape = str(rng.choice(["spiky", "gaussian"], p=[0.65, 0.35]))
        modulation_scheme = str(rng.choice(["pulsed", "pulse-train", "chirp-like"], p=[0.45, 0.40, 0.15]))
        emission_type = "intentional"
        propagation_path = str(rng.choice(["line_of_sight", "reflected"], p=[0.78, 0.22]))
        licensed = True
        compliance = str(rng.choice(["compliant", "unknown", "partially-compliant"], p=[0.55, 0.25, 0.20]))

        center_ghz = float(_clip(rng.normal(loc=25.5, scale=2.0), 22.1, 29.8))
        bandwidth_mhz = float(rng.choice([10, 20, 40, 80, 120]))
        duty_cycle = float(_clip(rng.normal(loc=0.10, scale=0.08), 0.005, 0.50))
        pulse_width_s = float(_clip(rng.lognormal(mean=np.log(0.08), sigma=0.9), 0.005, 1.0))
        repetition_rate_hz = float(_clip(rng.normal(loc=4.0, scale=2.5), 0.2, 20.0))
        avg_power_K = float(_clip(rng.normal(loc=180.0, scale=100.0), 20.0, 1200.0))
        peak_power_K = float(_clip(avg_power_K * rng.uniform(4.0, 12.0), avg_power_K, 5000.0))
        angular_sigma_deg = float(_clip(rng.normal(loc=5.0, scale=2.5), 0.8, 12.0))
        distance_km = float(_clip(rng.lognormal(mean=np.log(3.0), sigma=0.9), 0.2, 60.0))
        antenna_gain_factor = float(_clip(rng.normal(loc=1.35, scale=0.45), 0.3, 3.0))

    # Broadcast: more stable, almost continuous, flatter spectrum.
    elif source_class == "Broadcast Services":
        spectral_shape = str(rng.choice(["flat", "gaussian"], p=[0.65, 0.35]))
        modulation_scheme = str(rng.choice(["continuous", "am-like", "fm-like"], p=[0.60, 0.20, 0.20]))
        emission_type = str(rng.choice(["intentional", "spurious"], p=[0.75, 0.25]))
        propagation_path = str(rng.choice(["line_of_sight", "reflected", "scattered"], p=[0.50, 0.30, 0.20]))
        licensed = True
        compliance = str(rng.choice(["compliant", "partially-compliant", "unknown"], p=[0.65, 0.20, 0.15]))

        center_ghz = float(_clip(rng.normal(loc=24.5, scale=2.2), 22.0, 30.0))
        bandwidth_mhz = float(rng.choice([6, 8, 20, 40, 80]))
        duty_cycle = float(_clip(rng.normal(loc=0.85, scale=0.12), 0.20, 1.00))
        pulse_width_s = float(_clip(rng.lognormal(mean=np.log(2.5), sigma=0.5), 0.2, 15.0))
        repetition_rate_hz = float(_clip(rng.normal(loc=0.15, scale=0.08), 0.01, 1.0))
        avg_power_K = float(_clip(rng.normal(loc=140.0, scale=70.0), 15.0, 900.0))
        peak_power_K = float(_clip(avg_power_K * rng.uniform(1.1, 1.8), avg_power_K, 1800.0))
        angular_sigma_deg = float(_clip(rng.normal(loc=18.0, scale=6.0), 4.0, 45.0))
        distance_km = float(_clip(rng.lognormal(mean=np.log(6.0), sigma=1.0), 0.5, 120.0))
        antenna_gain_factor = float(_clip(rng.normal(loc=0.95, scale=0.25), 0.2, 1.8))

    # ISM: can be bursty / nearby / irregular.
    elif source_class == "ISM Equipment":
        spectral_shape = str(rng.choice(["flat", "spiky", "gaussian"], p=[0.45, 0.35, 0.20]))
        modulation_scheme = str(rng.choice(["continuous", "bursty", "frequency-hopping-like"], p=[0.30, 0.45, 0.25]))
        emission_type = str(rng.choice(["intentional", "spurious"], p=[0.60, 0.40]))
        propagation_path = str(rng.choice(["line_of_sight", "reflected", "scattered"], p=[0.45, 0.35, 0.20]))
        licensed = False
        compliance = str(rng.choice(["unknown", "partially-compliant", "compliant"], p=[0.45, 0.35, 0.20]))

        center_ghz = float(_clip(rng.normal(loc=24.125, scale=0.35), 22.0, 30.0))
        bandwidth_mhz = float(rng.choice([20, 40, 80, 100, 200]))
        duty_cycle = float(_clip(rng.normal(loc=0.50, scale=0.22), 0.05, 1.00))
        pulse_width_s = float(_clip(rng.lognormal(mean=np.log(0.35), sigma=0.8), 0.02, 6.0))
        repetition_rate_hz = float(_clip(rng.normal(loc=1.2, scale=0.9), 0.05, 8.0))
        avg_power_K = float(_clip(rng.normal(loc=240.0, scale=140.0), 20.0, 1800.0))
        peak_power_K = float(_clip(avg_power_K * rng.uniform(1.5, 4.5), avg_power_K, 3500.0))
        angular_sigma_deg = float(_clip(rng.normal(loc=16.0, scale=7.0), 3.0, 45.0))
        distance_km = float(_clip(rng.lognormal(mean=np.log(0.35), sigma=0.8), 0.005, 8.0))
        antenna_gain_factor = float(_clip(rng.normal(loc=1.1, scale=0.35), 0.2, 2.2))

    # Unintentional emitters: messy, broadband, irregular, switching-like.
    elif source_class == "Unintentional Emitters":
        spectral_shape = str(rng.choice(["broadband", "spiky", "gaussian"], p=[0.50, 0.35, 0.15]))
        modulation_scheme = str(rng.choice(["random-bursty", "switching-noise-like", "continuous"], p=[0.45, 0.40, 0.15]))
        emission_type = "unintentional"
        propagation_path = str(rng.choice(["scattered", "reflected", "line_of_sight"], p=[0.45, 0.35, 0.20]))
        licensed = False
        compliance = str(rng.choice(["unknown", "non-compliant", "partially-compliant"], p=[0.55, 0.20, 0.25]))

        center_ghz = float(_clip(rng.normal(loc=25.0, scale=2.3), 22.0, 30.0))
        bandwidth_mhz = float(rng.choice([100, 200, 400, 800, 1500]))
        duty_cycle = float(_clip(rng.normal(loc=0.35, scale=0.22), 0.02, 0.95))
        pulse_width_s = float(_clip(rng.lognormal(mean=np.log(0.18), sigma=1.0), 0.005, 4.0))
        repetition_rate_hz = float(_clip(rng.normal(loc=1.8, scale=1.3), 0.05, 12.0))
        avg_power_K = float(_clip(rng.normal(loc=120.0, scale=90.0), 5.0, 900.0))
        peak_power_K = float(_clip(avg_power_K * rng.uniform(1.2, 3.5), avg_power_K, 2200.0))
        angular_sigma_deg = float(_clip(rng.normal(loc=30.0, scale=10.0), 6.0, 80.0))
        distance_km = float(_clip(rng.lognormal(mean=np.log(0.12), sigma=0.9), 0.001, 3.0))
        antenna_gain_factor = float(_clip(rng.normal(loc=0.8, scale=0.25), 0.1, 1.6))

    # Derived parameters
    bandwidth_ghz = bandwidth_mhz / 1000.0
    psd_like_K_per_ghz = float(avg_power_K / max(bandwidth_ghz, 1e-6))
    protected_band_overlap = bool(
        (23.6 <= center_ghz <= 24.0)
        or (center_ghz - bandwidth_ghz / 2 < 23.8 < center_ghz + bandwidth_ghz / 2)
    )

    # Return all source parameters in one dictionary.
    return {
        "source_class": source_class,
        "center_ghz": center_ghz,
        "bandwidth_mhz": bandwidth_mhz,
        "bandwidth_ghz": bandwidth_ghz,
        "spectral_shape": spectral_shape,
        "duty_cycle": duty_cycle,
        "pulse_width_s": pulse_width_s,
        "repetition_rate_hz": repetition_rate_hz,
        "modulation_scheme": modulation_scheme,
        "peak_power_K": peak_power_K,
        "average_power_K": avg_power_K,
        "psd_like_K_per_ghz": psd_like_K_per_ghz,
        "rfi_az_deg": rfi_az_deg,
        "rfi_el_deg": rfi_el_deg,
        "angular_sigma_deg": angular_sigma_deg,
        "distance_km": distance_km,
        "antenna_gain_factor": antenna_gain_factor,
        "propagation_path": propagation_path,
        "polarization_type": polarization_type,
        "polarization_factor": polarization_factor,
        "emission_type": emission_type,
        "licensed": licensed,
        "compliance": compliance,
        "protected_band_overlap": protected_band_overlap,
    }


def build_frequency_shape(
    freqs_ghz: np.ndarray,
    center_ghz: float,
    bandwidth_ghz: float,
    spectral_shape: str,
    rng: np.random.Generator
) -> np.ndarray:
    # Build the spectral signature of the RFI source over frequency.
    freqs_ghz = np.asarray(freqs_ghz, dtype=float)
    half_bw = max(1e-9, bandwidth_ghz / 2.0)
    x = (freqs_ghz - center_ghz) / half_bw

    # Smooth bell-shaped spectrum.
    if spectral_shape == "gaussian":
        shape = np.exp(-0.5 * (x / 0.75) ** 2)

    # Mostly flat inside the band, weak leakage outside.
    elif spectral_shape == "flat":
        shape = np.where(np.abs(x) <= 1.0, 1.0, 0.03 * np.exp(-2.0 * np.abs(x)))

    # Narrow spikes / tones inside the band.
    elif spectral_shape == "spiky":
        base = np.where(np.abs(x) <= 1.0, 0.35, 0.0)
        shape = base.copy()
        idx = np.where(np.abs(x) <= 1.0)[0]
        if len(idx) > 0:
            n_spikes = int(min(len(idx), max(3, len(idx) // 3)))
            chosen = rng.choice(idx, size=n_spikes, replace=False)
            shape[chosen] += rng.uniform(0.6, 1.4, size=n_spikes)
        shape += 0.02 * np.exp(-2.0 * np.abs(x))

    # Broadband messy spectrum.
    elif spectral_shape == "broadband":
        shape = np.exp(-0.5 * (x / 1.6) ** 2) + 0.10 * rng.random(len(freqs_ghz))

    # OFDM-like block spectrum with ripple/jitter across bins.
    else:  # ofdm_like
        inband = np.abs(x) <= 1.0
        shape = np.zeros_like(freqs_ghz, dtype=float)
        idx = np.where(inband)[0]
        if len(idx) > 0:
            n_in = len(idx)
            grid = np.linspace(0.0, 1.0, n_in)
            roll = 0.3 + 0.7 * (0.5 * (1 + np.cos(np.pi * np.linspace(-1, 1, n_in))))
            ripple = np.zeros(n_in, dtype=float)
            n_tones = int(rng.integers(6, 18))
            for _ in range(n_tones):
                k = float(rng.uniform(1.0, 10.0))
                phase = float(rng.uniform(0.0, 2.0 * np.pi))
                ripple += np.sin(2.0 * np.pi * k * grid + phase)
            ripple = ripple / (np.max(np.abs(ripple)) + 1e-12)
            jitter = rng.normal(0.0, 0.15, size=n_in)
            band_profile = roll * (1.0 + 0.35 * ripple + jitter)
            band_profile = np.clip(band_profile, 0.0, None)
            shape[idx] = band_profile

        shape += 0.02 * np.exp(-0.5 * (x / 1.8) ** 2)

    # Normalize so the max spectral amplitude is 1.
    shape = np.asarray(shape, dtype=float)
    maxv = float(np.nanmax(shape)) if shape.size else 0.0
    if maxv > 0:
        shape = shape / maxv
    return shape


def build_temporal_envelope(
    t_len: int,
    dt_seconds: float,
    duty_cycle: float,
    pulse_width_s: float,
    repetition_rate_hz: float,
    average_power_K: float,
    peak_power_K: float,
    modulation_scheme: str,
    rng: np.random.Generator
) -> tuple[np.ndarray, dict[str, float]]:
    # Build the time behavior of the RFI source.
    #
    # This creates pulses / bursts / continuous-like activity depending
    # on the selected modulation scheme.
    dt_seconds = max(1e-6, float(dt_seconds))
    envelope = np.zeros(t_len, dtype=float)

    if t_len <= 0:
        return envelope, {"actual_duty_cycle": 0.0}

    pulse_len = max(1, int(round(pulse_width_s / dt_seconds)))
    if repetition_rate_hz <= 0:
        period_len = max(pulse_len + 1, t_len + 1)
    else:
        period_len = max(pulse_len, int(round((1.0 / repetition_rate_hz) / dt_seconds)))

    target_on = int(round(duty_cycle * t_len))
    mod = modulation_scheme.lower()

    # Random bursty/switching style behavior.
    if any(k in mod for k in ["bursty", "random", "switching"]):
        on_count = 0
        attempts = 0
        while on_count < target_on and attempts < 20000:
            attempts += 1
            start = int(rng.integers(0, max(1, t_len - pulse_len)))
            if not envelope[start:start + pulse_len].any():
                burst_amp = rng.uniform(average_power_K, peak_power_K)
                envelope[start:start + pulse_len] = burst_amp
                on_count += pulse_len

    # More periodic pulse-train / continuous-like behavior.
    else:
        phase0 = int(rng.integers(0, max(1, period_len)))
        for start in range(phase0, t_len, period_len):
            end = min(t_len, start + pulse_len)
            burst_amp = rng.uniform(average_power_K, peak_power_K)
            envelope[start:end] = burst_amp

        current_on = int(np.count_nonzero(envelope > 0))
        if current_on > target_on and current_on > 0:
            on_idx = np.where(envelope > 0)[0]
            keep = max(1, target_on)
            if keep < len(on_idx):
                keep_idx = rng.choice(on_idx, size=keep, replace=False)
                new_env = np.zeros_like(envelope)
                new_env[keep_idx] = envelope[keep_idx]
                envelope = new_env
        elif current_on < target_on:
            needed = target_on - current_on
            zero_idx = np.where(envelope == 0)[0]
            if len(zero_idx) > 0:
                add_idx = rng.choice(zero_idx, size=min(needed, len(zero_idx)), replace=False)
                envelope[add_idx] = rng.uniform(average_power_K * 0.7, peak_power_K, size=len(add_idx))

    # Slight smoothing so the signal is less blocky.
    if t_len >= 3:
        kernel = np.array([0.2, 0.6, 0.2])
        envelope = np.convolve(envelope, kernel, mode="same")

    # Slow fading factor to mimic load/beam/power variation over time.
    slow = np.linspace(0.0, 2.0 * np.pi, t_len)
    fade = 1.0 + 0.18 * np.sin(2.3 * slow + float(rng.uniform(0.0, 2.0 * np.pi)))
    envelope *= fade

    # Add small random fluctuations on active segments.
    active = envelope > 0
    if np.any(active):
        envelope[active] += rng.normal(0.0, 0.07 * average_power_K, size=int(np.sum(active)))
        envelope = np.clip(envelope, 0.0, peak_power_K)

    actual_duty = float(np.mean(envelope > 0))
    return envelope, {"actual_duty_cycle": actual_duty}


def add_rfi_to_df(
    df_in: DataFrame,
    channel_cols: list[str],
    channel_freqs: np.ndarray,
    source: dict[str, Any],
    pointing_az_deg: float,
    pointing_el_deg: float,
    rng: np.random.Generator
) -> tuple[DataFrame, dict[str, Any]]:
    # Apply the synthetic RFI source to the data.
    #
    # Final model:
    #   RFI(t, f) = time_envelope(t) * freq_shape(f) * total_coupling
    #
    # where total_coupling includes:
    #   - angular mismatch
    #   - distance attenuation
    #   - path factor
    #   - antenna gain
    #   - polarization factor
    df = df_in.copy()
    if "Date/Time" not in df.columns or not channel_cols:
        return df, source

    dt_seconds = _estimate_dt_seconds(df["Date/Time"])
    freqs = np.asarray(channel_freqs, dtype=float)

    # Frequency-domain behavior
    freq_shape = build_frequency_shape(
        freqs_ghz=freqs,
        center_ghz=float(source["center_ghz"]),
        bandwidth_ghz=float(source["bandwidth_ghz"]),
        spectral_shape=str(source["spectral_shape"]),
        rng=rng
    )

    # Time-domain behavior
    time_env, time_meta = build_temporal_envelope(
        t_len=len(df),
        dt_seconds=dt_seconds,
        duty_cycle=float(source["duty_cycle"]),
        pulse_width_s=float(source["pulse_width_s"]),
        repetition_rate_hz=float(source["repetition_rate_hz"]),
        average_power_K=float(source["average_power_K"]),
        peak_power_K=float(source["peak_power_K"]),
        modulation_scheme=str(source["modulation_scheme"]),
        rng=rng
    )

    # Angular coupling between source direction and radiometer direction
    angular_factor = _angular_coupling(
        pointing_az_deg=pointing_az_deg,
        pointing_el_deg=pointing_el_deg,
        source_az_deg=float(source["rfi_az_deg"]),
        source_el_deg=float(source["rfi_el_deg"]),
        sigma_deg=float(source["angular_sigma_deg"])
    )

    # Distance attenuation
    distance_km = max(0.001, float(source["distance_km"]))
    distance_factor = 1.0 / (1.0 + 0.35 * distance_km**1.15)

    # Path-dependent attenuation
    path_factor_map = {
        "line_of_sight": 1.00,
        "reflected": 0.65,
        "scattered": 0.40,
    }
    path_factor = float(path_factor_map.get(str(source["propagation_path"]), 0.6))

    antenna_gain_factor = float(source["antenna_gain_factor"])
    polarization_factor = float(source["polarization_factor"])

    # Total scaling of the source before adding it to the radiometer data
    total_coupling = angular_factor * distance_factor * path_factor * antenna_gain_factor * polarization_factor

    center_ghz = float(source["center_ghz"])
    bw_ghz = float(source["bandwidth_ghz"])
    harmonic_shape = np.zeros_like(freqs, dtype=float)

    # If the source is spurious, add extra side components / harmonics.
    if str(source["emission_type"]) == "spurious":
        harmonic_1 = np.exp(-0.5 * ((freqs - (center_ghz + 0.6 * bw_ghz)) / max(0.04, 0.25 * bw_ghz)) ** 2)
        harmonic_2 = np.exp(-0.5 * ((freqs - (center_ghz - 0.75 * bw_ghz)) / max(0.04, 0.22 * bw_ghz)) ** 2)
        harmonic_shape = harmonic_1 + 0.8 * harmonic_2
        if np.max(harmonic_shape) > 0:
            harmonic_shape = harmonic_shape / np.max(harmonic_shape)

    full_freq_shape = freq_shape + 0.18 * harmonic_shape
    if np.max(full_freq_shape) > 0:
        full_freq_shape = full_freq_shape / np.max(full_freq_shape)

    # Build the actual RFI matrix to add to the data.
    rfi_K = (time_env[:, None]) * full_freq_shape[None, :] * total_coupling

    # Add RFI to the selected frequency channels.
    X = df[channel_cols].to_numpy(float)
    df.loc[:, channel_cols] = X + rfi_K

    # Useful metadata for logging
    band_low = center_ghz - bw_ghz / 2.0
    band_high = center_ghz + bw_ghz / 2.0
    overlaps_instrument = bool((band_high >= FREQ_MIN_GHZ) and (band_low <= FREQ_MAX_GHZ))

    meta = dict(source)
    meta.update(time_meta)
    meta.update({
        "dt_seconds": dt_seconds,
        "band_low_ghz": band_low,
        "band_high_ghz": band_high,
        "angular_coupling": angular_factor,
        "distance_factor": distance_factor,
        "path_factor": path_factor,
        "total_coupling": total_coupling,
        "overlaps_instrument": overlaps_instrument,
        "pointing_az_deg": pointing_az_deg,
        "pointing_el_deg": pointing_el_deg,
    })
    return df, meta


# ============================================================
# 5) GUI APPLICATION
# ============================================================

class MP3000App:
    def __init__(self, root: tk.Tk):
        # Main window configuration
        self.root = root
        self.root.title("Synthetic RFI Generator — MP-3000 LV1")
        self.root.geometry("1220x760")

        # Create one tab for the application
        self.tab_control = ttk.Notebook(root)
        self.tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab, text="MP-3000 LV1 (22–30 GHz)")
        self.tab_control.pack(expand=1, fill="both")

        # GUI state variables
        self.data_dir = tk.StringVar(value="./data")
        self.out_dir = tk.StringVar(value="./out")

        self.plot_mode = tk.StringVar(value="frequency")
        self.az_choice = tk.StringVar(value="")
        self.el_choice = tk.StringVar(value="")
        self.freq_choice = tk.StringVar(value="22.000")

        self.add_rfi = tk.BooleanVar(value=False)
        self.rfi_source_type = tk.StringVar(value="5G")

        # Internal data containers
        self.clean_df: Optional[DataFrame] = None
        self.clean_cols: list[str] = []
        self.clean_freqs: np.ndarray = np.array([])

        # Build all GUI widgets
        self._build_ui()

    def _build_ui(self) -> None:
        # Left panel: controls
        controls = ttk.LabelFrame(self.tab, text="⚙️ Parameters")
        controls.pack(side="left", padx=10, pady=10, fill="y")

        # Data folder selector
        ttk.Label(controls, text="Data folder (xlsx/csv):").pack(pady=(6, 2))
        row1 = ttk.Frame(controls)
        row1.pack(pady=2)
        tk.Entry(row1, textvariable=self.data_dir, width=26).grid(row=0, column=0, padx=2)
        ttk.Button(row1, text="Browse", command=self._browse_data).grid(row=0, column=1, padx=2)

        # Output folder selector
        ttk.Label(controls, text="Output folder:").pack(pady=(10, 2))
        row2 = ttk.Frame(controls)
        row2.pack(pady=2)
        tk.Entry(row2, textvariable=self.out_dir, width=26).grid(row=0, column=0, padx=2)
        ttk.Button(row2, text="Browse", command=self._browse_out).grid(row=0, column=1, padx=2)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)

        # Preprocess button
        ttk.Button(
            controls,
            text="Preprocess (clean FIRST file only)",
            command=self.preprocess
        ).pack(pady=6)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)

        # Plot mode controls
        ttk.Label(controls, text="Plot controls (clean data)", font=("Segoe UI", 9, "bold")).pack(pady=(4, 2))

        mode_frame = ttk.Frame(controls)
        mode_frame.pack(pady=2, fill="x")
        ttk.Radiobutton(mode_frame, text="Frequency", variable=self.plot_mode, value="frequency").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Time", variable=self.plot_mode, value="time").pack(anchor="w")
        ttk.Radiobutton(mode_frame, text="Both (Frequency + Time)", variable=self.plot_mode, value="both").pack(anchor="w")

        # Direction filter
        ttk.Label(controls, text="Az(deg):").pack(pady=(6, 2))
        self.az_combo = ttk.Combobox(controls, textvariable=self.az_choice, width=22, state="readonly")
        self.az_combo.pack()

        ttk.Label(controls, text="El(deg):").pack(pady=(6, 2))
        self.el_combo = ttk.Combobox(controls, textvariable=self.el_choice, width=22, state="readonly")
        self.el_combo.pack()

        # Frequency selector for time plot
        ttk.Label(controls, text="Freq (GHz) for Time plot:").pack(pady=(8, 2))
        self.freq_combo = ttk.Combobox(controls, textvariable=self.freq_choice, width=22, state="readonly")
        self.freq_combo.pack()

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)

        # Optional synthetic RFI
        ttk.Label(controls, text="RFI (plot only)", font=("Segoe UI", 9, "bold")).pack(pady=(2, 2))
        ttk.Checkbutton(controls, text="Add RFI", variable=self.add_rfi).pack(anchor="w")

        ttk.Label(controls, text="RFI Source Type:").pack(pady=(6, 2))
        self.rfi_source_combo = ttk.Combobox(
            controls,
            textvariable=self.rfi_source_type,
            width=22,
            state="readonly",
            values=RFI_SOURCE_OPTIONS
        )
        self.rfi_source_combo.pack()

        # Plot button
        ttk.Button(controls, text="Plot (selected mode)", command=self.plot_selected).pack(pady=10)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)

        # Save current plot
        ttk.Button(controls, text="Save Plot (PNG 300 DPI)", command=self.save_plot).pack(pady=2)

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=8)

        # Log box
        ttk.Label(controls, text="Log:").pack(pady=(2, 2))
        self.log = tk.Text(controls, width=42, height=18)
        self.log.pack(padx=4, pady=4)
        self.log.insert("end", "Ready.\n")

        # Right panel: matplotlib plot area
        plot_frame = ttk.Frame(self.tab)
        plot_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.fig, ax = plt.subplots(1, 1, figsize=(9.5, 6.0))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        ax.set_title("Plot will appear here")
        ax.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()

    def _log_add(self, msg: str) -> None:
        # Append text to the GUI log window.
        self.log.insert("end", msg)
        self.log.see("end")

    def _browse_data(self) -> None:
        # Ask the user to select the input data folder.
        p = filedialog.askdirectory()
        if p:
            self.data_dir.set(p)

    def _browse_out(self) -> None:
        # Ask the user to select the output folder.
        p = filedialog.askdirectory()
        if p:
            self.out_dir.set(p)

    def _populate_direction_and_freq_controls(self) -> None:
        # After a clean file is loaded, populate all combo boxes:
        #   - available Az values
        #   - available El values
        #   - available frequency channels
        if self.clean_df is None:
            return

        df = self.clean_df

        az_values = sorted(df["Az(deg)"].dropna().unique().tolist()) if "Az(deg)" in df.columns else []
        el_values = sorted(df["El(deg)"].dropna().unique().tolist()) if "El(deg)" in df.columns else []

        az_str = [f"{v:.6g}" for v in az_values] if az_values else ["(missing)"]
        el_str = [f"{v:.6g}" for v in el_values] if el_values else ["(missing)"]

        self.az_combo["values"] = az_str
        self.el_combo["values"] = el_str

        if not self.az_choice.get() and az_str:
            self.az_choice.set(az_str[0])
        if not self.el_choice.get() and el_str:
            self.el_choice.set(el_str[0])

        cols, freqs = extract_channels_from_clean(df)
        self.clean_cols, self.clean_freqs = select_band(cols, freqs, FREQ_MIN_GHZ, FREQ_MAX_GHZ)

        self.freq_combo["values"] = self.clean_cols
        if self.clean_cols and (self.freq_choice.get() not in self.clean_cols):
            self.freq_choice.set(self.clean_cols[0])

    def _filter_by_direction(self, df: DataFrame) -> DataFrame:
        # Keep only rows that match the selected Az/El.
        if pd is None:
            return df
        out = df.copy()

        if "Az(deg)" in out.columns and self.az_choice.get() and self.az_choice.get() != "(missing)":
            az = float(self.az_choice.get())
            az_col = pd.to_numeric(out["Az(deg)"], errors="coerce").to_numpy()
            mask = np.isfinite(az_col) & np.isclose(az_col, az, rtol=0, atol=DIRECTION_ATOL_DEG)
            out = out.loc[mask]

        if "El(deg)" in out.columns and self.el_choice.get() and self.el_choice.get() != "(missing)":
            el = float(self.el_choice.get())
            el_col = pd.to_numeric(out["El(deg)"], errors="coerce").to_numpy()
            mask = np.isfinite(el_col) & np.isclose(el_col, el, rtol=0, atol=DIRECTION_ATOL_DEG)
            out = out.loc[mask]

        return out

    def _apply_optional_rfi_for_plot(self, df_dir: DataFrame) -> DataFrame:
        # If the user enabled "Add RFI", generate one synthetic source
        # and apply it only to the plotted dataframe copy.
        if not self.add_rfi.get():
            return df_dir
        if not self.clean_cols:
            return df_dir

        # Create a seed so the exact generated source can be logged.
        seed_rng = np.random.default_rng()
        seed_used = int(seed_rng.integers(0, 2**31 - 1))
        rng = np.random.default_rng(seed_used)

        # Read the selected radiometer pointing
        pointing_az = _safe_float(self.az_choice.get(), 0.0) if self.az_choice.get() != "(missing)" else 0.0
        pointing_el = _safe_float(self.el_choice.get(), 0.0) if self.el_choice.get() != "(missing)" else 0.0

        # Sample a synthetic source according to the chosen source class
        source_class = self.rfi_source_type.get().strip()
        source = sample_rfi_source(rng, source_class)

        # Apply RFI to the filtered data copy
        df_rfi, meta = add_rfi_to_df(
            df_in=df_dir,
            channel_cols=self.clean_cols,
            channel_freqs=self.clean_freqs,
            source=source,
            pointing_az_deg=pointing_az,
            pointing_el_deg=pointing_el,
            rng=rng
        )

        # Write all generated source info in the log
        self._log_add(
            f"Add RFI ({meta['source_class']}):\n"
            f"  seed={seed_used}\n"
            f"  emission_type={meta['emission_type']}\n"
            f"  modulation={meta['modulation_scheme']}\n"
            f"  spectral_shape={meta['spectral_shape']}\n"
            f"  fc={meta['center_ghz']:.3f} GHz\n"
            f"  BW={meta['bandwidth_mhz']:.0f} MHz ({meta['band_low_ghz']:.3f}–{meta['band_high_ghz']:.3f} GHz)\n"
            f"  duty(target)={meta['duty_cycle']:.2f}, duty(actual)={meta['actual_duty_cycle']:.2f}\n"
            f"  pulse_width={meta['pulse_width_s']:.3f} s, repetition_rate={meta['repetition_rate_hz']:.2f} Hz\n"
            f"  avg_power={meta['average_power_K']:.1f} K, peak_power={meta['peak_power_K']:.1f} K\n"
            f"  PSD-like={meta['psd_like_K_per_ghz']:.1f} K/GHz\n"
            f"  source_az={meta['rfi_az_deg']:.1f}°, source_el={meta['rfi_el_deg']:.1f}°\n"
            f"  pointing_az={meta['pointing_az_deg']:.1f}°, pointing_el={meta['pointing_el_deg']:.1f}°\n"
            f"  angular_sigma={meta['angular_sigma_deg']:.1f}°, distance={meta['distance_km']:.3f} km\n"
            f"  propagation={meta['propagation_path']}, antenna_gain_factor={meta['antenna_gain_factor']:.2f}\n"
            f"  polarization={meta['polarization_type']}, polarization_factor={meta['polarization_factor']:.2f}\n"
            f"  angular_coupling={meta['angular_coupling']:.3f}, total_coupling={meta['total_coupling']:.3f}\n"
            f"  licensed={meta['licensed']}, compliance={meta['compliance']}\n"
            f"  protected_band_overlap={meta['protected_band_overlap']}\n"
            f"  overlaps_22_30GHz={meta['overlaps_instrument']}\n\n"
        )

        return df_rfi

    def preprocess(self) -> None:
        # Clean the first raw radiometer file found and auto-load it.
        if not require_pandas():
            return

        data_dir = self.data_dir.get().strip()
        out_dir = self.out_dir.get().strip()

        try:
            in_path, clean_path = clean_first_file_only(data_dir, out_dir)

            self._log_add(
                "Preprocess done ✅ (cleaned FIRST file only)\n"
                f"Input file:\n{in_path}\n"
                f"Output clean:\n{clean_path}\n\n"
            )

            self.clean_df = load_clean_xlsx(clean_path)
            self._populate_direction_and_freq_controls()
            self.plot_selected()

        except Exception as e:
            messagebox.showerror("Preprocess error", str(e))

    def plot_selected(self) -> None:
        # Main plotting function.
        #
        # Steps:
        #   1) verify clean data exists
        #   2) filter by Az/El
        #   3) optionally add synthetic RFI
        #   4) draw frequency / time / both plots
        if self.clean_df is None:
            messagebox.showinfo("No clean data", "Run Preprocess first to create/load *_clean.xlsx.")
            return

        df_dir = self._filter_by_direction(self.clean_df)

        if getattr(df_dir, "empty", False):
            messagebox.showinfo("No data", "No rows found for that Az/El direction.")
            return

        if not self.clean_cols:
            messagebox.showinfo("No channels", "No 22–30 GHz channels found in this clean file.")
            return

        df_plot = self._apply_optional_rfi_for_plot(df_dir)

        mode = self.plot_mode.get().strip().lower()
        self.fig.clf()

        suffix = ""
        if self.add_rfi.get():
            suffix = f" ({self.rfi_source_type.get()})"

        def draw_frequency(ax):
            # Frequency plot = average over time for each frequency channel
            X = df_plot[self.clean_cols].to_numpy(float)
            y = np.nanmean(X, axis=0)
            ax.plot(self.clean_freqs, y, marker="o")
            ax.set_title("Frequency plot — mean over time" + suffix)
            ax.set_xlabel("Frequency (GHz)")
            ax.set_ylabel("Brightness Temperature (K)")
            ax.grid(True)

        def draw_time(ax) -> bool:
            # Time plot = one selected frequency channel versus Date/Time
            fcol = self.freq_choice.get().strip()
            if fcol not in df_plot.columns:
                messagebox.showerror("Missing column", f"Frequency column not found: {fcol}")
                return False
            t = df_plot["Date/Time"]
            y = df_plot[fcol].to_numpy(float)
            ax.plot(t, y, marker="o", linewidth=1.5)
            ax.set_title(f"Time plot — {fcol} GHz" + suffix)
            ax.set_xlabel("Time")
            ax.set_ylabel("Brightness Temperature (K)")
            ax.grid(True)
            return True

        if mode == "frequency":
            ax = self.fig.add_subplot(111)
            draw_frequency(ax)
        elif mode == "time":
            ax = self.fig.add_subplot(111)
            if not draw_time(ax):
                return
            self.fig.autofmt_xdate()
        elif mode == "both":
            ax1 = self.fig.add_subplot(211)
            draw_frequency(ax1)
            ax2 = self.fig.add_subplot(212)
            if not draw_time(ax2):
                return
            self.fig.autofmt_xdate()
        else:
            messagebox.showerror("Mode error", "plot_mode must be 'frequency', 'time', or 'both'.")
            return

        self.fig.tight_layout()
        self.canvas.draw()

    def save_plot(self) -> None:
        # Save the currently displayed matplotlib figure as PNG.
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            title="Save plot (PNG 300 DPI)"
        )
        if not path:
            return

        try:
            self.fig.savefig(path, dpi=300, bbox_inches="tight")
            messagebox.showinfo("Saved", f"Saved plot (300 DPI):\n{path}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))


# ============================================================
# 6) MAIN
# ============================================================

if __name__ == "__main__":
    # Start the Tkinter application
    root = tk.Tk()
    app = MP3000App(root)
    root.mainloop()