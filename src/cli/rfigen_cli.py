# rfigen_cli.py
# ============================================================
# Command Line Interface for RFIGen
# ------------------------------------------------------------
# Allows automated dataset generation using a YAML/JSON config.
#
# Example:
#   python src/cli/rfigen_cli.py --config src/config/examples/base_config.yaml
# ============================================================

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ------------------------------------------------------------
# Make sure the project root is available for imports
# This allows running:
#   python src/cli/rfigen_cli.py
# from the project root.
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config.config_loader import load_config
from src.config.config_parser import ConfigValidationError, parse_and_validate_config
from src.data.dataset_builder import build_dataset
from src.visualization.plots import generate_visualization_products


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="RFIGen CLI — Synthetic RFI dataset generator for K-band radiometric data."
    )

    parser.add_argument(
        "--config",
        type=str,
        default="src/config/examples/base_config.yaml",
        help="Path to YAML/JSON configuration file.",
    )

    parser.add_argument(
        "--records",
        type=int,
        default=None,
        help="Optional override for number of dataset records.",
    )

    parser.add_argument(
        "--output-prefix",
        type=str,
        default=None,
        help="Optional output filename prefix.",
    )

    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Generate dataset but do not export CSV, NPY, or metadata files.",
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Do not generate visualization figures.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Main CLI entry point.
    """

    args = parse_args()

    config_path = Path(args.config)

    print("============================================")
    print("RFIGen CLI")
    print("============================================")
    print(f"Config file: {config_path}")

    try:
        raw_config = load_config(config_path)
        config = parse_and_validate_config(raw_config)

    except ConfigValidationError as exc:
        print("\nConfig validation failed:")
        print(exc)
        raise SystemExit(1) from exc

    except Exception as exc:
        print("\nFailed to load configuration:")
        print(exc)
        raise SystemExit(1) from exc

    print("\nConfig loaded successfully.")
    print(f"Project: {config['project']['name']}")
    print(f"Profile: {config['project']['profile']}")
    print(
        f"Frequency band: "
        f"{config['frequency']['band']['min_ghz']}–"
        f"{config['frequency']['band']['max_ghz']} GHz"
    )
    print(f"Center frequency: {config['frequency']['center_ghz']} GHz")
    print(f"Configured RFI sources: {len(config.get('rfi_sources', []))}")

    try:
        dataset_result, exported_files = build_dataset(
            config=config,
            records_override=args.records,
            output_prefix=args.output_prefix,
            export=not args.no_export,
        )

        figure_files = {}

        if not args.no_plots:
            figure_files = generate_visualization_products(
                mixer_result=dataset_result,
                config=config,
                output_prefix=args.output_prefix or str(config["run"]["output_prefix"]),
            )

    except Exception as exc:
        print("\nDataset generation failed:")
        print(exc)
        raise SystemExit(1) from exc

    print("\nDataset generated successfully.")
    print(f"Clean dataset shape: {dataset_result.clean_df.shape}")
    print(f"Contaminated dataset shape: {dataset_result.contaminated_df.shape}")
    print(f"RFI matrix shape: {dataset_result.rfi_matrix.shape}")
    print(f"Channels: {dataset_result.channel_cols}")

    if exported_files:
        print("\nExported files:")
        for name, path in exported_files.items():
            print(f"  {name}: {path}")
    else:
        if args.no_export:
            print("\nNo files exported because --no-export was used.")
        else:
            print("\nNo dataset files were exported.")

    if figure_files:
        print("\nFigure files:")
        for name, path in figure_files.items():
            print(f"  {name}: {path}")
    else:
        if args.no_plots:
            print("\nNo figures generated because --no-plots was used.")
        else:
            print("\nNo figures generated.")

    print("\nDone.")


if __name__ == "__main__":
    main()