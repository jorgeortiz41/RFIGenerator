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
- **CLI**: Full command-line interface with 5 subcommands for scripting and automation
- **GUI**: Interactive graphical interface for real-time parameter adjustment and visualization
- Both interfaces available in the modern RFIGen_2 version

### RFI Models
- **6 Parametric Waveform Models** (RFIGen_2): narrowband, broadband, pulsed, bursty, chirp, AM
- **5 RFI Source Classes** (Original): 5G, Radar Systems, Broadcast Services, ISM Equipment, Unintentional Emitters
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

## Project Versions

RFIGenerator includes two main versions, each with distinct strengths:

### RFIGen_2 (Recommended for new projects)
**Location**: `/RFIGen_2/` directory

**Features**:
- Modern, modular Python codebase
- Complete CLI with 5 subcommands (`generate`, `plot`, `inspect-csv`, `generate-from-csv`, `gui`)
- Clean Tkinter GUI with real-time visualization
- 6 parametric RFI waveform models
- YAML/JSON configuration file support
- Better organized source structure (`src/rfigen/`)
- Python API for programmatic use

**Best for**: 
- New experiments and algorithm development
- Scripting and batch processing
- Clean synthetic dataset generation
- Real data injection workflows

**Limitations**:
- Requires PyYAML for config file loading (but works with CLI flags without it)

### Original Version (GUI for real data analysis)
**Location**: Root directory (`gui_visual.py` and `src/` subdirectories)

**Features**:
- Comprehensive GUI optimized for real radiometer data analysis
- 5 RFI source classes (5G, Radar, Broadcast, ISM, Unintentional)
- Direct XLSX/CSV file import with data cleaning
- Synthetic RFI overlay on real measurements
- Detailed radiometer profile visualizations

**Best for**:
- Analyzing existing MP-3000A measurements
- Working with Excel-based radiometer data
- RFI source class-based analysis

**Integration**: Both versions share underlying radiometry and visualization principles; original provides RFI source class models not present in RFIGen_2.

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

**Optional dependencies**:
- `openpyxl`: For Excel file support (original GUI only)
- `pyyaml`: For YAML config files (can use JSON or CLI flags without it)

### Step 3: Install RFIGenerator

```bash
cd /path/to/RFIGenerator
pip install -e .
```

Or for development with all optional dependencies:
```bash
pip install -e ".[dev,yaml,scipy]"
```

### Verify Installation

Test that the CLI works:
```bash
python RFIGen_2/rfigen_cli.py --help
```

Or test the GUI:
```bash
python RFIGen_2/Gui_app.py
```

## Quick Start

### Option 1: Generate Synthetic Dataset (CLI)

Quickest way to create a dataset:

```bash
cd RFIGen_2
python rfigen_cli.py generate \
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
cd RFIGen_2
python rfigen_cli.py generate \
  --config configs/example.yaml \
  --output outputs/example_config
```

### Option 3: Generate Visualizations Only

Create plots from an existing configuration:

```bash
cd RFIGen_2
python rfigen_cli.py plot \
  --config configs/example.yaml \
  --output outputs/figures
```

### Option 4: Interactive GUI

Launch the graphical interface:

```bash
cd RFIGen_2
python Gui_app.py
```

Then:
1. Adjust parameters in the left panel
2. Select visualization type from "View" dropdown
3. Click "Generate" to create dataset
4. Click "Export Dataset" to save

### Option 5: Analyze Real Radiometer Data

Inspect an MP-3000A CSV file:

```bash
cd RFIGen_2
python rfigen_cli.py inspect-csv /path/to/radiometer_data.csv
```

Inject synthetic RFI into real radiometer measurements:

```bash
cd RFIGen_2
python rfigen_cli.py generate-from-csv \
  /path/to/radiometer_data.csv \
  --rfi-type pulsed \
  --center-frequency-ghz 24.0 \
  --power-k 20 \
  --output outputs/real_with_rfi
```

## Project Structure

```
RFIGenerator/
├── README.md                           # This file
├── USER_MANUAL.md                      # Comprehensive guide
├── requirements.txt                    # Pip dependencies
├── pyproject.toml                      # Package configuration
├── LICENSE                             # MIT License
│
├── RFIGen_2/                          # Modern version (RECOMMENDED)
│   ├── rfigen_cli.py                  # CLI entry point
│   ├── Gui_app.py                     # GUI entry point
│   ├── configs/
│   │   └── example.yaml               # Example configuration
│   ├── examples/
│   │   └── generate_dataset.py        # Example Python script
│   ├── src/rfigen/
│   │   ├── cli.py                     # CLI implementation
│   │   ├── gui.py                     # GUI implementation
│   │   ├── config.py                  # Configuration management
│   │   ├── dataset.py                 # Dataset generation
│   │   ├── radiometry.py              # K-band radiometry simulation
│   │   ├── export_data.py             # CSV/NPZ/JSON export
│   │   ├── models/                    # RFI model implementations
│   │   │   ├── base.py
│   │   │   └── [model files]
│   │   ├── visualization/             # Plotting utilities
│   │   ├── grid.py                    # Time/frequency grid generation
│   │   └── mixer.py                   # Signal mixing
│   ├── tests/                         # Unit tests
│   └── outputs/                       # Default output directory
│
├── src/                               # Original version
│   ├── cli/                           # CLI interface
│   ├── gui/
│   │   └── gui_app.py
│   ├── models/                        # RFI models
│   ├── config/                        # Configuration
│   ├── export/                        # Export utilities
│   ├── visualization/                 # Plotting
│   └── tests/
│
├── gui_visual.py                      # Original GUI (legacy)
├── gausiansignal.py                   # Original utilities
│
├── examples/                          # Usage examples
├── outputs/                           # Example output directory
└── tests/                             # Root tests
```

## Getting Help

### Documentation
- **Comprehensive Guide**: See `USER_MANUAL.md` for:
  - Complete CLI command reference
  - GUI tutorials for both versions
  - Configuration file format and examples
  - RFI model descriptions and parameters
  - Real data import workflows
  - Working examples with actual output
  - Troubleshooting guide
  - Python API reference

### Running Tests

Verify everything works correctly:

```bash
cd RFIGen_2
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
✅ **GUI (RFIGen_2)**: Clean, responsive Tkinter interface  
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
