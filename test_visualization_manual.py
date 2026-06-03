from src.config.config_loader import load_config
from src.config.config_parser import parse_and_validate_config
from src.data.dataset_builder import build_dataset
from src.visualization.plots import generate_visualization_products


raw_config = load_config("src/config/examples/base_config.yaml")
config = parse_and_validate_config(raw_config)

dataset_result, exported_files = build_dataset(
    config=config,
    records_override=3,
    output_prefix="viz_test",
    export=True,
)

figure_files = generate_visualization_products(
    mixer_result=dataset_result,
    config=config,
    output_prefix="viz_test",
)

print("Dataset exported:")
for name, path in exported_files.items():
    print(f"{name}: {path}")

print("\nFigures exported:")
for name, path in figure_files.items():
    print(f"{name}: {path}")