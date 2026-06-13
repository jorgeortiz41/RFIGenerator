"""Minimal Python API example."""

from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset


config = ExperimentConfig(
    seed=7,
    duration_s=30,
    sample_rate_hz=2,
    rfi=[
        RFIConfig(
            type="narrowband",
            center_frequency_ghz=22.235,
            bandwidth_mhz=30,
            power_k=18,
        )
    ],
)

dataset = build_dataset(config)
export_dataset(dataset, "outputs/python_example")
print(dataset.contaminated.shape)
