# RFI Generator: K-Band Synthetic Radio Frequency Interference Generator

A comprehensive Python application for generating synthetic Radio Frequency Interference (RFI) signals in the K-band (20-30 GHz) for K-band radiometric observations. Designed for UPRM CARSE researchers to validate RFI detection algorithms, test radiometer performance, and generate reproducible synthetic datasets for algorithm development and testing.

## Table of Contents

- [Overview](#overview)
- [Why Use RFI Generator?](#why-use-rfi-generator)
- [Key Features](#key-features)
- [Project Versions](#project-versions)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Getting Help](#getting-help)
- [Status](#status)
- [License](#license)

## Overview

RFI Generator provides both **Command-Line Interface (CLI)** and **Graphical User Interface (GUI)** tools to:

- Generate synthetic radiometric datasets with realistic K-band characteristics
- Inject synthetic RFI into real MP-3000A radiometer measurement data
- Simulate multiple RFI source types with configurable parameters
- Create publication-quality visualizations in time, frequency, and time-frequency domains
- Export data in multiple formats (CSV, NPZ, PNG) for analysis and archival

The tool emphasizes **reproducibility** through seed-based random number generation and **flexibility** via both interactive GUI and scriptable CLI interfaces.

## Why Use RFI Generator?

### For Algorithm Development
- Create controlled test datasets with known RFI characteristics
- Validate RFI detection and mitigation algorithms
- Test edge cases and parameter sensitivity

### For Radiometer Performance Testing
- Generate synthetic interference patterns that mimic real-world conditions
- Test radiometer responses to multiple simultaneous RFI sources
- Create baseline performance metrics under controlled conditions

### For Reproducible Research
- All datasets generated with specific seeds for exact reproducibility
- Configuration files document all experimental parameters
- Automated batch processing for parameter studies

### For Real Data Analysis
- Inject synthetic RFI into actual MP-3000A radiometer measurements
- Compare clean vs. contaminated radiometric profiles
- Develop and validate RFI mitigation strategies on real data

## Key Features

### Interfaces
- **CLI**: One `rfigen` command with 7 subcommands for scripting and automation
- **GUI**: Four interactive graphical interfaces, each with its own entry point
- Both engines — the ndarray core and the legacy DataFrame pipeline — are reachable from the same CLI

### RFI Models
- **6 Parametric Waveform Models** (core engine): narrowband, broadband, pulsed, bursty, chirp, AM
- **5 RFI Source Classes** (legacy engine): 5G, Radar Systems, Broadcast Services, ISM Equipment, Unintentional Emitters
- Mix multiple RFI sources in a single experiment

### Data Support
- Generate pure synthetic radiometric datasets
- Inject RFI into real MP-3000A radiometer CSV data
- Supports K-band frequency range (18-30 GHz, default 20-30 GHz)
- Standard 21-channel MP-3000A profile support

### Output Formats
- **CSV**: Human-readable matrices for spreadsheet analysis
- **NPZ**: Compressed NumPy arrays for efficient storage
- **PNG**: Publication-quality figures (profiles, spectrograms, frequency analysis)
- **JSON**: Complete metadata and experiment configuration

### Visualization
- **Time-Frequency Spectrograms**: Time-varying frequency content
- **Frequency Profiles**: Power spectral density by direction and frequency
- **Time Series**: Temporal evolution at selected frequencies
- **Direction-Specific Plots**: Analysis by azimuth and elevation angle

### Advanced Features
- **Reproducible Results**: Seed-based random generation for exact reproducibility
- **Batch Processing**: Generate multiple scenarios programmatically
- **Flexible Configuration**: YAML/JSON configuration files or CLI flags
- **Real Data Integration**: Combine synthetic RFI with actual radiometer measurements
- **Flexible Frequency Bands**: Custom frequency grids or standard K-band profiles

## Architecture

RFIGen ships a single installable package (`rfigen`) containing two engines. They were
previously two separate projects (`RFIGen_1` and `RFIGen_2`) and have been merged without
rewriting either one, so both keep their exact numerical behavior.

### Core engine — `rfigen.*`

Models a scan as a **time x frequency ndarray** of brightness temperatures in Kelvin, with
dataclass-based configuration.

- 6 parametric RFI waveform models: `narrowband`, `broadband`, `pulsed`, `bursty`, `chirp`, `am`
- MP-3000A-like clean radiometric simulation and real MP-3000A Level-1 CSV import
- CSV, NPZ, JSON metadata and figure export, including per-direction profiles
- Best for new experiments, batch processing, and real-data injection workflows

### Legacy engine — `rfigen.legacy.*`

Models a scan as **MP-3000A-style pandas rows** (`Ch <freq>` columns), with dict-based YAML
configuration and a deep-merge validator.

- RFI **source classes** (5G, Radar, Broadcast, ISM, Unintentional) with azimuth/elevation
  angular coupling — a pointing-aware model the core engine does not have
- RTTOV-style synthetic Level-1 generator
- CSV/XLSX export
- Best for pointing-dependent studies, Excel workflows, and legacy experiment compatibility

### Graphical interfaces

All four GUIs are preserved and installed as console scripts:

| Command | Also | What it is |
|---------|------|------------|
| `rfigen-gui` | `rfigen gui` | Core engine: live parametric RFI controls, direction picker, export |
| `rfigen-gui-mp3000a` | `rfigen gui --mp3000a` | Real MP-3000A workflow: XLSX/CSV cleaning, direction and frequency filtering, 5 RFI source classes, 300-DPI figure export |
| `rfigen-gui-legacy` | `rfigen gui --legacy` | Legacy engine: config load/save, generate, time/frequency/spectrogram tabs, export |
| `rfigen-gui-signal` | `rfigen gui --signal` | Signal workbench: sine, Gaussian noise, combined, frequency table, CSV import |

## Installation

### Prerequisites
- **Python**: 3.10 or higher
- **Conda**: Miniconda or Anaconda installation

### Step 1: Set Up Conda Environment

```bash
conda create -n RFI_Generator python=3.13
conda activate RFI_Generator
```

### Step 2: Install Dependencies

```bash
conda install numpy pandas matplotlib scipy pyyaml pytest
```

All of these are required: `openpyxl` backs the MP-3000A GUI's Excel support and `pyyaml`
backs the YAML configuration files.

### Step 3: Install RFIGenerator

```bash
cd /path/to/RFIGenerator
pip install -e .
```

Or for development, with the test dependencies:
```bash
pip install -e ".[dev]"
```

### Verify Installation

Test that the CLI works:
```bash
rfigen --help
```

Or test a GUI:
```bash
rfigen gui
```

## Quick Start

### Option 1: Generate Synthetic Dataset (CLI)

Quickest way to create a dataset:

```bash
rfigen generate \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --power-k 15 \
  --output outputs/example_narrowband
```

This creates:
- `clean.csv`: Synthetic radiometry without RFI
- `contaminated.csv`: Clean + RFI
- `rfi.csv`: RFI signal alone
- `dataset.npz`: Binary NumPy archive
- `metadata.json`: Experiment parameters
- `figures/`: PNG visualizations

### Option 2: Use Configuration File

For more complex setups with multiple RFI sources:

```bash
rfigen generate \
  --config configs/example.yaml \
  --output outputs/example_config
```

### Option 3: Generate Visualizations Only

Create plots from an existing configuration:

```bash
rfigen plot \
  --config configs/example.yaml \
  --output outputs/figures
```

### Option 4: Interactive GUI

Launch the graphical interface:

```bash
rfigen gui
```

Then:
1. Adjust parameters in the left panel
2. Select visualization type from "View" dropdown
3. Click "Generate" to create dataset
4. Click "Export Dataset" to save

### Option 5: Analyze Real Radiometer Data

Inspect an MP-3000A CSV file:

```bash
rfigen inspect-csv /path/to/radiometer_data.csv
```

Inject synthetic RFI into real radiometer measurements:

```bash
rfigen generate-from-csv \
  /path/to/radiometer_data.csv \
  --rfi-type pulsed \
  --center-frequency-ghz 24.0 \
  --power-k 20 \
  --output outputs/real_with_rfi
```

### Option 6: Run the Legacy Pipeline

Config-driven clean/contaminated generation with pointing-aware RFI source classes:

```bash
rfigen pipeline --config configs/legacy_base.yaml
```

### Option 7: Generate an RTTOV Level-1 File

```bash
rfigen rttov --output outputs/rttov_lv1.csv --hours 6 --seed 42
```

Note that this writes a tidy/long CSV (one row per channel per observation), which is a
different schema from the MP-3000A wide format read by `inspect-csv` and `generate-from-csv`.
Set `radiometry.use_rttov: true` in a legacy config to feed it straight into the pipeline,
which reshapes it automatically.

## Project Structure

```
RFIGenerator/
├── README.md                           # This file
├── USER_MANUAL.md                      # Comprehensive guide
├── requirements.txt                    # Pip dependencies
├── pyproject.toml                      # Package configuration
├── LICENSE                             # MIT License
├── rfigen_cli.py                       # Run the CLI without installing
├── Gui_app.py                          # Run the core GUI without installing
│
├── configs/
│   ├── example.yaml                    # Core engine configuration
│   └── legacy_base.yaml                # Legacy engine configuration
├── data/
│   ├── datos_radiometro/               # Real MP-3000A Level-1 measurements
│   ├── datos_radiometro_procesados/    # Cleaned measurements
│   └── datos_radiometro_sinteticos/    # Generated measurements
├── docs/
│   ├── legacy_cli.md                   # Legacy CLI notes
│   └── legacy_config.md                # Legacy config reference
├── examples/generate_dataset.py        # Python API example
├── notebooks/                          # Analysis notebooks
│
├── src/rfigen/                         # The package
│   ├── cli.py                          # Unified CLI (7 subcommands)
│   ├── gui.py                          # Core GUI
│   ├── config.py                       # Dataclass configuration
│   ├── dataset.py                      # Dataset generation
│   ├── grid.py                         # Time/frequency grids
│   ├── mixer.py                        # Signal mixing
│   ├── radiometry.py                   # K-band radiometry simulation
│   ├── real_data.py                    # MP-3000A Level-1 CSV import
│   ├── export_data.py                  # CSV/NPZ/JSON export
│   ├── models/base.py                  # 6 parametric RFI models
│   ├── visualization/plots.py          # Plotting utilities
│   │
│   └── legacy/                         # Legacy engine
│       ├── pipeline.py                 # Config-driven pipeline
│       ├── config_loader.py            # YAML/JSON loading
│       ├── config_parser.py            # Defaults + validation
│       ├── radiometry.py               # DataFrame radiometry
│       ├── rttov.py                    # RTTOV Level-1 generator
│       ├── rfi_generator.py            # RFI source classes
│       ├── signal_mixer.py             # Angular-coupling mixer
│       ├── export_data.py              # CSV/XLSX export
│       ├── data_import.py              # Local measurement import
│       ├── gui.py                      # Legacy GUI
│       ├── mp3000a_gui.py              # MP-3000A real-data GUI
│       ├── signal_gui.py               # Signal workbench GUI
│       └── visualization/              # Time/frequency plotting
│
└── tests/
    ├── test_config.py  test_dataset.py  test_real_data.py
    ├── test_gui_smoke.py               # All four GUIs
    └── legacy/                         # Legacy engine tests
```

## Getting Help

### Documentation
- **Comprehensive Guide**: See `USER_MANUAL.md` for:
  - Complete CLI command reference
  - GUI tutorials for all four interfaces
  - Configuration file format and examples
  - RFI model descriptions and parameters
  - Real data import workflows
  - Working examples with actual output
  - Troubleshooting guide
  - Python API reference

### Running Tests

Verify everything works correctly:

```bash
pytest tests/ -v
```

All tests should pass with output showing number of passing tests.

### Common Tasks

- **Generate synthetic data**: See Quick Start - Option 1
- **Use real radiometer data**: See Quick Start - Option 5
- **Configure complex scenarios**: See USER_MANUAL.md "Configuration" section
- **Batch process multiple scenarios**: See USER_MANUAL.md "Examples" section
- **Troubleshoot issues**: See USER_MANUAL.md "Troubleshooting" section

## Status

✅ **CLI**: Fully functional with all 5 subcommands working  
✅ **GUIs**: Four Tkinter interfaces, all installed as console scripts  
✅ **Visualization**: Complete time, frequency, and time-frequency domain plots  
✅ **Export**: CSV, NPZ, JSON, PNG formats all working  
✅ **Real Data**: MP-3000A CSV import and RFI injection operational  
✅ **Testing**: All unit tests passing  
✅ **Ready for Production**: Suitable for research use

## License

MIT License - See LICENSE file for details

## Contact

ECE Department, Center for Advanced Research on Satellite Earth Observation (CARSE)  
University of Puerto Rico - Mayagüez
