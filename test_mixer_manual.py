import pandas as pd
import numpy as np

from src.config.config_loader import load_config
from src.config.config_parser import parse_and_validate_config
from src.mixer.signal_mixer import mix_clean_with_rfi
from src.export.export_data import export_mixer_result


# Load config
raw_config = load_config("src/config/examples/base_config.yaml")
config = parse_and_validate_config(raw_config)

# Create simple clean radiometric data
freqs = ["22.000", "22.234", "22.500", "23.000", "23.834", "25.000", "26.234", "28.000", "30.000"]

df = pd.DataFrame({
    "Date/Time": pd.date_range("2026-01-01 00:00:00", periods=100, freq="1s"),
    "Az(deg)": np.zeros(100),
    "El(deg)": np.ones(100) * 90.0,
})

for f in freqs:
    df[f] = 180.0 + np.random.normal(0, 0.5, size=100)

# Mix clean data with RFI
result = mix_clean_with_rfi(df, config)

print("Clean shape:", result.clean_df.shape)
print("Contaminated shape:", result.contaminated_df.shape)
print("RFI matrix shape:", result.rfi_matrix.shape)
print("Channels:", result.channel_cols)
print("Metadata:")
print(result.metadata)

# Save quick outputs
exported_files = export_mixer_result(
    mixer_result=result,
    config=config,
    output_prefix="test_mixer"
)

print("Exported files:")
for name, path in exported_files.items():
    print(f"{name}: {path}")