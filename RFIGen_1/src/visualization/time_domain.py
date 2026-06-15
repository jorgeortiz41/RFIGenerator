"""
Time-domain visualization utilities for RFI Generator.
Provides functions to plot signals in the time domain.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def plot_time_domain(
    data: pd.DataFrame,
    channel: str = "Ch  23.834",
    title: str = "Time Domain Signal",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot time-domain signal from radiometric data."""
    fig, ax = plt.subplots(figsize=figsize)
    
    if channel in data.columns:
        ax.plot(data[channel], linewidth=1.5, alpha=0.8)
    else:
        freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
        if freq_cols:
            ax.plot(data[freq_cols[0]], linewidth=1.5, alpha=0.8)
    
    ax.set_xlabel("Time Index (samples)")
    ax.set_ylabel("Brightness Temperature (K)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_time_series_comparison(
    clean_data: pd.DataFrame,
    contaminated_data: pd.DataFrame,
    channel: str = "Ch  23.834",
    title: str = "Time Domain Comparison: Clean vs RFI-Contaminated",
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot comparison of clean and RFI-contaminated signals in time domain."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=figsize)
    
    if channel not in clean_data.columns:
        freq_cols = [col for col in clean_data.columns if str(col).startswith("Ch")]
        if not freq_cols:
            return fig
        channel = freq_cols[0]
    
    ax1.plot(clean_data[channel], linewidth=1, alpha=0.8, color='blue')
    ax1.set_ylabel("Brightness Temperature (K)")
    ax1.set_title(f"Clean Signal - {channel}")
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(contaminated_data[channel], linewidth=1, alpha=0.8, color='red')
    ax2.set_ylabel("Brightness Temperature (K)")
    ax2.set_title(f"RFI-Contaminated Signal - {channel}")
    ax2.grid(True, alpha=0.3)
    
    rfi_contribution = contaminated_data[channel] - clean_data[channel]
    ax3.plot(rfi_contribution, linewidth=1, alpha=0.8, color='green')
    ax3.set_xlabel("Time Index (samples)")
    ax3.set_ylabel("RFI Power (K)")
    ax3.set_title(f"RFI Contribution - {channel}")
    ax3.grid(True, alpha=0.3)
    
    fig.suptitle(title, fontsize=14, fontweight='bold')
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_multiple_channels_time(
    data: pd.DataFrame,
    n_channels: int = 6,
    figsize: Tuple[int, int] = (14, 8),
    save_path: Optional[str] = None
) -> Figure:
    """Plot multiple frequency channels over time."""
    freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
    
    if len(freq_cols) == 0:
        fig, ax = plt.subplots(figsize=figsize)
        return fig
    
    step = max(1, len(freq_cols) // n_channels)
    selected_channels = freq_cols[::step][:n_channels]
    
    fig, axes = plt.subplots(n_channels, 1, figsize=figsize, sharex=True)
    if n_channels == 1:
        axes = [axes]
    
    for i, (ax, channel) in enumerate(zip(axes, selected_channels)):
        ax.plot(data[channel], linewidth=1, alpha=0.8)
        ax.set_ylabel("Tb (K)")
        ax.set_title(f"Channel {i+1}: {channel}")
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel("Time Index (samples)")
    fig.suptitle("Time-Domain Signals - Multiple Channels", fontsize=14, fontweight='bold')
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig


def plot_time_statistics(
    data: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> Figure:
    """Plot time-series statistics (mean, std, min, max)."""
    freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
    
    if len(freq_cols) == 0:
        fig, ax = plt.subplots(figsize=figsize)
        return fig
    
    means = [data[col].mean() for col in freq_cols]
    stds = [data[col].std() for col in freq_cols]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    x = np.arange(len(freq_cols))
    ax.errorbar(x, means, yerr=stds, fmt='o-', capsize=5, capthick=2, alpha=0.8)
    
    ax.set_xlabel("Frequency Channel Index")
    ax.set_ylabel("Brightness Temperature (K)")
    ax.set_title("Time-Series Statistics per Channel (Mean ± Std)")
    ax.grid(True, alpha=0.3, axis='y')
    
    fig.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
    
    return fig
