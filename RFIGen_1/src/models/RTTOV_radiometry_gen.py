from __future__ import annotations

"""
Synthetic Level-1 data generator for a Radiometrics MP-3000A radiometer.

IMPORTANT:
- This is NOT the real RTTOV model.
- It generates a "RTTOV-like" approximation of Level-1 brightness temperatures (Tb)
  by channel, using a simplified atmospheric emission/absorption model inspired by the
  physics behind microwave radiometry.
- If you need true RTTOV outputs, you must install RTTOV itself, use the proper
  coefficient files, and call its interface directly.

What this script creates:
- A CSV file with Level-1 style data containing:
    record_no, datetime_utc, record_type, channel_mhz, frequency_ghz,
    elevation_deg, azimuth_deg, tb_k, tamb_c, rh_pct, pressure_hpa, rain_flag
- Surface meteorology records (record type 41)
- Sky brightness temperature records (record type 51)

Simplified physical idea behind the model:
- K-band (22-30 GHz): mainly sensitive to water vapor and cloud liquid water
- V-band (51-59 GHz): mainly sensitive to atmospheric temperature through oxygen absorption
- The script approximates brightness temperature as:
    Tb = trans * T_bg + (1 - trans) * T_eff + cloud_term + noise

Quick start:
    python mp3000a_level1_sintetico.py

Choose a custom output file:
    python mp3000a_level1_sintetico.py --output mp3000a_lv1.csv

Generate 24 hours with a 30-second time step:
    python mp3000a_level1_sintetico.py --hours 24 --step-seconds 30
"""

# ==========================================================
# PART 1 - Imports
# ----------------------------------------------------------
# We import only standard Python modules so the script can
# run without installing extra packages.
# ==========================================================

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ==========================================================
# PART 2 - MP-3000A channel definition
# ----------------------------------------------------------
# These are the microwave frequencies used by the synthetic
# Level-1 generator.
#
# We use a practical set of K-band and V-band channels that
# matches the MP-3000A style described in the instrument
# documentation.
# ==========================================================

K_BAND_CHANNELS_GHZ = [
    22.234,
    22.500,
    23.034,
    23.834,
    25.000,
    26.234,
    28.000,
    30.000,
]

V_BAND_CHANNELS_GHZ = [
    51.248,
    51.760,
    52.280,
    52.804,
    53.336,
    53.848,
    54.400,
    54.940,
    55.500,
    56.020,
    56.660,
    57.288,
    57.964,
    58.800,
]

ALL_CHANNELS_GHZ = K_BAND_CHANNELS_GHZ + V_BAND_CHANNELS_GHZ

# Cosmic background temperature used as a simple background term.
T_CMB_K = 2.7


# ==========================================================
# PART 3 - Data containers
# ----------------------------------------------------------
# These small data classes make the code easier to read.
#
# SurfaceMet stores surface meteorology.
# AtmosphereState stores the simplified atmospheric state
# used to compute synthetic Tb values.
# ==========================================================

@dataclass
class SurfaceMet:
    tamb_c: float
    rh_pct: float
    pressure_hpa: float
    rain_flag: int


@dataclass
class AtmosphereState:
    surface_temp_k: float
    vapor_scale: float
    liquid_scale: float
    lapse_rate_k_per_km: float
    inversion_strength_k: float


# ==========================================================
# PART 4 - Small math helper functions
# ----------------------------------------------------------
# These utility functions support the synthetic radiative
# calculations.
# ==========================================================

def clamp(value: float, vmin: float, vmax: float) -> float:
    """Limit a value to the interval [vmin, vmax]."""
    return max(vmin, min(value, vmax))


def gaussian(x: float, mu: float, sigma: float) -> float:
    """Simple Gaussian shape used to approximate spectral sensitivity."""
    if sigma <= 0:
        return 0.0
    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z)


def secant_elevation_model(elevation_deg: float) -> float:
    """
    Approximate how the atmospheric path length changes with elevation.

    Zenith (90° elevation) gives path factor ~1.
    Lower elevation angles increase the optical path.
    """
    zenith_angle_deg = 90.0 - elevation_deg
    zenith_angle_deg = clamp(zenith_angle_deg, 0.0, 75.0)
    cosz = math.cos(math.radians(zenith_angle_deg))
    return 1.0 / max(cosz, 0.25)


