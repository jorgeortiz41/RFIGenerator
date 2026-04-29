# rfi_generator.py
# ============================================================
# Synthetic RFI Generator Module
# Standalone version extracted from GUI
# ============================================================

import numpy as np
from typing import Any, Tuple


# ============================================================
# ANGULAR COUPLING
# ============================================================

def angular_coupling(
    pointing_az_deg: float,
    pointing_el_deg: float,
    source_az_deg: float,
    source_el_deg: float,
    sigma_deg: float
) -> float:
    sigma_deg = max(0.5, float(sigma_deg))

    d_az = pointing_az_deg - source_az_deg
    d_el = pointing_el_deg - source_el_deg

    dist2 = d_az**2 + d_el**2
    return np.exp(-dist2 / (2 * sigma_deg**2))


# ============================================================
# SAMPLE RFI SOURCE
# ============================================================

def sample_rfi_source(rng: np.random.Generator, source_class: str) -> dict[str, Any]:
    
    center_ghz = rng.uniform(22, 30)
    bandwidth_ghz = rng.uniform(0.05, 1.5)

    source = {
        "source_class": source_class,
        "center_ghz": center_ghz,
        "bandwidth_ghz": bandwidth_ghz,
        "avg_power_K": rng.uniform(1, 10),
        "peak_power_K": rng.uniform(10, 50),
        "az_deg": rng.uniform(0, 360),
        "el_deg": rng.uniform(0, 90),
        "sigma_deg": rng.uniform(1, 20),
        "modulation": rng.choice(["continuous", "pulsed", "burst"]),
        "spectral_shape": rng.choice(["gaussian", "flat"])
    }

    return source


# ============================================================
# FREQUENCY SHAPE
# ============================================================

def frequency_shape(
    freqs_ghz: np.ndarray,
    center_ghz: float,
    bandwidth_ghz: float,
    shape: str
) -> np.ndarray:

    x = (freqs_ghz - center_ghz) / (bandwidth_ghz / 2)

    if shape == "gaussian":
        return np.exp(-x**2)
    else:
        return np.where(np.abs(x) <= 1, 1.0, 0.0)


# ============================================================
# TIME ENVELOPE
# ============================================================

def time_envelope(
    n_samples: int,
    avg_power: float,
    peak_power: float,
    modulation: str,
    rng: np.random.Generator
) -> np.ndarray:

    if modulation == "continuous":
        return np.full(n_samples, avg_power)

    elif modulation == "pulsed":
        env = np.zeros(n_samples)
        pulse_idx = rng.choice(n_samples, size=n_samples // 10)
        env[pulse_idx] = peak_power
        return env

    else:  # burst
        env = np.zeros(n_samples)
        start = rng.integers(0, n_samples // 2)
        end = start + rng.integers(10, n_samples // 2)
        env[start:end] = peak_power
        return env


# ============================================================
# MAIN RFI APPLICATION
# ============================================================

def add_rfi(
    data: np.ndarray,
    freqs_ghz: np.ndarray,
    source: dict[str, Any],
    pointing_az: float,
    pointing_el: float,
    rng: np.random.Generator
) -> Tuple[np.ndarray, dict]:

    n_time, n_freq = data.shape

    # Time + frequency behavior
    t_env = time_envelope(
        n_time,
        source["avg_power_K"],
        source["peak_power_K"],
        source["modulation"],
        rng
    )

    f_shape = frequency_shape(
        freqs_ghz,
        source["center_ghz"],
        source["bandwidth_ghz"],
        source["spectral_shape"]
    )

    # Angular coupling
    coupling = angular_coupling(
        pointing_az,
        pointing_el,
        source["az_deg"],
        source["el_deg"],
        source["sigma_deg"]
    )

    # Final RFI model
    rfi = t_env[:, None] * f_shape[None, :] * coupling

    contaminated = data + rfi

    return contaminated, {
        "center_ghz": source["center_ghz"],
        "bandwidth_ghz": source["bandwidth_ghz"],
        "power": source["peak_power_K"],
        "coupling": coupling
    }