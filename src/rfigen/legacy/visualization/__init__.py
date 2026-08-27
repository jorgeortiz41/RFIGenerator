"""Legacy time- and frequency-domain plotting helpers."""

from rfigen.legacy.visualization.frequency_domain import (
    plot_frequency_spectrum,
    plot_power_spectral_density,
    plot_rfi_contamination_map,
    plot_spectrogram,
    plot_spectrum_comparison,
)
from rfigen.legacy.visualization.time_domain import (
    plot_multiple_channels_time,
    plot_time_domain,
    plot_time_series_comparison,
    plot_time_statistics,
)

__all__ = [
    "plot_frequency_spectrum",
    "plot_multiple_channels_time",
    "plot_power_spectral_density",
    "plot_rfi_contamination_map",
    "plot_spectrogram",
    "plot_spectrum_comparison",
    "plot_time_domain",
    "plot_time_series_comparison",
    "plot_time_statistics",
]