# ==========================================================
# PART 5 - Effective atmospheric temperature
# ----------------------------------------------------------
# RTTOV computes radiances using detailed atmospheric physics.
# This script does not do that exactly.
#
# Instead, we estimate a simplified "effective temperature"
# for each channel.
#
# K-band channels are made more sensitive to lower, moist layers.
# V-band channels are made more sensitive to the thermal structure
# associated with oxygen absorption around 57 GHz.
# ==========================================================

def effective_temperature_k(channel_ghz: float, state: AtmosphereState) -> float:
    if channel_ghz < 40.0:
        base = state.surface_temp_k - (3.5 + 8.0 * gaussian(channel_ghz, 22.235, 0.8))
        inversion = 0.35 * state.inversion_strength_k
        return base + inversion

    line_strength = gaussian(channel_ghz, 57.0, 2.7)
    base = state.surface_temp_k - (8.0 + 18.0 * line_strength)
    inversion = 0.55 * state.inversion_strength_k * (0.5 + line_strength)
    lapse_term = -2.5 * (state.lapse_rate_k_per_km - 6.5) * line_strength
    return base + inversion + lapse_term


# ==========================================================
# PART 6 - Synthetic optical depth
# ----------------------------------------------------------
# Optical depth controls how much the atmosphere absorbs and
# emits along the line of sight.
#
# Here we approximate it using:
# - water vapor contribution in K-band near 22.235 GHz
# - oxygen contribution in V-band near 57 GHz
# - cloud liquid water contribution in both bands
# ==========================================================

def optical_depth(channel_ghz: float, state: AtmosphereState, path_factor: float) -> float:
    tau = 0.01

    if channel_ghz < 40.0:
        water_line = 1.8 * gaussian(channel_ghz, 22.235, 0.55)
        water_wing = 0.45 * gaussian(channel_ghz, 24.0, 2.2)
        continuum = 0.06 + 0.015 * (channel_ghz - 22.0)
        tau += state.vapor_scale * (water_line + water_wing + continuum)
        tau += 0.35 * state.liquid_scale
    else:
        oxygen_complex = 0.15 + 2.8 * gaussian(channel_ghz, 57.0, 2.1)
        wing = 0.25 * gaussian(channel_ghz, 54.0, 3.0)
        tau += oxygen_complex + wing
        tau += 0.12 * state.vapor_scale
        tau += 0.18 * state.liquid_scale

    return tau * path_factor


# ==========================================================
# PART 7 - Cloud liquid water emission term
# ----------------------------------------------------------
# This is a simple extra term that raises brightness temperature
# when cloud liquid water is present.
# ==========================================================

def cloud_emission_term(channel_ghz: float, state: AtmosphereState) -> float:
    if state.liquid_scale <= 0:
        return 0.0

    if channel_ghz < 40.0:
        factor = 2.0 + 4.0 * gaussian(channel_ghz, 30.0, 4.0)
    else:
        factor = 1.0 + 2.0 * gaussian(channel_ghz, 57.0, 3.0)

    return factor * state.liquid_scale


# ==========================================================
# PART 8 - Final synthetic brightness temperature model
# ----------------------------------------------------------
# This function combines everything to generate one synthetic
# brightness temperature value.
#
# It uses a very simple radiative-transfer-like relationship:
#     Tb = trans * T_CMB + (1 - trans) * T_eff + cloud_term + noise
# ==========================================================

def synthetic_tb(channel_ghz: float, state: AtmosphereState, elevation_deg: float, rng: random.Random) -> float:
    path_factor = secant_elevation_model(elevation_deg)
    tau = optical_depth(channel_ghz, state, path_factor)
    trans = math.exp(-tau)
    t_eff = effective_temperature_k(channel_ghz, state)
    cloud_term = cloud_emission_term(channel_ghz, state)

    tb = trans * T_CMB_K + (1.0 - trans) * t_eff + cloud_term

    # Small instrument-like random noise.
    noise_std = 0.18 if channel_ghz < 40.0 else 0.12
    tb += rng.gauss(0.0, noise_std)

    return clamp(tb, 2.7, 400.0)


