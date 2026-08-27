"""Config-driven RFIGen legacy pipeline.

Generates clean radiometric data, mixes in sampled RFI sources, and exports the
clean/contaminated pair with metadata. Driven by ``rfigen pipeline --config``.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from rfigen.legacy.config_loader import load_config
from rfigen.legacy.config_parser import ConfigValidationError, parse_and_validate_config
from rfigen.legacy.export_data import save_pipeline_outputs
from rfigen.legacy.radiometry import generate_synthetic_dataset
from rfigen.legacy.rttov import generate_level1_from_config, level1_to_wide_frame
from rfigen.legacy.signal_mixer import generate_rfi_sources, mix_signals


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
        rttov_csv = generate_level1_from_config(config)
        print(f"RTTOV Level-1 file written to {rttov_csv}")
        # RTTOV writes tidy/long rows; the mixer needs the MP-3000A wide layout.
        data = level1_to_wide_frame(rttov_csv)
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
    rng = np.random.default_rng(config.get("run", {}).get("seed", 42))
    n_sources = config.get("rfi", {}).get("n_sources", 5)
    source_classes = config.get("rfi", {}).get("source_classes", ["satellite", "aircraft", "ground"])
    sources = generate_rfi_sources(n_sources, source_classes, rng)
    print(f"3. Generated {len(sources)} RFI sources successfully!✅")

    # 4. Combine radiometric data and RFI sources
    mixed_data, rfi_infos = mix_signals(data, sources, rng)
    print("4. RFI signals mixed into radiometric data successfully!✅")
    print(f"Mixed data sample:\n{mixed_data[0].head() if isinstance(mixed_data, list) and len(mixed_data) > 0 else mixed_data.head() if isinstance(mixed_data, pd.DataFrame) else mixed_data}")

    # 5. Export clean data, contaminated data, and metadata
    saved_files = save_pipeline_outputs(
        clean_data=data,
        contaminated_data=mixed_data,
        rfi_infos=rfi_infos,
        sources=sources,
        config=config,
    )
    print("5. Data and metadata exported successfully!✅")
    print(f"Export summary: {saved_files}")
    return mixed_data, rfi_infos
