"""Generate synthetic radiometric data with Gaussian variations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd


class SyntheticRadiometerGenerator:
    """Generate synthetic radiometer observations based on template data."""

    def __init__(
        self,
        template_data: pd.DataFrame | None = None,
        noise_std: float = 2.0,
        seed: int | None = None,
    ):
        """Initialize the generator.

        Parameters
        ----------
        template_data : pd.DataFrame, optional
            Template dataframe to use as base. If None, creates default template.
        noise_std : float
            Standard deviation of Gaussian noise for TB values.
        seed : int, optional
            Random seed for reproducibility.
        """
        self.template_data = template_data
        self.noise_std = noise_std
        self.rng = np.random.RandomState(seed)

    def generate_dataframes(self, n: int) -> List[pd.DataFrame]:
        """Generate n synthetic dataframes with Gaussian variations.

        Parameters
        ----------
        n : int
            Number of dataframes to generate.

        Returns
        -------
        list of pd.DataFrame
            List of synthetic dataframes with Gaussian-varied TB values.
        """
        if self.template_data is None:
            raise ValueError("Template data not provided. Load a CSV first.")

        dataframes = []

        for i in range(n):
            # Create a copy of the template
            df_copy = self.template_data.copy()

            # Identify frequency columns (start with "Ch ")
            freq_cols = [col for col in df_copy.columns if col.startswith("Ch")]

            # Generate one noise value per record (per row) that applies to ALL channels
            # This maintains the smooth spectral shape while varying between records
            noise_per_record = self.rng.normal(0, self.noise_std, len(df_copy))
            
            # Apply the same noise to all frequency channels for each record
            for freq_col in freq_cols:
                df_copy[freq_col] = df_copy[freq_col] + noise_per_record

            # Optionally add small variation to TkBB (very small, ~0.01 K)
            if "TkBB(K)" in df_copy.columns:
                tkbb_noise = self.rng.normal(0, 0.01, len(df_copy))
                df_copy["TkBB(K)"] = df_copy["TkBB(K)"] + tkbb_noise

            dataframes.append(df_copy)

        return dataframes

    @staticmethod
    def load_template(csv_path: str) -> pd.DataFrame:
        """Load a CSV file as template.

        Parameters
        ----------
        csv_path : str
            Path to CSV file.

        Returns
        -------
        pd.DataFrame
            Loaded template data.
        """
        return pd.read_csv(csv_path)

    @staticmethod
    def create_default_template(
        n_rows: int = 40,
        n_channels: int = 24,
        freq_min: float = 22.0,
        freq_max: float = 30.0,
    ) -> pd.DataFrame:
        """Create a default template dataframe.

        Parameters
        ----------
        n_rows : int
            Number of observations per dataframe.
        n_channels : int
            Number of frequency channels.
        freq_min : float
            Minimum frequency (GHz).
        freq_max : float
            Maximum frequency (GHz).

        Returns
        -------
        pd.DataFrame
            Default template with realistic values.
        """
        # Create frequency channel columns
        frequencies = np.linspace(freq_min, freq_max, n_channels)
        freq_cols = {f"Ch {freq:7.3f}": None for freq in frequencies}

        # Generate template structure
        data = {
            "Record": list(range(2, n_rows + 2)),
            "Date/Time": pd.date_range("2023-04-04 00:05:05", periods=n_rows, freq="18S").strftime("%m/%d/%y %H:%M:%S"),
            "50": [50] * n_rows,
            "Az(deg)": np.tile([0.0, 45.0, 90.0, 135.0], n_rows // 4 + 1)[:n_rows],
            "El(deg)": np.tile([19.8, 90.0, 160.2], n_rows // 3 + 1)[:n_rows],
            "TkBB(K)": np.linspace(306.9, 307.1, n_rows),
        }

        # Add frequency columns with realistic TB values
        rng = np.random.RandomState(42)
        for i, freq in enumerate(frequencies):
            # TB values vary with frequency (lower at higher frequencies, typically)
            base_tb = 180.0 - (freq - 22.0) * 2.5
            noise = rng.normal(0, 5.0, n_rows)
            data[f"Ch {freq:7.3f}"] = base_tb + noise

        df = pd.DataFrame(data)

        # Reorder columns to match typical radiometer format
        cols = ["Record", "Date/Time", "50", "Az(deg)", "El(deg)", "TkBB(K)"]
        cols.extend([col for col in df.columns if col.startswith("Ch")])
        df = df[cols]

        return df

    def save_dataframes(
        self,
        dataframes: List[pd.DataFrame],
        output_dir: str = "src/data/datos_radiometro_sinteticos",
        prefix: str = "synthetic",
    ) -> List[str]:
        """Save generated dataframes to CSV files.

        Parameters
        ----------
        dataframes : list of pd.DataFrame
            Dataframes to save.
        output_dir : str
            Output directory path.
        prefix : str
            Prefix for output filenames.

        Returns
        -------
        list of str
            Paths to saved files.
        """
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for i, df in enumerate(dataframes):
            filename = output_path / f"{prefix}_{i:03d}.csv"
            df.to_csv(filename, index=False)
            saved_files.append(str(filename))

        return saved_files


def generate_synthetic_dataset(
    template_path: str | None = None,
    n_dataframes: int = 10,
    noise_std: float = 2.0,
    seed: int = 42,
    output_dir: str = "src/data/datos_radiometro_sinteticos",
) -> List[pd.DataFrame]:
    """Generate a dataset of synthetic radiometer dataframes.

    Parameters
    ----------
    template_path : str, optional
        Path to template CSV. If None, creates default template.
    n_dataframes : int
        Number of dataframes to generate.
    noise_std : float
        Standard deviation of Gaussian noise.
    seed : int
        Random seed.
    output_dir : str
        Output directory for saving.

    Returns
    -------
    list of pd.DataFrame
        Generated synthetic dataframes.
    """
    # Load or create template
    if template_path:
        template = SyntheticRadiometerGenerator.load_template(template_path)
    else:
        template = SyntheticRadiometerGenerator.create_default_template()

    # Generate dataframes
    generator = SyntheticRadiometerGenerator(
        template_data=template,
        noise_std=noise_std,
        seed=seed,
    )

    dataframes = generator.generate_dataframes(n_dataframes)

    # Save to disk
    saved_files = generator.save_dataframes(dataframes, output_dir)

    print(f"✅ Generated {n_dataframes} synthetic dataframes")
    print(f"   Noise std: {noise_std} K")
    print(f"   Saved to: {output_dir}")
    print(f"   Files: {len(saved_files)}")

    return dataframes


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        template_path = sys.argv[1]
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        dfs = generate_synthetic_dataset(template_path, n_dataframes=n)
    else:
        # Generate with default template
        dfs = generate_synthetic_dataset(n_dataframes=10, noise_std=2.0)
        print(f"First dataframe shape: {dfs[0].shape}")
        print(f"First dataframe:\n{dfs[0].head()}")