# ==========================================================
# PART 9 - Synthetic time-varying surface meteorology
# ----------------------------------------------------------
# We create a simple diurnal cycle for:
# - ambient temperature
# - relative humidity
# - pressure
# - rain flag
#
# This gives the output file realistic temporal variation.
# ==========================================================

def build_surface_met(t: datetime, rng: random.Random) -> SurfaceMet:
    hod = t.hour + t.minute / 60.0 + t.second / 3600.0

    tamb_c = 25.0 + 3.5 * math.sin(2.0 * math.pi * (hod - 14.0) / 24.0)
    tamb_c += rng.gauss(0.0, 0.15)

    rh_pct = 78.0 - 14.0 * math.sin(2.0 * math.pi * (hod - 14.0) / 24.0)
    rh_pct += rng.gauss(0.0, 1.2)
    rh_pct = clamp(rh_pct, 35.0, 100.0)

    pressure_hpa = 1012.0 + 1.8 * math.sin(2.0 * math.pi * hod / 12.0)
    pressure_hpa += rng.gauss(0.0, 0.25)

    rain_flag = 1 if (18.0 <= hod <= 19.5 and rh_pct > 85.0) else 0

    return SurfaceMet(
        tamb_c=tamb_c,
        rh_pct=rh_pct,
        pressure_hpa=pressure_hpa,
        rain_flag=rain_flag,
    )


# ==========================================================
# PART 10 - Synthetic atmospheric state
# ----------------------------------------------------------
# From the surface meteorology, we create a simplified
# atmospheric description:
# - surface temperature
# - vapor amount
# - cloud liquid amount
# - lapse rate
# - inversion strength
# ==========================================================

def build_atmosphere_state(met: SurfaceMet, t: datetime, rng: random.Random) -> AtmosphereState:
    hod = t.hour + t.minute / 60.0 + t.second / 3600.0

    surface_temp_k = met.tamb_c + 273.15

    vapor_scale = 0.75 + 0.008 * (met.rh_pct - 50.0)
    vapor_scale += 0.12 * math.exp(-0.5 * ((hod - 17.0) / 2.5) ** 2)
    vapor_scale = clamp(vapor_scale, 0.35, 1.60)

    liquid_scale = 0.0
    if met.rain_flag:
        liquid_scale = 2.8 + rng.uniform(0.0, 0.7)
    elif met.rh_pct > 92.0:
        liquid_scale = 0.35 + rng.uniform(0.0, 0.15)

    lapse_rate = 6.2 + 0.6 * math.sin(2.0 * math.pi * (hod - 9.0) / 24.0)
    lapse_rate += rng.gauss(0.0, 0.08)

    inversion_strength = 0.0
    if 2.0 <= hod <= 8.0:
        inversion_strength = 2.5 + 1.3 * math.cos(2.0 * math.pi * (hod - 5.0) / 6.0)
        inversion_strength = max(inversion_strength, 0.0)

    return AtmosphereState(
        surface_temp_k=surface_temp_k,
        vapor_scale=vapor_scale,
        liquid_scale=liquid_scale,
        lapse_rate_k_per_km=lapse_rate,
        inversion_strength_k=inversion_strength,
    )


# ==========================================================
# PART 11 - CSV writing
# ----------------------------------------------------------
# This is where the script creates the final Level-1 style file.
#
# For each time step, it writes:
# - one meteorology record (type 41)
# - one brightness temperature record (type 51) per channel
# ==========================================================

def channel_to_mhz(freq_ghz: float) -> int:
    return int(round(freq_ghz * 1000.0))


