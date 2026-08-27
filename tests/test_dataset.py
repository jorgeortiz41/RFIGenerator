import numpy as np

from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset


def test_build_dataset_shapes_and_contamination():
    config = ExperimentConfig(
        seed=42,
        duration_s=5,
        sample_rate_hz=2,
        frequency_bins=32,
        rfi=[RFIConfig(type="narrowband", center_frequency_ghz=22.0, power_k=20.0)],
    )
    dataset = build_dataset(config)
    assert dataset.clean.shape == (10, 32)
    assert dataset.rfi.shape == dataset.clean.shape
    assert dataset.contaminated.shape == dataset.clean.shape
    assert np.allclose(dataset.contaminated, dataset.clean + dataset.rfi)
    assert dataset.rfi.max() > 0
