"""Synthetic RFI generator for K-band radiometric data."""

from rfigen.config import ExperimentConfig, RFIConfig, RadiometryConfig, load_config
from rfigen.dataset import Dataset, build_dataset

__all__ = [
    "Dataset",
    "ExperimentConfig",
    "RFIConfig",
    "RadiometryConfig",
    "build_dataset",
    "load_config",
]

__version__ = "0.1.0"
