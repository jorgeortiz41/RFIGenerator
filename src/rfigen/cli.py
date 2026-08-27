"""Command line interface for RFIGen."""

from __future__ import annotations

import argparse
from pathlib import Path

from rfigen.config import ExperimentConfig, RFIConfig, load_config
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset
from rfigen.real_data import build_dataset_from_real_csv, summarize_mp3000a_csv
from rfigen.visualization import save_all_plots


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rfigen", description="Synthetic RFI generator for K-band radiometry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="generate and export a dataset")
    _add_common_options(generate_parser)
    generate_parser.add_argument("--output", default="outputs/dataset", help="output directory")
    generate_parser.add_argument("--no-csv", action="store_true", help="skip CSV exports")
    generate_parser.add_argument("--no-npz", action="store_true", help="skip NPZ export")
    generate_parser.set_defaults(func=_generate)

    plot_parser = subparsers.add_parser("plot", help="generate visualization images")
    _add_common_options(plot_parser)
    plot_parser.add_argument("--output", default="outputs/figures", help="output directory")
    plot_parser.set_defaults(func=_plot)

    inspect_parser = subparsers.add_parser("inspect-csv", help="inspect an MP-3000A-style CSV file")
    inspect_parser.add_argument("csv_file", help="path to the CSV file")
    inspect_parser.add_argument("--min-frequency-ghz", type=float, default=20.0)
    inspect_parser.add_argument("--max-frequency-ghz", type=float, default=30.0)
    inspect_parser.set_defaults(func=_inspect_csv)

    real_parser = subparsers.add_parser("generate-from-csv", help="inject synthetic RFI into real radiometer CSV data")
    _add_common_options(real_parser)
    real_parser.add_argument("csv_file", help="path to the CSV file")
    real_parser.add_argument("--output", default="outputs/real_dataset", help="output directory")
    real_parser.add_argument("--min-frequency-ghz", type=float, default=20.0)
    real_parser.add_argument("--max-frequency-ghz", type=float, default=30.0)
    real_parser.add_argument("--no-csv", action="store_true", help="skip CSV exports")
    real_parser.add_argument("--no-npz", action="store_true", help="skip NPZ export")
    real_parser.set_defaults(func=_generate_from_csv)

    gui_parser = subparsers.add_parser("gui", help="open one of the interactive GUIs")
    gui_group = gui_parser.add_mutually_exclusive_group()
    gui_group.add_argument("--legacy", action="store_true", help="config-driven legacy GUI")
    gui_group.add_argument("--mp3000a", action="store_true", help="MP-3000A LV1 real-data GUI")
    gui_group.add_argument("--signal", action="store_true", help="sine/Gaussian signal workbench")
    gui_parser.set_defaults(func=_gui)

    pipeline_parser = subparsers.add_parser("pipeline", help="run the legacy config-driven pipeline")
    pipeline_parser.add_argument("--config", required=True, help="YAML or JSON configuration file")
    pipeline_parser.set_defaults(func=_pipeline)

    rttov_parser = subparsers.add_parser("rttov", help="generate a synthetic MP-3000A Level-1 CSV")
    rttov_parser.add_argument("--output", default="outputs/rttov_lv1.csv", help="output CSV path")
    rttov_parser.add_argument("--hours", type=float, default=6.0, help="hours to simulate")
    rttov_parser.add_argument("--step-seconds", type=int, default=60, help="seconds between samples")
    rttov_parser.add_argument("--seed", type=int, default=42, help="random seed")
    rttov_parser.add_argument("--start-utc", default="", help="UTC start as YYYY-mm-ddTHH:MM:SS")
    rttov_parser.set_defaults(func=_rttov)

    args = parser.parse_args(argv)
    return args.func(args)


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="YAML or JSON configuration file")
    parser.add_argument("--seed", type=int, help="random seed override")
    parser.add_argument("--duration-s", type=float, help="duration override")
    parser.add_argument("--sample-rate-hz", type=float, help="sample rate override")
    parser.add_argument("--rfi-type", choices=["narrowband", "broadband", "pulsed", "bursty", "chirp", "am"], help="single RFI model when no config is provided")
    parser.add_argument("--center-frequency-ghz", type=float, default=22.235, help="center frequency for direct CLI generation")
    parser.add_argument("--bandwidth-mhz", type=float, default=25.0, help="RFI bandwidth for direct CLI generation")
    parser.add_argument("--power-k", type=float, default=15.0, help="RFI power for direct CLI generation")


