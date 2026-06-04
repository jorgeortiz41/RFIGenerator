# RFIGen — Synthetic RFI Generator for K-Band Radiometric Data

RFIGen is a Python-based synthetic Radio Frequency Interference (RFI) generator designed for K-band ground-based radiometric data. The project supports reproducible dataset generation using configuration files, synthetic clean radiometric data, RFI contamination, metadata export, and visualization products.

The system is designed around a modular pipeline:

```text
Configuration
    ↓
Radiometric Dataset Builder
    ↓
Signal Mixer
    ↓
Export Module
    ↓
Visualization Module
    ↓
CLI Interface
Project Goals

The main goal of RFIGen is to generate synthetic K-band radiometric datasets containing both clean and RFI-contaminated observations. These datasets can support research, testing, and future machine-learning workflows for RFI detection and mitigation.

Current capabilities include:

Synthetic clean radiometric dataset generation
Synthetic RFI injection into K-band channels
Clean and contaminated dataset export
Metadata export
RFI matrix export
Time-domain visualization
Frequency-domain visualization
Time-frequency visualization
Command Line Interface automation
Unit and integration testing
Project Structure
RFIGenerator/
│
├── archive/
│   ├── gausiansignal.py
│   └── gui_visual.py
│
├── outputs/
│   ├── .gitkeep
│   └── figures/
│       └── .gitkeep
│
├── src/
│   ├── cli/
│   │   └── rfigen_cli.py
│   │
│   ├── config/
│   │   ├── config_loader.py
│   │   ├── config_parser.py
│   │   ├── RFIGen_CONFIG_README.md
│   │   └── examples/
│   │       └── base_config.yaml
│   │
│   ├── data/
│   │   ├── dataset_builder.py
│   │   ├── local_radiometric_import.py
│   │   └── RTTOV_radiometry_gen.py
│   │
│   ├── export/
│   │   └── export_data.py
│   │
│   ├── gui/
│   │   └── gui_app.py
│   │
│   ├── mixer/
│   │   └── signal_mixer.py
│   │
│   ├── models/
│   │   ├── radiometry.py
│   │   └── rfi_generator.py
│   │
│   ├── tests/
│   │   ├── test_cli.py
│   │   ├── test_dataset_builder.py
│   │   ├── test_export_data.py
│   │   ├── test_signal_mixer.py
│   │   └── test_visualization.py
│   │
│   └── visualization/
│       └── plots.py
│
├── .gitignore
├── LICENSE
└── README.md
Installation

Create or activate a Python environment, then install the required packages:

python -m pip install numpy pandas matplotlib pyyaml pytest

If Excel file support is needed:

python -m pip install openpyxl
Running the CLI

The main CLI entry point is:

python src/cli/rfigen_cli.py --config src/config/examples/base_config.yaml

Example with record override and custom output prefix:

python src/cli/rfigen_cli.py --config src/config/examples/base_config.yaml --records 3 --output-prefix cli_test

This generates files in the outputs/ directory.

CLI Options
--config          Path to YAML/JSON configuration file
--records         Optional override for number of dataset records
--output-prefix   Optional output filename prefix
--no-export       Generate dataset but do not export CSV, NPY, or metadata files
--no-plots        Do not generate visualization figures

Example without exporting files or figures:

python src/cli/rfigen_cli.py --config src/config/examples/base_config.yaml --records 1 --no-export --no-plots
Output Files

A normal CLI run creates:

outputs/<prefix>_clean.csv
outputs/<prefix>_contaminated.csv
outputs/<prefix>_rfi_matrix.npy
outputs/<prefix>_metadata.json

The visualization module creates:

outputs/figures/<prefix>_time_domain.png
outputs/figures/<prefix>_frequency_spectrum.png
outputs/figures/<prefix>_time_frequency.png

Generated output files are ignored by Git. Only the folder structure is preserved using .gitkeep.

Configuration File

The main example configuration is located at:

src/config/examples/base_config.yaml

The configuration controls:

project metadata
random seed
number of samples
frequency band
radiometric baseline parameters
RFI source parameters
dataset export settings
visualization settings
CLI and GUI interface settings
validation rules

Example RFI source:

rfi_sources:
  - id: rfi_nb_001
    type: narrowband
    enabled: true
    center_offset_mhz: 12.0
    bandwidth_mhz: 2.0
    power_dbm: -72.0
    persistence: 1.0
    modulation: none
Current RFI Source Support

The configuration parser supports the following RFI source types:

narrowband
broadband
pulsed
bursty
time_varying_frequency
amplitude_modulated

Current signal mixing supports configurable RFI injection based on:

center frequency offset
bandwidth
power scaling
persistence
pulse/burst behavior
spectral shape
temporal envelope
overlap policy
Running Tests

Run all tests:

python -m pytest src/tests

Expected result:

28 passed

Run individual test files:

python -m pytest src/tests/test_signal_mixer.py
python -m pytest src/tests/test_dataset_builder.py
python -m pytest src/tests/test_export_data.py
python -m pytest src/tests/test_visualization.py
python -m pytest src/tests/test_cli.py
Tested Modules

The project currently includes tests for:

Signal Mixer
Dataset Builder
Export Module
Visualization Module
CLI Integration

The CLI test verifies the full workflow:

CLI → Config → Dataset Builder → Signal Mixer → Export → Visualization
Development Notes

The files in archive/ are earlier prototypes used during initial development. Their useful functionality is being refactored into the modular SDP-based architecture.

The active modular implementation is located inside src/.

Current Status

Completed:

Modular project structure
YAML/JSON configuration loading
Configuration validation
Synthetic dataset builder
Signal mixer
RFI contamination pipeline
Export module
Visualization module
CLI interface
Unit tests
CLI integration tests

Next development steps:

Improve GUI integration with the modular pipeline
Add more realistic RFI source models
Expand scientific validation
Add MP-3000A-style export format
Improve documentation for users and developers