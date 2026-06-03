from src.config.config_loader import load_config
from src.config.config_parser import parse_and_validate_config
from src.data.dataset_builder import build_dataset


raw_config = load_config("src/config/examples/base_config.yaml")
config = parse_and_validate_config(raw_config)

dataset_result, exported_files = build_dataset(
    config=config,
    records_override=3,
    output_prefix="test_dataset",
    export=True,
)

print("Dataset created successfully.")
print("Clean dataset shape:", dataset_result.clean_df.shape)
print("Contaminated dataset shape:", dataset_result.contaminated_df.shape)
print("RFI matrix shape:", dataset_result.rfi_matrix.shape)
print("Channels:", dataset_result.channel_cols)

print("\nExported files:")
for name, path in exported_files.items():
    print(f"{name}: {path}")