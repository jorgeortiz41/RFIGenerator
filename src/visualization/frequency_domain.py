"""
Frequency-domain visualization utilities for RFI Generator.
Provides functions to plot signals in frequency and time-frequency domains.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy import signal


def plot_frequency_spectrum(
    data: pd.DataFrame,
    title: str = "Frequency Spectrum",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot frequency spectrum showing mean brightness temperature per frequency channel."""
    freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if len(freq_cols) == 0:
        fig.tight_layout()
        return fig
    
    frequencies = []
    spectrum = []
    
    for col in freq_cols:
        try:
            freq = float(str(col).split()[-1])
            frequencies.append(freq)
            spectrum.append(data[col].mean())
        except (ValueError, IndexError):
            pass
    
    if frequencies:
        ax.plot(frequencies, spectrum, marker='o', linewidth=2, markersize=6, alpha=0.8)
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Mean Brightness Temperature (K)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_spectrum_comparison(
    clean_data: pd.DataFrame,
    contaminated_data: pd.DataFrame,
    title: str = "Frequency Spectrum Comparison",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Compare frequency spectra of clean and contaminated data."""
    freq_cols = [col for col in clean_data.columns if str(col).startswith("Ch")]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if len(freq_cols) == 0:
        fig.tight_layout()
        return fig
    
    frequencies = []
    clean_spectrum = []
    contaminated_spectrum = []
    
    for col in freq_cols:
        try:
            freq = float(str(col).split()[-1])
            frequencies.append(freq)
            clean_spectrum.append(clean_data[col].mean())
            contaminated_spectrum.append(contaminated_data[col].mean())
        except (ValueError, IndexError):
            pass
    
    if frequencies:
        ax.plot(frequencies, clean_spectrum, marker='o', label='Clean', linewidth=2, alpha=0.8)
        ax.plot(frequencies, contaminated_spectrum, marker='s', label='Contaminated', linewidth=2, alpha=0.8)
        ax.fill_between(frequencies, clean_spectrum, contaminated_spectrum, alpha=0.2, color='red')
        
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Mean Brightness Temperature (K)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_spectrogram(
    data: pd.DataFrame,
    n_freq_channels: int = 20,
    title: str = "Spectrogram",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None,
    cmap: str = 'viridis'
) -> Figure:
    """Plot spectrogram showing brightness temperature as function of time and frequency."""
    freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if len(freq_cols) == 0:
        fig.tight_layout()
        return fig
    
    selected_cols = freq_cols[:min(n_freq_channels, len(freq_cols))]
    spectrogram_data = np.array([data[col].values for col in selected_cols])
    
    im = ax.imshow(
        spectrogram_data,
        aspect='auto',
        cmap=cmap,
        origin='lower',
        interpolation='bilinear'
    )
    
    ax.set_xlabel("Time Index (samples)")
    ax.set_ylabel(f"Frequency Channel Index")
    ax.set_title(title)
    
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Brightness Temperature (K)")
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_rfi_contamination_map(
    clean_data: pd.DataFrame,
    contaminated_data: pd.DataFrame,
    n_freq_channels: int = 20,
    title: str = "RFI Contamination Map",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot map showing RFI contamination as function of time and frequency."""
    freq_cols = [col for col in clean_data.columns if str(col).startswith("Ch")]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if len(freq_cols) == 0:
        fig.tight_layout()
        return fig
    
    selected_cols = freq_cols[:min(n_freq_channels, len(freq_cols))]
    
    rfi_data = np.array([
        (contaminated_data[col] - clean_data[col]).values for col in selected_cols
    ])
    
    vmax = np.abs(rfi_data).max()
    im = ax.imshow(
        rfi_data,
        aspect='auto',
        cmap='RdBu_r',
        origin='lower',
        vmin=-vmax,
        vmax=vmax,
        interpolation='bilinear'
    )
    
    ax.set_xlabel("Time Index (samples)")
    ax.set_ylabel(f"Frequency Channel Index")
    ax.set_title(title)
    
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("RFI Power (K)")
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_power_spectral_density(
    data: pd.DataFrame,
    channel: Optional[str] = None,
    title: str = "Power Spectral Density",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot power spectral density estimate using FFT."""
    freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if len(freq_cols) == 0:
        fig.tight_layout()
        return fig
    
    if channel is None:
        channel = freq_cols[0]
    
    if channel not in data.columns:
        fig.tight_layout()
        return fig
    
    signal_data = data[channel].values
    freqs, psd = signal.welch(signal_data, nperseg=1024)
    
    ax.semilogy(freqs, psd, linewidth=1.5)
    ax.set_xlabel("Normalized Frequency (0-0.5)")
    ax.set_ylabel("Power Spectral Density")
    ax.set_title(f"{title} - {channel}")
    ax.grid(True, alpha=0.3, which='both')
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig
