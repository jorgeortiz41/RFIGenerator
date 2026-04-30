import pandas as pd
import pytest

from src.models.radiometry import SyntheticRadiometerGenerator, generate_synthetic_dataset


def test_create_default_template_has_expected_rows_and_channels():
    template = SyntheticRadiometerGenerator.create_default_template(n_rows=8, n_channels=4)

    channel_columns = [column for column in template.columns if column.startswith("Ch")]

    assert len(template) == 8
    assert len(channel_columns) == 4
    assert {"Record", "Date/Time", "Az(deg)", "El(deg)", "TkBB(K)"}.issubset(
        template.columns
    )


def test_generate_dataframes_requires_template_data():
    generator = SyntheticRadiometerGenerator(template_data=None)

    with pytest.raises(ValueError, match="Template data not provided"):
        generator.generate_dataframes(1)


def test_generate_dataframes_is_reproducible_with_seed():
    template = SyntheticRadiometerGenerator.create_default_template(n_rows=6, n_channels=3)
    generator_one = SyntheticRadiometerGenerator(template, noise_std=0.5, seed=99)
    generator_two = SyntheticRadiometerGenerator(template, noise_std=0.5, seed=99)

    generated_one = generator_one.generate_dataframes(1)[0]
    generated_two = generator_two.generate_dataframes(1)[0]

    pd.testing.assert_frame_equal(generated_one, generated_two)


def test_generate_dataframes_changes_channel_values_without_changing_shape():
    template = SyntheticRadiometerGenerator.create_default_template(n_rows=6, n_channels=3)
    generator = SyntheticRadiometerGenerator(template, noise_std=0.5, seed=99)

    generated = generator.generate_dataframes(1)[0]

    assert generated.shape == template.shape
    assert not generated.filter(regex=r"^Ch").equals(template.filter(regex=r"^Ch"))


def test_generate_synthetic_dataset_returns_requested_number_of_dataframes():
    dataframes = generate_synthetic_dataset(n_dataframes=2, noise_std=0.1, seed=123)

    assert len(dataframes) == 2
    assert all(isinstance(dataframe, pd.DataFrame) for dataframe in dataframes)
