# RFIGen

RFIGen is a Python application for creating synthetic Radio Frequency Interference (RFI)
in K-band ground-based radiometric observations, with the default working band set to
20-30 GHz. It includes:

- configurable RFI signal models
- MP-3000A-like clean radiometric simulation
- clean/contaminated dataset generation
- CSV, NPZ, JSON metadata, and figure export
- per-direction radiometric profile figures
- CLI automation
- Tkinter GUI for interactive exploration

## Environment

Use the requested Conda environment:

```bash
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate RFI_Generator
```

You can run the project directly from the repository. Editable installation is optional.
In a restricted environment, `--no-build-isolation` avoids downloading build tooling:

```bash
pip install -e ".[dev,yaml,scipy]" --no-build-isolation
```

If YAML or SciPy are not installed, RFIGen still works with JSON configs and NumPy-based
fallbacks.

## Quick Start

Generate a dataset:

```bash
python rfigen_cli.py generate --config configs/example.yaml --output outputs/example
```

Create plots from the same configuration:

```bash
python rfigen_cli.py plot --config configs/example.yaml --output outputs/figures
```

Open the GUI:

```bash
python Gui_app.py
```

Inspect a processed radiometer profile CSV:

```bash
python rfigen_cli.py inspect-csv /path/to/2023-04-01.csv
```

Inject RFI into a real profile dataset:

```bash
python rfigen_cli.py generate-from-csv /path/to/2023-04-01.csv --rfi-type narrowband --center-frequency-ghz 28.0 --power-k 35 --output outputs/real_profile
```

Run tests:

```bash
pytest
```

## Data Model

Datasets are represented as time-by-frequency arrays in Kelvin:

- `clean`: synthetic radiometric brightness temperature
- `rfi`: additive interference field
- `contaminated`: clean + RFI

Frequencies are stored in GHz. The base example uses the processed radiometer profile
channels from 22.000-30.000 GHz, including nonuniform channels such as 22.234, 23.034,
and 26.234 GHz. The CSV importer defaults to the broader 20-30 GHz selection.

The main profile figure is `figures/profiles_by_direction.png`. Individual direction
profiles and direction-specific time-frequency views are written under `figures/directions/`.

## Supported RFI Models

- `narrowband`
- `broadband`
- `pulsed`
- `bursty`
- `chirp`
- `am`

Each model supports configurable center frequency, bandwidth, power, persistence, duty
cycle, and optional modulation parameters.