def _load_or_create_config(args: argparse.Namespace) -> ExperimentConfig:
    config = load_config(args.config) if args.config else ExperimentConfig()
    if not args.config and args.rfi_type:
        config.rfi.append(
            RFIConfig(
                type=args.rfi_type,
                center_frequency_ghz=args.center_frequency_ghz,
                bandwidth_mhz=args.bandwidth_mhz,
                power_k=args.power_k,
            )
        )
    if args.seed is not None:
        config.seed = args.seed
    if args.duration_s is not None:
        config.duration_s = args.duration_s
    if args.sample_rate_hz is not None:
        config.sample_rate_hz = args.sample_rate_hz
    config.validate()
    return config


def _generate(args: argparse.Namespace) -> int:
    config = _load_or_create_config(args)
    dataset = build_dataset(config)
    output = export_dataset(dataset, args.output, include_csv=not args.no_csv, include_npz=not args.no_npz)
    if config.export.include_plots:
        save_all_plots(dataset, Path(output) / "figures")
    print(f"Dataset written to {output}")
    return 0


def _plot(args: argparse.Namespace) -> int:
    config = _load_or_create_config(args)
    dataset = build_dataset(config)
    output = save_all_plots(dataset, args.output)
    print(f"Figures written to {output}")
    return 0


def _inspect_csv(args: argparse.Namespace) -> int:
    summary = summarize_mp3000a_csv(args.csv_file, args.min_frequency_ghz, args.max_frequency_ghz)
    print(f"Rows: {summary['rows']}")
    print(f"Channels: {summary['channels']}")
    print(f"Frequency range: {summary['frequency_min_ghz']:.3f}-{summary['frequency_max_ghz']:.3f} GHz")
    print("Frequencies:", ", ".join(f"{item:.3f}" for item in summary["frequencies_ghz"]))
    print(f"Directions: {summary['direction_count']}")
    for direction, count in summary["direction_rows"].items():
        print(f"  {direction}: {count} rows")
    print(f"Time span: {summary['time_start']} to {summary['time_stop']}")
    return 0


def _generate_from_csv(args: argparse.Namespace) -> int:
    config = _load_or_create_config(args)
    dataset = build_dataset_from_real_csv(
        args.csv_file,
        config,
        min_frequency_ghz=args.min_frequency_ghz,
        max_frequency_ghz=args.max_frequency_ghz,
    )
    output = export_dataset(dataset, args.output, include_csv=not args.no_csv, include_npz=not args.no_npz)
    if config.export.include_plots:
        save_all_plots(dataset, Path(output) / "figures")
    print(f"Real-data dataset written to {output}")
    return 0


def _gui(args: argparse.Namespace) -> int:
    if args.legacy:
        from rfigen.legacy.gui import launch_gui
    elif args.mp3000a:
        from rfigen.legacy.mp3000a_gui import launch_gui
    elif args.signal:
        from rfigen.legacy.signal_gui import launch_gui
    else:
        from rfigen.gui import run_gui as launch_gui

    launch_gui()
    return 0


def _pipeline(args: argparse.Namespace) -> int:
    from rfigen.legacy.pipeline import run_pipeline

    run_pipeline(args.config)
    return 0


def _rttov(args: argparse.Namespace) -> int:
    from rfigen.legacy.rttov import generate_level1

    output = generate_level1(
        output_path=args.output,
        hours=args.hours,
        step_seconds=args.step_seconds,
        seed=args.seed,
        start_utc=args.start_utc,
    )
    print(f"Level-1 file written to {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