def write_level1_csv(
    output_path: Path,
    start_time: datetime,
    hours: float,
    step_seconds: int,
    scan_positions: list[tuple[float, float]],
    seed: int,
) -> None:
    rng = random.Random(seed)

    end_time = start_time + timedelta(hours=hours)
    current = start_time
    record_no = 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "record_no",
            "datetime_utc",
            "record_type",
            "channel_mhz",
            "frequency_ghz",
            "elevation_deg",
            "azimuth_deg",
            "tb_k",
            "tamb_c",
            "rh_pct",
            "pressure_hpa",
            "rain_flag",
        ])

        while current < end_time:
            met = build_surface_met(current, rng)
            state = build_atmosphere_state(met, current, rng)
            dt_str = current.strftime("%m/%d/%Y %H:%M:%S")

            # Surface met record.
            writer.writerow([
                record_no,
                dt_str,
                41,
                "",
                "",
                "",
                "",
                "",
                round(met.tamb_c, 3),
                round(met.rh_pct, 3),
                round(met.pressure_hpa, 3),
                met.rain_flag,
            ])
            record_no += 1

            # Brightness temperature records for every requested azimuth-elevation direction.
            for azimuth_deg, elevation_deg in scan_positions:
                for freq_ghz in ALL_CHANNELS_GHZ:
                    tb_k = synthetic_tb(freq_ghz, state, elevation_deg, rng)
                    writer.writerow([
                        record_no,
                        dt_str,
                        51,
                        channel_to_mhz(freq_ghz),
                        f"{freq_ghz:.3f}",
                        f"{elevation_deg:.2f}",
                        f"{azimuth_deg:.2f}",
                        f"{tb_k:.4f}",
                        round(met.tamb_c, 3),
                        round(met.rh_pct, 3),
                        round(met.pressure_hpa, 3),
                        met.rain_flag,
                    ])
                    record_no += 1

            current += timedelta(seconds=step_seconds)


# ==========================================================
# PART 12 - Command-line arguments
# ----------------------------------------------------------
# This section lets the user control the script from the terminal.
#
# You can change:
# - output file name
# - number of hours
# - time step
# - random seed
# - start time
#
# The scan directions are now defined inside main() using the
# 9 requested Az-El directions.
# ==========================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic MP-3000A Level-1 style data."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="mp3000a_lv1_sintetico.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--hours",
        type=float,
        default=6.0,
        help="Number of hours to simulate.",
    )
    parser.add_argument(
        "--step-seconds",
        type=int,
        default=60,
        help="Time step between samples in seconds.",
    )
    parser.add_argument(
        "--elevation-deg",
        type=float,
        default=90.0,
        help="Observation elevation. 90 = zenith.",
    )
    parser.add_argument(
        "--azimuth-deg",
        type=float,
        default=0.0,
        help="Observation azimuth.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--start-utc",
        type=str,
        default="",
        help="UTC start time in YYYY-mm-ddTHH:MM:SS format. If omitted, current UTC time is used.",
    )
    return parser.parse_args()


# ==========================================================
# PART 13 - Main function
# ----------------------------------------------------------
# This is the entry point of the script.
# It reads the user arguments, sets the start time,
# writes the CSV, and prints a summary.
# ==========================================================

def main() -> None:
    args = parse_args()

    if args.step_seconds <= 0:
        raise ValueError("--step-seconds must be greater than 0")
    if args.hours <= 0:
        raise ValueError("--hours must be greater than 0")

    if args.start_utc.strip():
        start_time = datetime.strptime(args.start_utc, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    else:
        start_time = datetime.now(timezone.utc).replace(microsecond=0)

    # Default scan pattern requested by the user.
    # Format: (azimuth_deg, elevation_deg)
    scan_positions = [
        (0.0, 20.0),
        (0.0, 90.0),
        (0.0, 160.0),
        (45.0, 20.0),
        (45.0, 160.0),
        (90.0, 20.0),
        (90.0, 160.0),
        (135.0, 20.0),
        (135.0, 160.0),
    ]

    output_path = Path(args.output)
    write_level1_csv(
        output_path=output_path,
        start_time=start_time,
        hours=args.hours,
        step_seconds=args.step_seconds,
        scan_positions=scan_positions,
        seed=args.seed,
    )

    print(f"File created: {output_path.resolve()}")
    print(f"Simulated channels: {len(ALL_CHANNELS_GHZ)}")
    print(f"Number of scan directions per time step: {len(scan_positions)}")
    print("Scan directions (Az-El):")
    for azimuth_deg, elevation_deg in scan_positions:
        print(f"  {azimuth_deg:.0f}-{elevation_deg:.0f}")
    print(f"K-band range: {K_BAND_CHANNELS_GHZ[0]:.3f} - {K_BAND_CHANNELS_GHZ[-1]:.3f} GHz")
    print(f"V-band range: {V_BAND_CHANNELS_GHZ[0]:.3f} - {V_BAND_CHANNELS_GHZ[-1]:.3f} GHz")


if __name__ == "__main__":
    main()
