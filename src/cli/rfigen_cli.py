# Minimal imports
from pathlib import Path
from src.config.config_loader import load_config
from src.config.config_parser import parse_and_validate_config, ConfigValidationError
from src.models.RTTOV_radiometry_gen import main as generate_synthetic_data
from src.models.radiometry import generate_synthetic_dataset
from src.export.export_data import save_data
import sys
import pandas as pd

# Direct pipeline execution
def run_pipeline(config_path):
    # 1. Load, parse, and validate config
    resolved_config_path = Path(config_path).resolve()
    raw_config = load_config(resolved_config_path)
    try:
        config = parse_and_validate_config(raw_config)
    except ConfigValidationError as exc:
        print(f"Config validation failed: {exc}")
        raise SystemExit(1) from exc
    print("1. Config loaded successfully!✅")
    
    # 2. Generate synthetic radiometric data
    print(f"Seed: {config.get('run', {}).get('seed')}")
    print(config.get("radiometry", {}))
    if config.get("radiometry", {}).get("use_rttov", False):
        print("Generating synthetic data using RTTOV...")
        data = generate_synthetic_data(config)
    else:
        data = generate_synthetic_dataset(
            n_dataframes=config.get("run", {}).get("n_datasets", 10),
            noise_std=config.get("radiometry", {}).get("noise_std_k", 2.0),
            seed=config.get("run", {}).get("seed", 42),
            output_dir=config.get("export", {}).get("directory", "outputs/"),
        )
    print("2. Synthetic radiometric data generated successfully!✅")
    print(f"Data sample:\n{data[0].head() if isinstance(data, list) and len(data) > 0 else data.head() if isinstance(data, pd.DataFrame) else data}")

    # 3. Generate RFI sources


    # 4. Combine radiometric data and RFI sources
    

    # 5. Export data and metadata
    # save_data(processed, config.get('output_path'))
    return config

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot.py <args>")
        print("Example: python -m src.cli.rfigen_cli --config src/config/examples/base_config.yaml")
        sys.exit(1)
    
    if '--config' in sys.argv:
        config_index = sys.argv.index('--config') + 1
        if config_index < len(sys.argv):
            config_path = sys.argv[config_index]
            print(f"Using configuration file: {config_path}")
            data = run_pipeline(config_path)
            # print("Generated data:")
            # print(data.head() if isinstance(data, pd.DataFrame) else data)
        else:
            print("Error: --config flag provided but no path specified.")
            sys.exit(1)

if __name__ == "__main__":
    main()