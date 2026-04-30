# signal_mixer.py
# ============================================================
# Signal Mixing Module
# Combines radiometric data with RFI signals
# ============================================================

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from .rfi_generator import sample_rfi_source, add_rfi


def generate_rfi_sources(
    n_sources: int,
    source_classes: List[str],
    rng: np.random.Generator
) -> List[Dict[str, Any]]:
    """Generate a list of RFI sources.

    Parameters
    ----------
    n_sources : int
        Number of RFI sources to generate.
    source_classes : List[str]
        List of source classes to choose from.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    List[Dict[str, Any]]
        List of RFI source dictionaries.
    """
    sources = []
    for _ in range(n_sources):
        source_class = rng.choice(source_classes) if source_classes else "unknown"
        source = sample_rfi_source(rng, source_class)
        sources.append(source)
    return sources


def add_rfi_to_dataframe(
    df: pd.DataFrame,
    sources: List[Dict[str, Any]],
    rng: np.random.Generator
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Add RFI signals to a single radiometric DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Radiometric data DataFrame.
    sources : List[Dict[str, Any]]
        List of RFI sources.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    Tuple[pd.DataFrame, List[Dict[str, Any]]]
        Updated DataFrame and list of RFI info for each source.
    """
    # Extract frequency columns
    freq_cols = [col for col in df.columns if col.startswith("Ch ")]
    if not freq_cols:
        raise ValueError("No frequency channels found in DataFrame.")

    # Extract frequencies
    freqs_ghz = np.array([float(col.split()[1]) for col in freq_cols])

    # Extract TB data
    tb_data = df[freq_cols].values.astype(float)  # shape (n_time, n_freq)

    # Extract pointing angles (assume per row, but for simplicity, use first or average)
    # For proper coupling, we need per-time coupling, but add_rfi assumes fixed.
    # To fix, compute coupling per time step.

    az_deg = df["Az(deg)"].values
    el_deg = df["El(deg)"].values

    rfi_infos = []

    for source in sources:
        # Compute coupling for each time step
        couplings = []
        for az, el in zip(az_deg, el_deg):
            coupling = angular_coupling(
                az, el,
                source["az_deg"], source["el_deg"],
                source["sigma_deg"]
            )
            couplings.append(coupling)
        coupling_array = np.array(couplings)  # shape (n_time,)

        # Modify add_rfi to handle per-time coupling
        # Instead of fixed coupling, use coupling_array

        # Time + frequency behavior
        t_env = time_envelope(
            tb_data.shape[0],
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

        # Final RFI model: t_env (n_time,) * f_shape (n_freq,) * coupling (n_time,)
        rfi_signal = t_env[:, None] * f_shape[None, :] * coupling_array[:, None]

        tb_data += rfi_signal

        rfi_infos.append({
            "center_ghz": source["center_ghz"],
            "bandwidth_ghz": source["bandwidth_ghz"],
            "power": source["peak_power_K"],
            "avg_coupling": np.mean(coupling_array)
        })

    # Update DataFrame
    df[freq_cols] = tb_data

    return df, rfi_infos


def mix_signals(
    data: List[pd.DataFrame] | pd.DataFrame,
    sources: List[Dict[str, Any]],
    rng: np.random.Generator
) -> Tuple[List[pd.DataFrame] | pd.DataFrame, List[List[Dict[str, Any]]]]:
    """Mix RFI signals into radiometric data.

    Parameters
    ----------
    data : List[pd.DataFrame] or pd.DataFrame
        Radiometric data (list of DataFrames or single DataFrame).
    sources : List[Dict[str, Any]]
        List of RFI sources.
    rng : np.random.Generator
        Random number generator.

    Returns
    -------
    Tuple[List[pd.DataFrame] or pd.DataFrame, List[List[Dict[str, Any]]]]
        Updated data and list of RFI infos per DataFrame.
    """
    if isinstance(data, pd.DataFrame):
        data = [data]

    updated_data = []
    all_infos = []

    for df in data:
        updated_df, infos = add_rfi_to_dataframe(df.copy(), sources, rng)
        updated_data.append(updated_df)
        all_infos.append(infos)

    if len(updated_data) == 1:
        return updated_data[0], all_infos
    else:
        return updated_data, all_infos


# Helper functions copied from rfi_generator for per-time coupling
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