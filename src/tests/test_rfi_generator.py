import numpy as np
import pytest

from src.models.rfi_generator import (
    add_rfi,
    angular_coupling,
    frequency_shape,
    sample_rfi_source,
    time_envelope,
)


def rfi_source(**overrides):
    source = {
        "source_class": "test",
        "center_ghz": 23.0,
        "bandwidth_ghz": 2.0,
        "avg_power_K": 2.5,
        "peak_power_K": 10.0,
        "az_deg": 0.0,
        "el_deg": 45.0,
        "sigma_deg": 5.0,
        "modulation": "continuous",
        "spectral_shape": "flat",
    }
    source.update(overrides)
    return source


def test_angular_coupling_is_one_for_matching_angles():
    assert angular_coupling(10.0, 20.0, 10.0, 20.0, 5.0) == pytest.approx(1.0)


def test_angular_coupling_decreases_with_distance():
    near = angular_coupling(0.0, 0.0, 1.0, 1.0, 5.0)
    far = angular_coupling(0.0, 0.0, 20.0, 20.0, 5.0)

    assert 0.0 <= far < near < 1.0


def test_frequency_shape_flat_marks_values_inside_bandwidth():
    freqs = np.array([21.5, 22.0, 23.0, 24.0, 24.5])

    shape = frequency_shape(freqs, center_ghz=23.0, bandwidth_ghz=2.0, shape="flat")

    np.testing.assert_array_equal(shape, np.array([0.0, 1.0, 1.0, 1.0, 0.0]))


def test_frequency_shape_gaussian_peaks_at_center():
    freqs = np.array([22.0, 23.0, 24.0])

    shape = frequency_shape(freqs, center_ghz=23.0, bandwidth_ghz=2.0, shape="gaussian")

    assert shape[1] == pytest.approx(1.0)
    assert shape[0] == pytest.approx(shape[2])
    assert shape[0] < shape[1]


def test_time_envelope_continuous_is_constant():
    rng = np.random.default_rng(123)

    envelope = time_envelope(5, 3.0, 12.0, "continuous", rng)

    np.testing.assert_array_equal(envelope, np.full(5, 3.0))


def test_time_envelope_pulsed_uses_peak_values():
    rng = np.random.default_rng(123)

    envelope = time_envelope(20, 3.0, 12.0, "pulsed", rng)

    assert np.count_nonzero(envelope == 12.0) == 2
    assert np.count_nonzero(envelope) == 2


def test_sample_rfi_source_is_reproducible_with_seed():
    source_one = sample_rfi_source(np.random.default_rng(42), "satellite")
    source_two = sample_rfi_source(np.random.default_rng(42), "satellite")

    assert source_one == source_two
    assert source_one["source_class"] == "satellite"


def test_add_rfi_returns_contaminated_data_and_metadata():
    rng = np.random.default_rng(123)
    data = np.zeros((3, 4))
    freqs = np.array([22.0, 23.0, 24.0, 25.0])

    contaminated, metadata = add_rfi(
        data,
        freqs,
        rfi_source(),
        pointing_az=0.0,
        pointing_el=45.0,
        rng=rng,
    )

    expected = np.array(
        [
            [2.5, 2.5, 2.5, 0.0],
            [2.5, 2.5, 2.5, 0.0],
            [2.5, 2.5, 2.5, 0.0],
        ]
    )
    np.testing.assert_allclose(contaminated, expected)
    assert metadata["center_ghz"] == 23.0
    assert metadata["coupling"] == pytest.approx(1.0)
