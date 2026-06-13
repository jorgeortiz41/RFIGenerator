import pytest

from rfigen.config import ExperimentConfig, RFIConfig


def test_config_validates_k_band_limits():
    config = ExperimentConfig(frequency_start_ghz=17.0)
    with pytest.raises(ValueError):
        config.validate()


def test_config_accepts_supported_rfi():
    config = ExperimentConfig(rfi=[RFIConfig(type="narrowband", center_frequency_ghz=22.0)])
    config.validate()
