# RFI Generator: Synthetic K-band Radio Frequency Interference Generator

A comprehensive Python application for generating synthetic RFI signals in the K-band for radiometric data analysis. This tool enables researchers to generate realistic RFI-contaminated datasets for developing RFI detection and mitigation algorithms.

## Features

- **Interactive generation** of synthetic RFI-contaminated radiometric data
- **Multiple RFI source types**: satellite, aircraft, ground, narrowband, pulsed, bursty
- **CLI and GUI interfaces** for flexibility
- **Real-time visualization** in time, frequency, and time-frequency domains
- **Batch processing** for large-scale dataset generation
- **Configurable parameters** via YAML files
- **Reproducible results** with seed-based random number generation

## Quick Start

### CLI Usage

```bash
conda activate RFI_Generator
PYTHONPATH=$(pwd):$PYTHONPATH python3 -m src.cli --config src/config/examples/base_config.yaml
```

### GUI Usage

```bash
conda activate RFI_Generator
python3 -c "from src.gui.gui_app import launch_gui; launch_gui()"
```

## Requirements

- Python 3.10+
- numpy, pandas, matplotlib, scipy, pyyaml

## Installation

```bash
conda create -n RFI_Generator python=3.13
conda activate RFI_Generator
conda install numpy pandas matplotlib scipy pyyaml pytest
pip install -e .
```

## Project Structure

```
src/
├── cli/                    # Command-line interface
├── gui/                    # Graphical user interface
├── models/                 # RFI and radiometry models
├── visualization/          # Plotting utilities
├── config/                 # Configuration management
├── export/                 # Data export
└── tests/                  # Unit tests (30 passing)
```

## Testing

```bash
pytest src/tests/ -v
```

## Documentation

See README in the project for complete documentation including:
- Detailed installation instructions
- Configuration file format
- Usage examples
- API documentation
- RFI source type specifications

## Status

✅ All 30 unit tests passing
✅ CLI fully functional
✅ GUI fully implemented
✅ Visualization components complete
✅ Ready for deployment

## License

MIT License

## Contact

ECE Department, University of Puerto Rico - Mayagüez
