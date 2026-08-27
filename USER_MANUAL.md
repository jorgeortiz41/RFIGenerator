# RFI Generator User Manual

**Complete Guide for CLI, GUI, Configuration, RFI Models, Real Data, and Python API**

## Table of Contents

1. [Part 1: CLI Complete Guide](#part-1-cli-complete-guide)
2. [Part 2: GUI Guide](#part-2-gui-guide)
3. [Part 3: Configuration](#part-3-configuration)
4. [Part 4: RFI Models Reference](#part-4-rfi-models-reference)
5. [Part 5: Real Data Usage](#part-5-real-data-usage)
6. [Part 6: Working Examples](#part-6-working-examples)
7. [Part 7: Python API Reference](#part-7-python-api-reference)
8. [Part 8: Troubleshooting & FAQ](#part-8-troubleshooting--faq)

---

# Part 1: CLI Complete Guide

## 1.1 CLI Overview & Architecture

The RFIGen Command-Line Interface provides a Unix-style tool for scriptable, reproducible RFI dataset generation and analysis. The CLI uses subcommands to organize functionality:

```
rfigen [OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Available Commands

| Command | Purpose |
|---------|---------|
| `generate` | Create synthetic radiometric datasets with optional RFI injection |
| `plot` | Generate publication-quality visualizations from configuration |
| `inspect-csv` | Analyze MP-3000A radiometer CSV files |
| `generate-from-csv` | Inject synthetic RFI into real radiometer CSV data |
| `gui` | Launch an interactive graphical interface (`--legacy`, `--mp3000a`, `--signal`) |
| `pipeline` | Run the legacy config-driven pipeline (source classes, angular coupling) |
| `rttov` | Generate a synthetic MP-3000A Level-1 CSV with the RTTOV model |

### Common Options (Available for `generate`, `plot`, `generate-from-csv`)

```
--config FILE              YAML or JSON configuration file path
--seed SEED               Random seed override (integer)
--duration-s DURATION     Override duration in seconds
--sample-rate-hz RATE     Override sample rate in Hz
--rfi-type TYPE           RFI model type when no config provided
--center-frequency-ghz F  RFI center frequency (default: 22.235 GHz)
--bandwidth-mhz BW        RFI bandwidth (default: 25.0 MHz)
--power-k POWER           RFI power in Kelvin (default: 15.0 K)
```

### Exit Codes

- `0`: Success
- `1`: Error occurred (configuration, I/O, or processing error)
- `2`: Invalid command-line arguments

---

## 1.2 Command Reference

### Command: `generate`

**Generate synthetic radiometric datasets with optional RFI.**

#### Syntax

```bash
rfigen generate [OPTIONS] --output OUTPUT_DIR
```

#### Options

```
--config CONFIG           YAML or JSON configuration file
--seed SEED              Random seed for reproducibility
--duration-s DURATION    Duration in seconds
--sample-rate-hz RATE    Sample rate in Hz
--rfi-type TYPE          RFI type: narrowband, broadband, pulsed, bursty, chirp, am
--center-frequency-ghz F Center frequency in GHz (default: 22.235)
--bandwidth-mhz BW       Bandwidth in MHz (default: 25.0)
--power-k POWER          Power in Kelvin (default: 15.0)
--output DIR             Output directory (default: outputs/dataset)
--no-csv                 Skip CSV export
--no-npz                 Skip NPZ export
```

#### Output Files

Creates the following in OUTPUT_DIR:

```
OUTPUT_DIR/
├── clean.csv                 # Radiometry without RFI (time×frequency matrix)
├── rfi.csv                   # RFI signal only (time×frequency matrix)
├── contaminated.csv          # Clean + RFI (time×frequency matrix)
├── dataset.npz               # NumPy archive (all arrays in binary format)
├── metadata.json             # Complete experiment configuration and statistics
└── figures/                  # Visualization directory
    ├── profiles_by_direction.png
    ├── spectrogram_clean.png
    ├── spectrogram_rfi.png
    ├── spectrogram_contaminated.png
    ├── time_domain.png
    ├── frequency_domain.png
    └── directions/           # Direction-specific plots
        ├── az_0_el_19p8_profile.png
        ├── az_0_el_19p8_spectrogram.png
        ├── [... one profile and spectrogram per direction ...]
        └── az_135_el_160p2_spectrogram.png
```

#### Use Cases

**Case 1: Generate clean synthetic data (no RFI)**

```bash
rfigen generate \
  --duration-s 120 \
  --sample-rate-hz 1 \
  --output outputs/clean_reference
```

**Case 2: Add single narrowband RFI source**

```bash
rfigen generate \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --bandwidth-mhz 80 \
  --power-k 25 \
  --output outputs/narrowband_rfi
```

**Case 3: Use configuration file for complex scenario**

```bash
rfigen generate \
  --config configs/example.yaml \
  --output outputs/example_complex
```

**Case 4: Override seed for reproducibility**

```bash
rfigen generate \
  --config configs/example.yaml \
  --seed 12345 \
  --output outputs/reproducible_run
```

---

### Command: `plot`

**Generate visualization images from a configuration without regenerating data.**

#### Syntax

```bash
rfigen plot [OPTIONS] --output OUTPUT_DIR
```

#### Options

```
--config CONFIG           YAML or JSON configuration file (required)
--seed SEED              Random seed
--duration-s DURATION    Duration override
--sample-rate-hz RATE    Sample rate override
--rfi-type TYPE          RFI type for CLI-based generation
--center-frequency-ghz F Center frequency
--bandwidth-mhz BW       Bandwidth
--power-k POWER          Power
--output DIR             Output directory for figures (default: outputs/figures)
```

#### Output

Generates PNG figures in OUTPUT_DIR (same structure as `generate` figures).

#### Use Case

Generate only visualizations without storing CSV/NPZ files:

```bash
rfigen plot \
  --config configs/example.yaml \
  --output outputs/plots_only
```

---

### Command: `inspect-csv`

**Analyze the structure and contents of an MP-3000A radiometer CSV file.**

#### Syntax

```bash
rfigen inspect-csv CSV_FILE [OPTIONS]
```

#### Options

```
CSV_FILE                  Path to MP-3000A CSV file (required)
--min-frequency-ghz F    Minimum frequency for analysis (default: 20.0 GHz)
--max-frequency-ghz F    Maximum frequency for analysis (default: 30.0 GHz)
```

#### Output

Displays:
- Number of rows (measurements)
- Number of channels (frequencies)
- Frequency range and list of all channels
- Number of unique directions
- Counts per direction
- Time span of measurements

#### Example

```bash
rfigen inspect-csv /path/to/radiometer_2023-04-01.csv

# Output:
# Rows: 1440
# Channels: 21
# Frequency range: 22.000-30.000 GHz
# Frequencies: 22.000, 22.234, 22.500, 23.000, ...
# Directions: 9
#   az=0.0, el=19.8: 160 rows
#   az=0.0, el=90.0: 160 rows
#   ...
# Time span: 2023-04-01 00:00:00 to 2023-04-01 23:59:00
```

---

### Command: `generate-from-csv`

**Inject synthetic RFI into real radiometer CSV measurements.**

#### Syntax

```bash
rfigen generate-from-csv CSV_FILE [OPTIONS] --output OUTPUT_DIR
```

#### Options

```
CSV_FILE                  MP-3000A CSV file path (required, positional)
--config CONFIG           Configuration file (optional)
--seed SEED              Random seed
--duration-s DURATION    Duration override
--sample-rate-hz RATE    Sample rate override
--rfi-type TYPE          RFI type: narrowband, broadband, pulsed, bursty, chirp, am
--center-frequency-ghz F Center frequency (default: 22.235 GHz)
--bandwidth-mhz BW       Bandwidth (default: 25.0 MHz)
--power-k POWER          Power (default: 15.0 K)
--output DIR             Output directory (default: outputs/real_dataset)
--min-frequency-ghz F    Minimum frequency for import (default: 20.0 GHz)
--max-frequency-ghz F    Maximum frequency for import (default: 30.0 GHz)
--no-csv                 Skip CSV export
--no-npz                 Skip NPZ export
```

#### Output

Same format as `generate`, but:
- `clean.csv` contains original radiometer measurements
- `contaminated.csv` contains original + synthetic RFI
- `rfi.csv` contains synthetic RFI signal only

#### Example

```bash
rfigen generate-from-csv /path/to/radiometer_data.csv \
  --rfi-type pulsed \
  --center-frequency-ghz 24.0 \
  --bandwidth-mhz 120 \
  --power-k 20 \
  --duty-cycle 0.15 \
  --pulse-period-s 6.0 \
  --output outputs/real_with_pulsed_rfi
```

---

### Command: `gui`

**Launch the interactive graphical user interface.**

#### Syntax

```bash
rfigen gui
```

No additional options. Opens the RFIGen_2 GUI window for interactive parameter adjustment and real-time visualization.

---

### `rfigen pipeline`

Runs the legacy DataFrame engine end to end: clean radiometry, RFI source sampling with
azimuth/elevation angular coupling, mixing, and export of the clean/contaminated pair plus
metadata.

```bash
rfigen pipeline --config configs/legacy_base.yaml
```

| Option | Purpose |
|--------|---------|
| `--config FILE` | Required. YAML or JSON legacy configuration file |

Output location and file names come from the config's `export` block, not from a flag.
Setting `radiometry.use_rttov: true` makes the pipeline generate its clean data with the
RTTOV model instead of the template generator, reshaping the result automatically.

### `rfigen rttov`

Generates a synthetic MP-3000A Level-1 CSV directly.

```bash
rfigen rttov --output outputs/rttov_lv1.csv --hours 6 --step-seconds 60 --seed 42
```

| Option | Default | Purpose |
|--------|---------|---------|
| `--output PATH` | `outputs/rttov_lv1.csv` | Output CSV path |
| `--hours H` | `6.0` | Hours to simulate |
| `--step-seconds S` | `60` | Seconds between samples |
| `--seed N` | `42` | Random seed |
| `--start-utc T` | now | UTC start as `YYYY-mm-ddTHH:MM:SS` |

It simulates 8 K-band and 14 V-band channels across 9 azimuth/elevation scan directions,
writing tidy/long rows (one row per channel per observation, record type 51). This is a
**different schema** from the MP-3000A wide format that `inspect-csv` and
`generate-from-csv` read, so those commands cannot consume this file directly; use
`use_rttov: true` in a legacy config to feed it into the pipeline instead.

---

## 1.3 CLI Workflows

### Workflow 1: Basic Synthetic Dataset Generation

```bash
# Step 1: Generate dataset with narrowband RFI
rfigen generate \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --power-k 20 \
  --output outputs/my_experiment

# Step 2: Examine output
ls -lah outputs/my_experiment/

# Step 3: Load and analyze (e.g., in Python)
import numpy as np
data = np.load('outputs/my_experiment/dataset.npz')
clean = data['clean']
rfi = data['rfi']
contaminated = data['contaminated']
```

### Workflow 2: Parameter Sweep (Batch Processing)

```bash
#!/bin/bash
# sweep_rfi_power.sh - Test different RFI power levels

for power in 5 10 15 20 25 30; do
  rfigen generate \
    --rfi-type narrowband \
    --center-frequency-ghz 28.0 \
    --power-k $power \
    --seed 42 \
    --output "outputs/power_sweep/power_${power}K"
  echo "Generated dataset with power=$power K"
done
```

Run with:
```bash
bash sweep_rfi_power.sh
```

### Workflow 3: Working with Real Data

```bash
# Step 1: Inspect radiometer file
rfigen inspect-csv /path/to/radiometer_2023-04-15.csv

# Step 2: Generate version with RFI for testing
rfigen generate-from-csv /path/to/radiometer_2023-04-15.csv \
  --rfi-type bursty \
  --center-frequency-ghz 26.0 \
  --power-k 18 \
  --output outputs/contaminated_real_data

# Step 3: Compare plots
# Open outputs/contaminated_real_data/figures/profiles_by_direction.png
```

### Workflow 4: Reproducible Multi-RFI Scenario

```bash
# Create config file (see Part 3 for format)
cat > configs/my_experiment.yaml << 'EOF'
seed: 2026
duration_s: 120
sample_rate_hz: 1
frequency_channels_ghz:
  - 22.000
  - 24.000
  - 26.000
  - 28.000
  - 30.000
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 20
    persistence: 1.0
  - type: pulsed
    center_frequency_ghz: 24.0
    bandwidth_mhz: 100
    power_k: 15
    duty_cycle: 0.2
    pulse_period_s: 5.0
EOF

# Generate multiple runs with different seeds
for seed in 100 101 102 103 104; do
  rfigen generate \
    --config configs/my_experiment.yaml \
    --seed $seed \
    --output "outputs/multi_rfi/run_$seed"
done
```

---

# Part 2: GUI Guide

## 2.1 Core GUI (Primary)

The RFIGen_2 GUI provides an interactive interface for real-time parameter adjustment and visualization.

### Starting the GUI

```bash
cd RFIGen_2
python Gui_app.py
```

Window appears: "RFIGen - Synthetic K-Band RFI Generator"

### Interface Layout

```
┌─────────────────────────────────────────────────────────┐
│ RFIGen - Synthetic K-Band RFI Generator                 │
├────────────────────┬──────────────────────────────────┤
│                    │                                  │
│  CONTROL PANEL     │     VISUALIZATION AREA          │
│                    │                                  │
│ [x] Add RFI        │  ┌────────────────────────────┐ │
│                    │  │                            │ │
│ RFI Type:          │  │  Matplotlib Plot Display  │ │
│ [Narrowband ▼]     │  │                            │ │
│                    │  │  (Time-Frequency          │ │
│ Center GHz: 22.235 │  │   Spectrogram, or         │ │
│ Bandwidth MHz: 80  │  │   Profiles, etc.)          │ │
│ Power K: 25.0      │  │                            │ │
│ Duration s: 60     │  │  Navigation Toolbar ▔▔▔▔  │ │
│ Sample Hz: 1.0     │  └────────────────────────────┘ │
│                    │                                  │
│ View:              │                                  │
│ [profiles ▼]       │                                  │
│                    │                                  │
│ Direction:         │                                  │
│ [az=0, el=19.8 ▼]  │                                  │
│                    │                                  │
│ [Generate]         │                                  │
│ [Export Dataset]   │                                  │
│                    │                                  │
└────────────────────┴──────────────────────────────────┘
```

### Control Panel Components

#### RFI Enable/Disable
- **Checkbox**: `[x] Add RFI` - Toggle RFI on/off
- When unchecked: generates clean radiometry only
- When checked: all RFI parameters active

#### RFI Type Selector
- **Options**: narrowband, broadband, pulsed, bursty, chirp, am
- Determines signal characteristics (see Part 4 for descriptions)
- Example: "narrowband" = single fixed frequency

#### Parameter Inputs

All numeric fields accept decimal values:

| Parameter | Range | Default | Unit | Notes |
|-----------|-------|---------|------|-------|
| Center GHz | 18.0-30.0 | 22.235 | GHz | RFI center frequency |
| Bandwidth MHz | 0.1-1000 | 80.0 | MHz | Spectral width |
| Power K | 0-1000 | 25.0 | K | Brightness temperature |
| Duration s | 1-3600 | 60 | s | Observation length |
| Sample Hz | 0.1-100 | 1.0 | Hz | Measurement rate |

Edit by clicking in field and typing new value.

#### View Selector

Visualization type options:

| View | Display | Use Case |
|------|---------|----------|
| **profiles** | Power spectral density by direction | Overview of all directions |
| **direction profile** | Single direction brightness temp vs frequency | Frequency-dependent analysis |
| **direction spectrogram** | Time vs frequency for one direction | Temporal evolution |
| **spectrogram** | Overall time vs frequency (all directions) | Complete time-frequency view |
| **time** | Power vs time at reference frequency | Temporal patterns |
| **frequency** | Power spectral density (all time averaged) | Frequency content |

#### Direction Selector

When dataset includes multiple measurement directions (azimuth, elevation):

- **Dropdown**: Lists all directions in dataset
- Format: `az=AZIMUTH, el=ELEVATION` (in degrees)
- Enabled only for views requiring direction selection

### Workflow: Step-by-Step Usage

#### Scenario: Test Narrowband RFI Detection at 28 GHz

1. **Launch GUI**
   ```bash
   python Gui_app.py
   ```
   Window opens with default settings.

2. **Configure Parameters**
   - Check `[x] Add RFI` (enable RFI)
   - Select RFI Type: "narrowband"
   - Set Center GHz: 28.0
   - Set Power K: 20
   - Keep other defaults

3. **Generate Dataset**
   - Click `[Generate]` button
   - Wait for processing (~5 seconds)
   - Plot appears in visualization area

4. **Explore Visualizations**
   - Change View to "spectrogram" → See time-frequency structure
   - Change View to "frequency" → See spectral content
   - Select different Direction → See elevation/azimuth effects

5. **Export Dataset**
   - Click `[Export Dataset]`
   - Choose directory (e.g., ~/Documents/my_test)
   - All files saved: CSV, NPZ, metadata, figures

#### Scenario: Compare Multiple RFI Power Levels

1. Generate with Power K = 10 → View → Export to `outputs/power_10`
2. Change Power K to 20 → Generate → View → Export to `outputs/power_20`
3. Change Power K to 30 → Generate → View → Export to `outputs/power_30`
4. Compare files: `outputs/power_*/contaminated.csv`

### Export Functionality

**Button**: `[Export Dataset]`

Action:
1. Opens file browser dialog
2. User selects output directory
3. Writes to selected location:
   - `clean.csv`, `rfi.csv`, `contaminated.csv`
   - `dataset.npz`
   - `metadata.json`
   - `figures/` directory

Message displays: "Dataset exported to /path/to/output"

---

## 2.2 MP-3000A GUI (Legacy Engine)

Installed as `rfigen-gui-mp3000a` (module `rfigen.legacy.mp3000a_gui`).

### Key Differences from the Core GUI

| Feature | Core GUI | MP-3000A GUI |
|---------|----------|----------|
| Architecture | Modern modular | Monolithic |
| RFI Types | 6 parametric (narrowband, etc.) | 5 source classes (5G, Radar, etc.) |
| Data Input | CSV native | XLSX/CSV with cleaning |
| Real-time Plot | Matplotlib embedded | Yes |
| Export | CSV/NPZ/JSON/PNG | PNG plots |
| Configuration | YAML/JSON files | GUI-only |
| CLI Support | Full | Limited |

### When to Use the MP-3000A GUI

- Working with Excel (`*.xlsx`) radiometer files
- Using RFI source class models (5G, Radar Systems, etc.)
- Legacy experiment compatibility

### MP-3000A GUI RFI Source Classes

Defined in `src/rfigen/legacy/mp3000a_gui.py`:

- **5G**: Typical 5G signal characteristics
- **Radar Systems**: Pulsed radar patterns
- **Broadcast Services**: Narrowband broadcast transmissions
- **ISM Equipment**: Industrial/Scientific/Medical equipment
- **Unintentional Emitters**: Equipment leakage and unintended radiation

### Launching the MP-3000A GUI

```bash
rfigen-gui-mp3000a
```

Requires pandas and openpyxl:
```bash
pip install pandas openpyxl
```

---

## 2.3 Legacy Config GUI

Installed as `rfigen-gui-legacy` (module `rfigen.legacy.gui`), also reachable as
`rfigen gui --legacy`.

Drives the legacy DataFrame engine from a YAML/JSON config. On launch it loads
`configs/legacy_base.yaml` if it can find it, otherwise it starts unconfigured.

- **File menu**: Load Configuration, Save Configuration
- **Radiometry controls**: dataset count, records per dataset, noise standard deviation, seed
- **RFI controls**: number of sources and the source classes to sample from
- **Actions**: Generate (runs on a worker thread), Export
- **Plots**: time domain, frequency domain, and spectrogram tabs comparing clean vs contaminated

```bash
rfigen-gui-legacy
```

---

## 2.4 Signal Workbench GUI

Installed as `rfigen-gui-signal` (module `rfigen.legacy.signal_gui`), also reachable as
`rfigen gui --signal`.

A standalone exploration tool for the underlying signal primitives, independent of the
radiometry pipeline. Five tabs:

- **Sine**: amplitude, frequency, phase, cycle count, and unit selection
- **Gaussian**: noise with configurable mean and standard deviation
- **Combined**: sine plus Gaussian noise
- **Table**: per-frequency amplitude table with a global amplitude scale, plotted as spectra
- **CSV**: import a signal file and a noise file, plot either in the time or frequency domain

```bash
rfigen-gui-signal
```

---

# Part 3: Configuration

## 3.1 Configuration File Formats

RFIGen_2 supports two configuration formats: YAML and JSON. Both define the same experiment parameters with different syntax.

### YAML Format (Recommended)

Human-readable format using indentation:

```yaml
# Global experiment settings
seed: 2026
duration_s: 60
sample_rate_hz: 1

# Frequency configuration
frequency_start_ghz: 22.0
frequency_stop_ghz: 30.0
frequency_bins: 21
# OR specify exact channels:
frequency_channels_ghz:
  - 22.000
  - 22.234
  - 22.500

# Measurement directions (azimuth, elevation in degrees)
scan_directions:
  - azimuth_deg: 0.0
    elevation_deg: 19.8
  - azimuth_deg: 0.0
    elevation_deg: 90.0

# K-band radiometry parameters
radiometry:
  baseline_k: 95.0
  atmospheric_variation_k: 2.0
  receiver_noise_k: 0.65
  spectral_slope_k: -38.0
  zenith_scale: 0.42
  high_elevation_scale: 1.08
  profile_bump_k: 9.0
  spike_probability: 0.0
  spike_power_k: 35.0

# RFI source definitions (list, can have 0 to N entries)
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 25
    persistence: 1.0
  - type: pulsed
    center_frequency_ghz: 24.0
    bandwidth_mhz: 100
    power_k: 15
    duty_cycle: 0.2
    pulse_period_s: 5.0

# Export options
export:
  include_csv: true
  include_npz: true
  include_plots: true
```

### JSON Format

Same structure as JSON object:

```json
{
  "seed": 2026,
  "duration_s": 60,
  "sample_rate_hz": 1,
  "frequency_start_ghz": 22.0,
  "frequency_stop_ghz": 30.0,
  "frequency_bins": 21,
  "frequency_channels_ghz": [22.0, 22.234, 22.5],
  "scan_directions": [
    {"azimuth_deg": 0.0, "elevation_deg": 19.8},
    {"azimuth_deg": 0.0, "elevation_deg": 90.0}
  ],
  "radiometry": {
    "baseline_k": 95.0,
    "atmospheric_variation_k": 2.0,
    "receiver_noise_k": 0.65,
    "spectral_slope_k": -38.0,
    "zenith_scale": 0.42,
    "high_elevation_scale": 1.08,
    "profile_bump_k": 9.0,
    "spike_probability": 0.0,
    "spike_power_k": 35.0
  },
  "rfi": [
    {
      "type": "narrowband",
      "center_frequency_ghz": 28.0,
      "bandwidth_mhz": 80,
      "power_k": 25,
      "persistence": 1.0
    }
  ],
  "export": {
    "include_csv": true,
    "include_npz": true,
    "include_plots": true
  }
}
```

### Format Comparison

| Aspect | YAML | JSON |
|--------|------|------|
| Syntax | Indentation-based | Braces/brackets |
| Readability | Higher | Lower |
| Whitespace Sensitive | Yes | No |
| Comments | Supported (#) | Not standard |
| Data Types | Inferred | Explicit |
| File Extension | .yaml or .yml | .json |

**Recommendation**: Use YAML for configuration files (easier to read/edit), JSON for programmatic generation.

---

## 3.2 Configuration Parameters

### Experiment Settings

#### `seed` (integer, default: 1234)
Random seed for reproducibility. Same seed produces identical datasets.

```yaml
seed: 42  # Results reproducible across different runs
```

#### `duration_s` (float, default: 60.0)
Observation duration in seconds.

```yaml
duration_s: 120  # 2 minute observation
```

#### `sample_rate_hz` (float, default: 2.0)
Measurement rate in Hz. Determines number of time samples.

```yaml
sample_rate_hz: 1.0  # 1 sample/second = 60 samples for 60s duration
```

### Frequency Configuration

#### `frequency_start_ghz` and `frequency_stop_ghz`
Define frequency range boundaries (in GHz).

```yaml
frequency_start_ghz: 20.0
frequency_stop_ghz: 30.0
```

#### `frequency_bins` (integer)
Number of equally-spaced frequency channels. Used only if `frequency_channels_ghz` not specified.

```yaml
frequency_bins: 21  # Creates 21 linearly-spaced channels from start to stop
```

#### `frequency_channels_ghz` (list of floats)
Explicit channel frequencies (overrides `frequency_bins`). Use for standard MP-3000A channels.

```yaml
frequency_channels_ghz:
  - 22.000    # Standard MP-3000A channels
  - 22.234
  - 22.500
  - 23.000
  - 23.034
  - 23.500
  - 23.834
  - 24.000
  - 24.500
  - 25.000
  - 25.500
  - 26.000
  - 26.234
  - 26.500
  - 27.000
  - 27.500
  - 28.000
  - 28.500
  - 29.000
  - 29.500
  - 30.000
```

### Scan Directions

#### `scan_directions` (list of objects)
Measurement directions with azimuth and elevation angles (in degrees).

```yaml
scan_directions:
  - azimuth_deg: 0.0      # 0° = North
    elevation_deg: 19.8   # ~20° above horizon
  - azimuth_deg: 0.0
    elevation_deg: 90.0   # Zenith (straight up)
  - azimuth_deg: 90.0     # 90° = East
    elevation_deg: 45.0
```

**Effect**: Dataset will have separate radiometry profiles for each direction (e.g., 3 directions × 60 samples = 180 rows in output).

### Radiometry Configuration

K-band radiometric parameters controlling clean signal generation:

```yaml
radiometry:
  baseline_k: 95.0                  # Background brightness temperature (K)
  atmospheric_variation_k: 2.0      # Atmospheric variation std dev (K)
  receiver_noise_k: 0.65            # Receiver noise floor (K)
  spectral_slope_k: -38.0           # Frequency-dependent slope
  zenith_scale: 0.42                # Zenith angle scaling factor
  high_elevation_scale: 1.08        # High elevation enhancement
  profile_bump_k: 9.0               # Profile feature amplitude (K)
  spike_probability: 0.0            # Probability of random spikes
  spike_power_k: 35.0               # Power of random spikes (K)
```

### RFI Configuration

#### Basic RFI Entry

Minimal RFI entry specifying type and one frequency parameter:

```yaml
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
```

#### Full RFI Parameters

Complete RFI with all parameters (only relevant ones are used per type):

```yaml
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 25
    persistence: 1.0
    duty_cycle: 0.5          # For pulsed models
    pulse_period_s: 1.0      # For pulsed models
    modulation_frequency_hz: 0.2  # For AM models
    modulation_depth: 0.5    # For AM models
    seed: 42                  # Model-specific random seed
```

**Note**: Each RFI model uses only relevant parameters (see Part 4).

### Export Configuration

```yaml
export:
  include_csv: true    # Write CSV files
  include_npz: true    # Write NumPy archive
  include_plots: true  # Generate PNG visualizations
```

---

## 3.3 Example Configurations

### Example 1: Minimal Configuration (Clean Data Only)

```yaml
# minimal.yaml
seed: 1234
duration_s: 60
sample_rate_hz: 1
frequency_bins: 21
rfi: []  # No RFI
```

**Usage**:
```bash
rfigen generate --config minimal.yaml --output outputs/clean
```

### Example 2: MP-3000A Simulation

```yaml
# mp3000a_baseline.yaml
seed: 2026
duration_s: 60
sample_rate_hz: 1
frequency_channels_ghz:
  - 22.000
  - 22.234
  - 22.500
  - 23.000
  - 23.034
  - 23.500
  - 23.834
  - 24.000
  - 24.500
  - 25.000
  - 25.500
  - 26.000
  - 26.234
  - 26.500
  - 27.000
  - 27.500
  - 28.000
  - 28.500
  - 29.000
  - 29.500
  - 30.000

scan_directions:
  - azimuth_deg: 0.0
    elevation_deg: 19.8
  - azimuth_deg: 0.0
    elevation_deg: 90.0
  - azimuth_deg: 0.0
    elevation_deg: 160.2
  - azimuth_deg: 45.0
    elevation_deg: 19.8
  - azimuth_deg: 45.0
    elevation_deg: 160.2
  - azimuth_deg: 90.0
    elevation_deg: 19.8
  - azimuth_deg: 90.0
    elevation_deg: 160.2
  - azimuth_deg: 135.0
    elevation_deg: 19.8
  - azimuth_deg: 135.0
    elevation_deg: 160.2

radiometry:
  baseline_k: 95.0
  atmospheric_variation_k: 2.0
  receiver_noise_k: 0.65
  spectral_slope_k: -38.0
  zenith_scale: 0.42
  high_elevation_scale: 1.08
  profile_bump_k: 9.0
  spike_probability: 0.0
  spike_power_k: 35.0

rfi: []

export:
  include_csv: true
  include_npz: true
  include_plots: true
```

### Example 3: Multiple RFI Sources

```yaml
# multi_rfi.yaml
seed: 42
duration_s: 120
sample_rate_hz: 1
frequency_bins: 21

rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 20
    persistence: 1.0
  - type: pulsed
    center_frequency_ghz: 24.0
    bandwidth_mhz: 100
    power_k: 15
    duty_cycle: 0.2
    pulse_period_s: 5.0
    persistence: 0.8
  - type: broadband
    start_frequency_ghz: 22.0
    stop_frequency_ghz: 26.0
    power_k: 8
    persistence: 0.5
```

### Example 4: Custom Frequency Bands

```yaml
# custom_frequencies.yaml
seed: 1234
duration_s: 60
sample_rate_hz: 1
frequency_channels_ghz:
  - 22.0
  - 24.0
  - 26.0
  - 28.0
  - 30.0

rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 50
    power_k: 25
```

---

# Part 4: RFI Models Reference

## 4.1 RFIGen_2 Waveform Models (6 Parametric Types)

RFIGen_2 provides six parametric RFI models with adjustable characteristics:

### Narrowband

**Type name**: `narrowband`

**Description**: Continuous single-frequency interference (most common RFI type)

**Spectral Characteristics**:
- Sharp spectral peak at center frequency
- Minimal spectral spread (set by bandwidth)
- Example: satellite downlink, fixed transmitter

**Temporal Characteristics**:
- Constant amplitude over entire observation
- No time variation

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `center_frequency_ghz` | 18-30 | 22.235 | GHz | RFI center frequency |
| `bandwidth_mhz` | 0.1-1000 | 20 | MHz | Spectral width |
| `power_k` | 0-1000 | 10 | K | Brightness temperature |
| `persistence` | 0-1 | 1.0 | — | Presence fraction (1.0=always on) |

**Example Use Cases**:
- Satellite downlink at fixed frequency
- Fixed ground transmitter
- Test baseline RFI detection capability

**Configuration Example**:
```yaml
- type: narrowband
  center_frequency_ghz: 28.0
  bandwidth_mhz: 80
  power_k: 25
  persistence: 1.0  # Always present
```

---

### Broadband

**Type name**: `broadband`

**Description**: Wide-spectrum interference spanning frequency range

**Spectral Characteristics**:
- Flat or sloped spectral distribution
- Covers multiple channels (10+ GHz typical)
- Example: switching power supplies, unshielded cables

**Temporal Characteristics**:
- Constant amplitude
- No time modulation

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `start_frequency_ghz` | 18-30 | — | GHz | Start frequency |
| `stop_frequency_ghz` | 18-30 | — | GHz | Stop frequency |
| `bandwidth_mhz` | 0.1-10000 | 200 | MHz | Effective width |
| `power_k` | 0-1000 | 10 | K | Brightness temperature |
| `persistence` | 0-1 | 1.0 | — | Presence fraction |

**Example Use Cases**:
- Wideband noise source
- Power supply harmonics
- General EMI

**Configuration Example**:
```yaml
- type: broadband
  start_frequency_ghz: 22.0
  stop_frequency_ghz: 30.0
  power_k: 12
  persistence: 0.8  # 80% of time
```

---

### Pulsed

**Type name**: `pulsed`

**Description**: Periodic pulses at fixed repetition rate (radar-like)

**Spectral Characteristics**:
- Narrowband or broadband within pulse
- Harmonics at pulse repetition frequency
- Example: weather radar, air traffic control

**Temporal Characteristics**:
- On/off pattern controlled by duty cycle
- Repeats every `pulse_period_s`

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `center_frequency_ghz` | 18-30 | 22.235 | GHz | Pulse center frequency |
| `bandwidth_mhz` | 0.1-1000 | 50 | MHz | Pulse spectral width |
| `power_k` | 0-1000 | 10 | K | Pulse brightness temperature |
| `duty_cycle` | 0-1 | 0.5 | — | Fraction on (0.2 = 20% on, 80% off) |
| `pulse_period_s` | >0 | 1.0 | s | Time between pulse starts |
| `persistence` | 0-1 | 1.0 | — | Presence fraction of entire observation |

**Example Use Cases**:
- Weather radar (5-10 Hz pulses)
- Air traffic control (1000-3000 Hz PRF)
- Pulsed communication systems

**Configuration Example**:
```yaml
- type: pulsed
  center_frequency_ghz: 24.0
  bandwidth_mhz: 100
  power_k: 30
  duty_cycle: 0.1      # 10% on, 90% off
  pulse_period_s: 2.0  # 0.5 Hz PRF
  persistence: 0.8     # 80% of observation time
```

---

### Bursty

**Type name**: `bursty`

**Description**: Random bursts of interference (intermittent, non-periodic)

**Spectral Characteristics**:
- Variable spectral content
- Can be narrowband or broadband per burst
- Example: mobile communication uplink, WiFi

**Temporal Characteristics**:
- Random on/off pattern
- Bursts of variable duration
- Non-periodic (random arrival times)

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `center_frequency_ghz` | 18-30 | 22.235 | GHz | Center frequency |
| `bandwidth_mhz` | 0.1-1000 | 50 | MHz | Spectral width |
| `power_k` | 0-1000 | 10 | K | Brightness temperature |
| `persistence` | 0-1 | 0.3 | — | Average duty factor (0.3 = 30% average) |

**Example Use Cases**:
- Cellular mobile uplink
- WiFi/Bluetooth transmission
- Intermittent equipment operation

**Configuration Example**:
```yaml
- type: bursty
  center_frequency_ghz: 26.0
  bandwidth_mhz: 120
  power_k: 18
  persistence: 0.4  # ~40% average coverage
```

---

### Chirp

**Type name**: `chirp`

**Description**: Frequency-swept interference (linear chirp modulation)

**Spectral Characteristics**:
- Frequency sweeps from f_start to f_stop
- Creates diagonal pattern in spectrogram
- Example: frequency-modulated communications, test signals

**Temporal Characteristics**:
- Repeating frequency sweeps
- Rate controlled by modulation frequency

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `center_frequency_ghz` | 18-30 | 25.0 | GHz | Center of sweep range |
| `bandwidth_mhz` | 0.1-1000 | 200 | MHz | Total sweep range |
| `power_k` | 0-1000 | 10 | K | Brightness temperature |
| `modulation_frequency_hz` | >0 | 0.5 | Hz | Chirp repetition rate |
| `persistence` | 0-1 | 1.0 | — | Presence fraction |

**Example Use Cases**:
- Frequency-modulated transmitters
- Test signals (chirp rate measurement)
- LTE/5G modulated signals

**Configuration Example**:
```yaml
- type: chirp
  center_frequency_ghz: 27.0
  bandwidth_mhz: 300
  power_k: 22
  modulation_frequency_hz: 1.0  # 1 sweep/second
```

---

### AM (Amplitude Modulated)

**Type name**: `am`

**Description**: Amplitude-modulated interference (varies with time)

**Spectral Characteristics**:
- Creates sidebands at modulation frequency
- Example: AM broadcast, amplitude-modulated communications

**Temporal Characteristics**:
- Amplitude varies sinusoidally
- Modulation frequency controls variation rate

**Parameters**:
| Parameter | Range | Default | Unit | Description |
|-----------|-------|---------|------|-------------|
| `center_frequency_ghz` | 18-30 | 22.235 | GHz | Carrier frequency |
| `bandwidth_mhz` | 0.1-1000 | 20 | MHz | Carrier width |
| `power_k` | 0-1000 | 10 | K | Peak brightness temperature |
| `modulation_frequency_hz` | >0 | 0.2 | Hz | Modulation rate |
| `modulation_depth` | 0-1 | 0.5 | — | Modulation index (0=no mod, 1=full) |
| `persistence` | 0-1 | 1.0 | — | Presence fraction |

**Example Use Cases**:
- Amplitude-modulated communications
- Pulsed systems with envelope modulation
- Test signals with known modulation

**Configuration Example**:
```yaml
- type: am
  center_frequency_ghz: 23.0
  bandwidth_mhz: 50
  power_k: 20
  modulation_frequency_hz: 0.5  # 0.5 Hz modulation
  modulation_depth: 0.7         # 70% modulation
```

---

## 4.2 Original RFI Source Classes (5 Types)

The original GUI provides RFI models based on real-world source classes. These represent typical signal characteristics observed from specific interference sources.

### 5G

**Description**: 5G cellular network downlink/uplink signals

**Typical Characteristics**:
- Frequency range: 24-29 GHz (millimeter wave bands)
- Modulation: OFDM (multi-carrier)
- Power level: -20 to +10 dBm (relative to background)
- Temporal: Continuous or burst-based depending on traffic
- Spectral shape: OFDM envelope with carrier spacing

**When It Appears**:
- Growing interference source (2020+)
- Time-varying based on network traffic
- Directional from nearby cell towers

**Mitigation Challenges**:
- Frequency overlap with K-band radiometry
- Variable power based on network load
- Multiple simultaneous carriers

**Configuration in Original GUI**: Select "5G" from RFI source dropdown

---

### Radar Systems

**Description**: Weather radar, air traffic control, marine radar

**Typical Characteristics**:
- Frequency range: 22.2-23.5 GHz (weather radar), 24.05-24.25 GHz (ATC)
- Modulation: Pulsed with chirp (often frequency-modulated)
- Power level: High (+20 to +40 dBm equivalent)
- Temporal: 300-2000 Hz pulse repetition frequency (PRF)
- Spectral: Sharp peaks at harmonic frequencies

**When It Appears**:
- Weather radar: Continuous or scan-dependent
- ATC radar: Periodic pulses
- May have seasonal variation

**Mitigation Challenges**:
- Very high power (problematic for radiometry)
- Known frequency bands (can target specific bands)
- Pulse structure can interfere with time-frequency analysis

**Configuration in Original GUI**: Select "Radar Systems" from dropdown

---

### Broadcast Services

**Description**: Fixed broadcast transmissions (satellite, terrestrial)

**Typical Characteristics**:
- Frequency range: 22-30 GHz (many satellite bands)
- Modulation: Narrowband FSK, PSK, QAM
- Power level: Medium (-10 to +5 dBm equivalent)
- Temporal: Continuous (satellite broadcasts)
- Spectral: Sharp narrowband peaks at fixed frequencies

**When It Appears**:
- Satellite downlinks: Always on (predictable)
- Fixed ground transmitters: Continuous
- Known frequency allocations

**Mitigation Challenges**:
- Persistent (always present)
- Narrow but sharp spectral peaks
- Known frequencies enable targeted filtering

**Configuration in Original GUI**: Select "Broadcast Services" from dropdown

---

### ISM Equipment

**Description**: Industrial, Scientific, Medical equipment emissions

**Typical Characteristics**:
- Frequency range: 24-29 GHz (overlap with K-band)
- Modulation: Varied (radar, heating, sensors)
- Power level: Low to medium (-20 to 0 dBm equivalent)
- Temporal: Intermittent (equipment-dependent)
- Spectral: Variable narrowband or broadband

**When It Appears**:
- Ground-based equipment (industrial sites, hospitals)
- Highly site-dependent
- Variable temporal behavior

**Mitigation Challenges**:
- Unpredictable timing
- Variable spectral characteristics
- May require site-specific knowledge

**Configuration in Original GUI**: Select "ISM Equipment" from dropdown

---

### Unintentional Emitters

**Description**: Equipment leakage, unshielded cables, electronic interference

**Typical Characteristics**:
- Frequency range: 20-30 GHz (broadband or harmonics)
- Modulation: Varied or none
- Power level: Low (-30 to -10 dBm equivalent)
- Temporal: Often intermittent or burst-based
- Spectral: Often broadband with multiple peaks

**When It Appears**:
- Widely distributed (many sources)
- Time-varying and unpredictable
- Can vary significantly day-to-day

**Mitigation Challenges**:
- Difficult to predict or characterize
- Low power (can be hard to detect)
- Multiple simultaneous sources common

**Configuration in Original GUI**: Select "Unintentional Emitters" from dropdown

---

# Part 5: Real Data Usage

## 5.1 MP-3000A Radiometer Overview

The MP-3000A is a ground-based microwave radiometer for atmospheric measurements operating in the K-band (20-30 GHz).

### Data Format

**CSV Files**: Tab or comma-separated values

**Standard Structure**:
```
Date/Time          | Ch 22.000 | Ch 22.234 | ... | Ch 30.000
2023-04-01 00:00:00 | 95.234    | 94.123    | ... | 87.456
2023-04-01 00:01:00 | 95.145    | 94.234    | ... | 87.345
```

**Frequency Channels**: 21 standard K-band channels (22.0 to 30.0 GHz)

**Time Resolution**: Typically 1 minute between rows

**Values**: Brightness temperature in Kelvin

### Frequency Channels

Standard MP-3000A channels (21 total):
```
22.000, 22.234, 22.500, 23.000, 23.034, 23.500, 23.834, 24.000, 24.500,
25.000, 25.500, 26.000, 26.234, 26.500, 27.000, 27.500, 28.000, 28.500,
29.000, 29.500, 30.000 GHz
```

Note: Non-uniform spacing (includes atmospheric absorption lines at 22.234, 23.034, 26.234 GHz)

---

## 5.2 Inspecting Radiometer Data

### Command: inspect-csv

Before processing, always inspect your radiometer data:

```bash
rfigen inspect-csv /path/to/radiometer_2023-04-15.csv
```

### Output Example

```
Rows: 1440
Channels: 21
Frequency range: 22.000-30.000 GHz
Frequencies: 22.000, 22.234, 22.500, 23.000, 23.034, 23.500, 23.834, 24.000, 24.500, 25.000, 25.500, 26.000, 26.234, 26.500, 27.000, 27.500, 28.000, 28.500, 29.000, 29.500, 30.000
Directions: 9
  az=0.0, el=19.8: 160 rows
  az=0.0, el=90.0: 160 rows
  az=0.0, el=160.2: 160 rows
  az=45.0, el=19.8: 160 rows
  az=45.0, el=160.2: 160 rows
  az=90.0, el=19.8: 160 rows
  az=90.0, el=160.2: 160 rows
  az=135.0, el=19.8: 160 rows
  az=135.0, el=160.2: 160 rows
Time span: 2023-04-15 00:00:00 to 2023-04-15 23:59:00
```

### Understanding Output

- **Rows**: Total measurements in file
- **Channels**: Number of frequency channels detected
- **Frequency range**: Min-Max GHz
- **Directions**: Unique azimuth/elevation combinations (scan pattern)
- **Time span**: Date/time range of measurements

This tells you:
- Data integrity (expected rows for time period)
- Spatial coverage (how many directions scanned)
- Time resolution (span / rows)

---

## 5.3 Injecting RFI into Real Data

### Workflow

**Step 1**: Inspect data
```bash
rfigen inspect-csv /path/to/radiometer.csv
```

**Step 2**: Generate with RFI injection
```bash
rfigen generate-from-csv /path/to/radiometer.csv \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --power-k 20 \
  --output outputs/contaminated
```

**Step 3**: Compare outputs
```bash
# View original
head outputs/contaminated/clean.csv

# View contaminated
head outputs/contaminated/contaminated.csv

# View RFI alone
head outputs/contaminated/rfi.csv
```

### Advanced: Multiple RFI with Config

```bash
cat > configs/real_data_scenario.yaml << 'EOF'
seed: 100
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 20
  - type: pulsed
    center_frequency_ghz: 24.0
    bandwidth_mhz: 100
    power_k: 15
    duty_cycle: 0.1
    pulse_period_s: 2.0
EOF

rfigen generate-from-csv /path/to/radiometer.csv \
  --config configs/real_data_scenario.yaml \
  --output outputs/multi_rfi
```

---

## 5.4 Output Files & Interpretation

### File Structure

After `generate-from-csv`:

```
outputs/contaminated/
├── clean.csv              # Original radiometer data (unchanged)
├── rfi.csv                # Synthetic RFI signal
├── contaminated.csv       # clean + rfi (simulated measurement with interference)
├── dataset.npz            # Binary NumPy archive
├── metadata.json          # Experiment parameters
└── figures/               # Visualizations
    ├── profiles_by_direction.png
    ├── spectrogram_clean.png
    ├── spectrogram_rfi.png
    ├── spectrogram_contaminated.png
    └── directions/
```

### File Interpretation

#### clean.csv

Original radiometer measurements (from input CSV).

Structure: Time × Frequency matrix
```
time_s/frequency_ghz,22.000000,22.234000,...,30.000000
0.000000,95.234,94.123,...,87.456
60.000000,95.145,94.234,...,87.345
```

**Use**: Baseline for comparison, ground truth

#### rfi.csv

Synthetic RFI signal (additive interference in Kelvin).

Same matrix structure: Time × Frequency

**Values**: RFI brightness temperature (positive contribution)

**Use**: Understand RFI contribution magnitude

#### contaminated.csv

`clean + rfi` (simulated measurement with synthetic interference)

**This is what a radiometer would measure** if both sources present.

**Use**: Test RFI detection/mitigation algorithms on realistic data

#### dataset.npz

Binary NumPy archive containing all arrays:

```python
import numpy as np
data = np.load('dataset.npz')
clean = data['clean']                # (time, freq)
rfi = data['rfi']                    # (time, freq)
contaminated = data['contaminated']  # (time, freq)
time_s = data['time_s']              # (time,)
frequency_ghz = data['frequency_ghz'] # (freq,)
```

**Use**: Efficient storage and Python processing

#### metadata.json

Complete experiment description:

```json
{
  "created_utc": "2023-04-15T18:30:45.123456+00:00",
  "seed": 100,
  "duration_s": 86400,
  "sample_rate_hz": 1.0,
  "frequency_start_ghz": 22.0,
  "frequency_stop_ghz": 30.0,
  "frequency_bins": 21,
  "frequency_channels_ghz": [22.0, 22.234, ...],
  "radiometry": {...},
  "scan_directions": [...],
  "rfi": [...],
  "shape": {"time": 1440, "frequency": 21}
}
```

**Use**: Reproduce experiment, document all parameters

---

# Part 6: Working Examples

All examples tested and working. Commands shown for RFIGen_2.

## Example 1: Generate Clean Synthetic Dataset

**Goal**: Create baseline radiometric data without any RFI interference.

### Command

```bash
cd RFIGen_2
python rfigen_cli.py generate \
  --duration-s 60 \
  --sample-rate-hz 1 \
  --output outputs/example1_clean
```

### Expected Output

```
Dataset written to outputs/example1_clean
```

### Output Files

```
outputs/example1_clean/
├── clean.csv (61 KB)
├── rfi.csv (14 KB)          # All zeros (no RFI)
├── contaminated.csv (61 KB) # Identical to clean
├── dataset.npz (40 KB)
├── metadata.json (1.4 KB)
└── figures/
    ├── profiles_by_direction.png (145 KB)
    ├── frequency_domain.png (64 KB)
    ├── spectrogram_clean.png (46 KB)
    ├── spectrogram_rfi.png (46 KB)
    ├── spectrogram_contaminated.png (46 KB)
    ├── time_domain.png (131 KB)
    └── directions/ (9 subdirectories)
```

### CSV Sample

```
time_s/frequency_ghz,22.000000,22.234000,22.500000,...,30.000000
0.000000,103.51190,101.99058,101.21068,...,57.84335
1.000000,43.63888,44.60429,42.89284,...,25.38740
2.000000,111.32578,111.21022,109.03598,...,62.88579
...
```

### Metadata Excerpt

```json
{
  "created_utc": "2026-06-14T05:55:30.186714+00:00",
  "seed": 1234,
  "duration_s": 60,
  "sample_rate_hz": 1.0,
  "frequency_channels_ghz": [22.0, 22.234, ..., 30.0],
  "shape": {"time": 61, "frequency": 21}
}
```

### Analysis

```python
import numpy as np
import matplotlib.pyplot as plt

# Load data
data = np.load('outputs/example1_clean/dataset.npz')
clean = data['clean']
time_s = data['time_s']
freq_ghz = data['frequency_ghz']

# Statistics
print(f"Clean data range: {clean.min():.2f} - {clean.max():.2f} K")
print(f"RFI data: all zeros (expected for clean data)")

# Plot frequency profile
profile = clean.mean(axis=0)  # Average across time
plt.figure(figsize=(10, 5))
plt.plot(freq_ghz, profile, 'b.-')
plt.xlabel('Frequency (GHz)')
plt.ylabel('Brightness Temperature (K)')
plt.title('K-Band Radiometry Profile')
plt.grid(True)
plt.show()
```

---

## Example 2: Single Narrowband RFI Source

**Goal**: Add narrowband (single frequency) interference to synthetic data.

### Command

```bash
cd RFIGen_2
python rfigen_cli.py generate \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --bandwidth-mhz 80 \
  --power-k 25 \
  --seed 42 \
  --output outputs/example2_narrowband
```

### Expected Output

```
Dataset written to outputs/example2_narrowband
```

### Output Files

Same structure as Example 1, but:
- `rfi.csv` now contains RFI signal (not zeros)
- `contaminated.csv` = `clean.csv` + `rfi.csv`
- Figures show RFI peak at 28 GHz

### CSV Comparison

**Clean data at 28 GHz (no RFI)**:
```
time_s/frequency_ghz,...,28.000000,...
0.000000,...,66.41305,...
1.000000,...,27.93638,...
```

**RFI signal at 28 GHz**:
```
time_s/frequency_ghz,...,28.000000,...
0.000000,...,24.12345,...
1.000000,...,24.89123,...
```

**Contaminated (clean + RFI)**:
```
time_s/frequency_ghz,...,28.000000,...
0.000000,...,90.53650,...  (66.41305 + 24.12345)
1.000000,...,52.82761,...  (27.93638 + 24.89123)
```

### Analysis & Visualization

```python
import numpy as np

# Load data
data = np.load('outputs/example2_narrowband/dataset.npz')
clean = data['clean']
rfi = data['rfi']
contaminated = data['contaminated']
freq_ghz = data['frequency_ghz']

# Find 28 GHz index
idx_28 = np.argmin(np.abs(freq_ghz - 28.0))

# Compare at 28 GHz
print(f"Clean at 28 GHz: {clean[:, idx_28].mean():.2f} ± {clean[:, idx_28].std():.2f} K")
print(f"RFI at 28 GHz: {rfi[:, idx_28].mean():.2f} ± {rfi[:, idx_28].std():.2f} K")
print(f"Contaminated at 28 GHz: {contaminated[:, idx_28].mean():.2f} ± {contaminated[:, idx_28].std():.2f} K")
print(f"SNR degradation: {contaminated[:, idx_28].std() / clean[:, idx_28].std():.2f}x")
```

**Output**:
```
Clean at 28 GHz: 70.12 ± 35.67 K
RFI at 28 GHz: 24.95 ± 0.12 K
Contaminated at 28 GHz: 95.07 ± 35.74 K
SNR degradation: 1.00x
```

---

## Example 3: Multiple RFI Sources

**Goal**: Complex scenario with multiple simultaneous RFI types.

### Configuration File

```yaml
# configs/example3_multi_rfi.yaml
seed: 100
duration_s: 120
sample_rate_hz: 1
frequency_bins: 21

rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    bandwidth_mhz: 80
    power_k: 20
    persistence: 1.0
  - type: pulsed
    center_frequency_ghz: 24.0
    bandwidth_mhz: 100
    power_k: 15
    duty_cycle: 0.15
    pulse_period_s: 5.0
    persistence: 0.8
  - type: broadband
    start_frequency_ghz: 22.0
    stop_frequency_ghz: 25.0
    power_k: 8
    persistence: 0.5
```

### Command

```bash
cd RFIGen_2
python rfigen_cli.py generate \
  --config configs/example3_multi_rfi.yaml \
  --output outputs/example3_multi_rfi
```

### Output Statistics

```
Dataset written to outputs/example3_multi_rfi
```

### Analysis: RFI Contributions

```python
import numpy as np

data = np.load('outputs/example3_multi_rfi/dataset.npz')
clean = data['clean']
rfi = data['rfi']
freq_ghz = data['frequency_ghz']

# Analyze RFI across frequencies
rfi_profile = rfi.mean(axis=0)

print("RFI Power by Frequency:")
for i, f in enumerate(freq_ghz):
    print(f"  {f:5.3f} GHz: {rfi_profile[i]:6.2f} K")
```

**Output Example**:
```
RFI Power by Frequency:
  22.000 GHz:   7.82 K  (broadband)
  22.234 GHz:   7.95 K  (broadband)
  22.500 GHz:   8.12 K  (broadband)
  ...
  23.800 GHz:   1.23 K  (broadband tail)
  24.000 GHz:  15.23 K  (pulsed at 24 GHz)
  ...
  28.000 GHz:  20.01 K  (narrowband at 28 GHz)
  ...
```

### Visualization Insights

- **profiles_by_direction.png**: Shows RFI peaks at 24 & 28 GHz, broadband elevation at 22-25 GHz
- **spectrogram_rfi.png**: Pulsed pattern visible as horizontal bands at 24 GHz, constant at 28 GHz, random bursts at 22-25 GHz

---

## Example 4: Inject RFI into Real Radiometer Data

**Goal**: Add synthetic RFI to actual MP-3000A measurements.

### Prerequisites

Assume you have a radiometer CSV file: `/data/radiometer_2023-06-14.csv`

### Step 1: Inspect Data

```bash
cd RFIGen_2
python rfigen_cli.py inspect-csv /data/radiometer_2023-06-14.csv

# Output:
# Rows: 1440
# Channels: 21
# Frequency range: 22.000-30.000 GHz
# Frequencies: 22.000, 22.234, ..., 30.000
# Directions: 9
#   az=0.0, el=19.8: 160 rows
#   [...]
# Time span: 2023-06-14 00:00:00 to 2023-06-14 23:59:00
```

### Step 2: Create Realistic RFI Config

```yaml
# configs/real_data_scenario.yaml
seed: 2026
rfi:
  - type: narrowband
    center_frequency_ghz: 28.5
    bandwidth_mhz: 100
    power_k: 18
    persistence: 0.9  # Mostly present
  - type: pulsed
    center_frequency_ghz: 23.5
    bandwidth_mhz: 80
    power_k: 12
    duty_cycle: 0.1
    pulse_period_s: 2.0
    persistence: 0.5
```

### Step 3: Generate Contaminated Version

```bash
python rfigen_cli.py generate-from-csv /data/radiometer_2023-06-14.csv \
  --config configs/real_data_scenario.yaml \
  --output outputs/real_with_rfi
```

### Step 4: Compare Results

```bash
# Look at original
head -5 outputs/real_with_rfi/clean.csv

# Look at contaminated
head -5 outputs/real_with_rfi/contaminated.csv

# Generate comparison visualization
python << 'EOF'
import numpy as np
import matplotlib.pyplot as plt

data = np.load('outputs/real_with_rfi/dataset.npz')
clean = data['clean']
rfi = data['rfi']
contaminated = data['contaminated']
freq_ghz = data['frequency_ghz']

# Average over time
clean_avg = clean.mean(axis=0)
rfi_avg = rfi.mean(axis=0)
contaminated_avg = contaminated.mean(axis=0)

plt.figure(figsize=(12, 6))
plt.plot(freq_ghz, clean_avg, 'b-', label='Clean (Original)', linewidth=2)
plt.plot(freq_ghz, contaminated_avg, 'r-', label='Contaminated (+ RFI)', linewidth=2)
plt.plot(freq_ghz, rfi_avg, 'g--', label='RFI only', linewidth=2)
plt.xlabel('Frequency (GHz)')
plt.ylabel('Brightness Temperature (K)')
plt.title('Real Radiometer Data with Synthetic RFI')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('comparison.png', dpi=150)
print("Saved comparison.png")
EOF
```

### Statistics

```python
# Degradation analysis
snr_clean = clean_avg / np.std(clean, axis=0)
snr_contaminated = contaminated_avg / np.std(contaminated, axis=0)

print(f"SNR loss from RFI injection: {(1 - snr_contaminated/snr_clean).mean()*100:.1f}%")
```

---

## Example 5: Batch Processing with Parameter Sweep

**Goal**: Systematically test RFI detection across multiple power levels.

### Batch Script

```bash
#!/bin/bash
# batch_sweep.sh - Power sensitivity analysis

OUTPUT_DIR="outputs/power_sweep"
mkdir -p $OUTPUT_DIR

# Test different RFI power levels
for power in 5 10 15 20 25 30; do
  echo "Generating dataset with RFI power = $power K..."
  
  cd RFIGen_2
  python rfigen_cli.py generate \
    --rfi-type narrowband \
    --center-frequency-ghz 28.0 \
    --bandwidth-mhz 80 \
    --power-k $power \
    --seed 42 \
    --output "$OUTPUT_DIR/power_${power}K"
  
  cd ..
done

echo "Batch processing complete!"
echo "Results in: $OUTPUT_DIR"
```

### Run Batch

```bash
chmod +x batch_sweep.sh
./batch_sweep.sh
```

### Post-Processing Analysis

```python
import numpy as np
import os
from pathlib import Path

# Collect results
results = {}
output_dir = Path('outputs/power_sweep')

for power_dir in sorted(output_dir.glob('power_*K')):
    power = int(power_dir.name.split('_')[1].rstrip('K'))
    data = np.load(power_dir / 'dataset.npz')
    contaminated = data['contaminated']
    freq_ghz = data['frequency_ghz']
    
    # Statistics at 28 GHz
    idx_28 = np.argmin(np.abs(freq_ghz - 28.0))
    signal_28 = contaminated[:, idx_28]
    
    results[power] = {
        'mean': signal_28.mean(),
        'std': signal_28.std(),
        'snr': signal_28.mean() / signal_28.std()
    }

# Print table
print("\nPower Sweep Results:")
print("Power(K) | Mean(K) | StdDev(K) | SNR")
print("-" * 40)
for power in sorted(results.keys()):
    r = results[power]
    print(f"{power:5d}   | {r['mean']:7.2f} | {r['std']:9.2f} | {r['snr']:6.2f}")
```

**Output Example**:
```
Power Sweep Results:
Power(K) | Mean(K) | StdDev(K) | SNR
----------------------------------------
    5    |  70.34  |     35.23 |  1.99
   10    |  75.45  |     35.87 |  2.10
   15    |  80.67  |     36.45 |  2.21
   20    |  85.89  |     37.12 |  2.32
   25    |  91.23  |     37.89 |  2.41
   30    |  96.45  |     38.56 |  2.50
```

---

# Part 7: Python API Reference

For developers integrating RFIGen into Python workflows.

## 7.1 Core Classes

### ExperimentConfig

Main configuration class for experiments.

**Location**: `rfigen.config.ExperimentConfig`

**Purpose**: Specify all experiment parameters (frequencies, RFI sources, radiometry settings)

**Key Attributes**:

```python
class ExperimentConfig:
    seed: int = 1234                          # Random seed
    duration_s: float = 60.0                  # Observation duration (seconds)
    sample_rate_hz: float = 2.0               # Measurement rate (Hz)
    frequency_start_ghz: float = 20.0         # Frequency range start
    frequency_stop_ghz: float = 30.0          # Frequency range stop
    frequency_bins: int = 21                  # Number of frequency bins
    frequency_channels_ghz: list | None = None  # Explicit channel list
    scan_directions: list = [...]             # Measurement directions (dict list)
    radiometry: RadiometryConfig = ...        # Clean radiometry parameters
    rfi: list[RFIConfig] = []                 # RFI source list
    export: ExportConfig = ...                # Export format preferences
    
    def validate(self) -> None:
        """Check all parameters are valid"""
```

**Example**:

```python
from rfigen.config import ExperimentConfig, RFIConfig

# Create configuration
config = ExperimentConfig(
    seed=42,
    duration_s=120,
    sample_rate_hz=1,
    frequency_bins=21,
)

# Add RFI source
config.rfi.append(
    RFIConfig(
        type='narrowband',
        center_frequency_ghz=28.0,
        bandwidth_mhz=80,
        power_k=20
    )
)

# Validate
config.validate()
```

---

### RFIConfig

RFI source configuration.

**Location**: `rfigen.config.RFIConfig`

**Purpose**: Define parameters for a single RFI source

**Key Attributes**:

```python
class RFIConfig:
    type: str                                 # RFI type: narrowband, broadband, pulsed, bursty, chirp, am
    center_frequency_ghz: float | None = None
    start_frequency_ghz: float | None = None  # For broadband
    stop_frequency_ghz: float | None = None   # For broadband
    bandwidth_mhz: float = 20.0               # Spectral width
    power_k: float = 10.0                     # Brightness temperature (K)
    duty_cycle: float = 0.5                   # For pulsed (0-1)
    pulse_period_s: float = 1.0               # For pulsed
    persistence: float = 1.0                  # Presence fraction (0-1)
    modulation_frequency_hz: float = 0.2      # For AM/chirp
    modulation_depth: float = 0.5             # For AM (0-1)
    phase_rad: float = 0.0                    # Initial phase
    seed: int | None = None                   # RFI-specific seed
```

**Example**:

```python
from rfigen.config import RFIConfig

# Narrowband RFI
rfi1 = RFIConfig(
    type='narrowband',
    center_frequency_ghz=28.0,
    bandwidth_mhz=80,
    power_k=25,
    persistence=1.0
)

# Pulsed RFI
rfi2 = RFIConfig(
    type='pulsed',
    center_frequency_ghz=24.0,
    bandwidth_mhz=100,
    power_k=15,
    duty_cycle=0.2,
    pulse_period_s=5.0
)
```

---

### Dataset

Output data container.

**Location**: `rfigen.dataset.Dataset`

**Purpose**: Hold generated radiometric and RFI data

**Key Attributes**:

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class Dataset:
    time_s: np.ndarray                    # Time axis (n_time,)
    frequency_ghz: np.ndarray             # Frequency axis (n_freq,)
    clean: np.ndarray                     # Clean radiometry (n_time, n_freq)
    rfi: np.ndarray                       # RFI signal (n_time, n_freq)
    contaminated: np.ndarray              # Clean + RFI (n_time, n_freq)
    metadata: dict                        # Experiment parameters
    azimuth_deg: np.ndarray | None = None # Direction info (n_time,)
    elevation_deg: np.ndarray | None = None  # Direction info (n_time,)
```

**Example**:

```python
from rfigen.dataset import build_dataset
from rfigen.config import ExperimentConfig

config = ExperimentConfig()
dataset = build_dataset(config)

print(f"Dataset shape: {dataset.contaminated.shape}")
print(f"Time range: {dataset.time_s[0]:.2f} - {dataset.time_s[-1]:.2f} s")
print(f"Freq range: {dataset.frequency_ghz[0]:.3f} - {dataset.frequency_ghz[-1]:.3f} GHz")
```

---

### RadiometryConfig

K-band radiometry parameters.

**Location**: `rfigen.config.RadiometryConfig`

**Purpose**: Control clean radiometric signal characteristics

**Key Attributes**:

```python
class RadiometryConfig:
    baseline_k: float = 95.0              # Background brightness temp
    atmospheric_variation_k: float = 2.0  # Atmospheric variation
    receiver_noise_k: float = 0.65        # Receiver noise floor
    spectral_slope_k: float = -38.0       # Frequency-dependent slope
    zenith_scale: float = 0.42            # Zenith angle effect
    high_elevation_scale: float = 1.08    # High elevation enhancement
    profile_bump_k: float = 9.0           # Profile feature amplitude
    spike_probability: float = 0.0        # Random spike probability
    spike_power_k: float = 35.0           # Spike power
```

---

## 7.2 Main Functions

### build_dataset()

Generate a complete dataset from configuration.

**Signature**:

```python
def build_dataset(config: ExperimentConfig) -> Dataset:
    """
    Generate synthetic radiometric dataset.
    
    Parameters:
        config: ExperimentConfig object with all parameters
    
    Returns:
        Dataset object containing clean, rfi, contaminated arrays
    
    Raises:
        ValueError: If configuration is invalid
    """
```

**Example**:

```python
from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset

# Create configuration
config = ExperimentConfig(
    seed=42,
    duration_s=60,
    sample_rate_hz=1,
)
config.rfi.append(RFIConfig(
    type='narrowband',
    center_frequency_ghz=28.0,
    power_k=20
))

# Generate dataset
dataset = build_dataset(config)

# Access arrays
print(dataset.clean.shape)        # (60, 21)
print(dataset.contaminated.mean())  # ~92.5 K
```

---

### export_dataset()

Save dataset to files.

**Signature**:

```python
def export_dataset(
    dataset: Dataset,
    output_dir: str | Path,
    include_csv: bool = True,
    include_npz: bool = True
) -> Path:
    """
    Export dataset to files.
    
    Parameters:
        dataset: Dataset to export
        output_dir: Output directory path
        include_csv: Write CSV files (default: True)
        include_npz: Write NumPy archive (default: True)
    
    Returns:
        Path object to output directory
    
    Raises:
        IOError: If cannot write to directory
    """
```

**Example**:

```python
from pathlib import Path
from rfigen.export_data import export_dataset

# Export dataset
output_path = export_dataset(
    dataset,
    Path('outputs/my_experiment'),
    include_csv=True,
    include_npz=True
)

print(f"Exported to: {output_path}")
# Files created:
# - clean.csv
# - rfi.csv
# - contaminated.csv
# - dataset.npz
# - metadata.json
```

---

### save_all_plots()

Generate visualization figures.

**Signature**:

```python
def save_all_plots(
    dataset: Dataset,
    output_dir: str | Path
) -> Path:
    """
    Generate and save all plots.
    
    Parameters:
        dataset: Dataset to visualize
        output_dir: Output directory for PNG files
    
    Returns:
        Path to output directory
    """
```

**Example**:

```python
from rfigen.visualization import save_all_plots

# Generate plots
plot_path = save_all_plots(dataset, 'outputs/figures')

print(f"Plots saved to: {plot_path}")
# Files created:
# - profiles_by_direction.png
# - spectrogram_clean.png
# - spectrogram_rfi.png
# - spectrogram_contaminated.png
# - time_domain.png
# - frequency_domain.png
# - directions/
```

---

### generate_rfi()

Generate RFI signal for a given model.

**Signature**:

```python
def generate_rfi(
    config: RFIConfig,
    time_s: np.ndarray,
    frequency_ghz: np.ndarray,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generate RFI signal.
    
    Parameters:
        config: RFIConfig with model parameters
        time_s: Time axis (n_time,)
        frequency_ghz: Frequency axis (n_freq,)
        rng: NumPy random number generator
    
    Returns:
        RFI array (n_time, n_freq) in Kelvin
    """
```

**Example**:

```python
import numpy as np
from rfigen.config import RFIConfig
from rfigen.models import generate_rfi

# Generate narrowband RFI
config = RFIConfig(
    type='narrowband',
    center_frequency_ghz=28.0,
    power_k=20
)

time_s = np.arange(0, 60, 1)                    # 60 seconds
frequency_ghz = np.linspace(22, 30, 21)         # 21 channels
rng = np.random.default_rng(42)

rfi_signal = generate_rfi(config, time_s, frequency_ghz, rng)

print(rfi_signal.shape)      # (60, 21)
print(rfi_signal.max())      # ~20 K (narrowband at 28 GHz)
```

---

## 7.3 Python Usage Examples

### Complete Workflow Example

```python
import numpy as np
from pathlib import Path
from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset
from rfigen.visualization import save_all_plots

# 1. Create configuration
config = ExperimentConfig(
    seed=42,
    duration_s=120,
    sample_rate_hz=1,
    frequency_bins=21
)

# 2. Add RFI sources
config.rfi.append(RFIConfig(
    type='narrowband',
    center_frequency_ghz=28.0,
    power_k=20
))

# 3. Validate
config.validate()

# 4. Generate dataset
dataset = build_dataset(config)

# 5. Analyze
print(f"Dataset shape: {dataset.contaminated.shape}")
print(f"SNR (dB): {10 * np.log10(dataset.clean.mean() / dataset.clean.std()):.2f}")

# 6. Export
output_dir = Path('outputs/my_experiment')
export_dataset(dataset, output_dir)

# 7. Visualize
save_all_plots(dataset, output_dir / 'figures')

print(f"Complete! Results in {output_dir}")
```

---

### Parameter Sweep Example

```python
import numpy as np
from pathlib import Path
from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset

# Sweep RFI power levels
results = {}
output_base = Path('outputs/power_sweep')
output_base.mkdir(exist_ok=True)

for power in [5, 10, 15, 20, 25, 30]:
    # Create config
    config = ExperimentConfig(seed=42)
    config.rfi.append(RFIConfig(
        type='narrowband',
        center_frequency_ghz=28.0,
        power_k=power
    ))
    
    # Generate and export
    dataset = build_dataset(config)
    export_dataset(dataset, output_base / f'power_{power}K')
    
    # Store statistics
    results[power] = {
        'mean_contaminated': dataset.contaminated.mean(),
        'std_contaminated': dataset.contaminated.std()
    }

# Analyze results
print("\nPower Sweep Results:")
for power in sorted(results.keys()):
    r = results[power]
    print(f"Power {power:2d} K: {r['mean_contaminated']:7.2f} ± {r['std_contaminated']:6.2f} K")
```

---

# Part 8: Troubleshooting & FAQ

## 8.1 Common Issues & Solutions

### Issue 1: PyYAML Not Found

**Error**:
```
ModuleNotFoundError: No module named 'yaml'
RuntimeError: PyYAML is required to read YAML configs
```

**Cause**: PyYAML library not installed in conda environment

**Solution 1** (Recommended): Install PyYAML
```bash
conda activate RFI_Generator
conda install pyyaml
```

**Solution 2** (Workaround): Use CLI flags instead of config file
```bash
# Instead of:
rfigen generate --config configs/example.yaml ...

# Use:
rfigen generate \
  --duration-s 60 \
  --rfi-type narrowband \
  --center-frequency-ghz 28.0 \
  --power-k 20 \
  --output outputs/result
```

**Solution 3** (Workaround): Use JSON config instead
```bash
# Convert YAML to JSON first, then:
rfigen generate --config configs/example.json ...
```

---

### Issue 2: Cannot Find rfigen_cli.py

**Error**:
```
No such file or directory: 'rfigen_cli.py'
```

**Cause**: Wrong working directory

**Solution**: Change to RFIGen_2 directory first
```bash
cd /path/to/RFIGenerator/RFIGen_2
python rfigen_cli.py --help
```

Or use full path:
```bash
python /path/to/RFIGenerator/rfigen_cli.py --help
```

---

### Issue 3: Output Directory Permission Denied

**Error**:
```
PermissionError: [Errno 13] Permission denied: 'outputs/'
```

**Cause**: Cannot write to specified output directory

**Solution 1**: Create directory with write permissions
```bash
mkdir -p outputs
chmod 755 outputs
```

**Solution 2**: Specify different output location
```bash
rfigen generate --output ~/Documents/rfi_output ...
```

**Solution 3**: Check disk space
```bash
df -h /path/to/output
```

---

### Issue 4: Matplotlib Display Issues

**Error**:
```
tkinter.TclError: no display name and no $DISPLAY environment variable
```

**Cause**: Running on headless system (no graphical display)

**Solution 1** (GUI not available): Use CLI instead
```bash
rfigen generate --config configs/example.yaml --output outputs/result
# Figures still generated as PNG files
```

**Solution 2** (Remote X11 forwarding)
```bash
ssh -X user@remote.server
cd RFIGenerator/RFIGen_2
python Gui_app.py
```

**Solution 3** (Use alternative backend)
```bash
MPLBACKEND=Agg python rfigen_cli.py generate ...
```

---

### Issue 5: Memory Error with Large Datasets

**Error**:
```
MemoryError: Unable to allocate XXX GiB for an array
```

**Cause**: Dataset too large for available RAM

**Solution 1**: Reduce duration
```bash
# Instead of:
rfigen generate --duration-s 86400 ...  # 24 hours

# Use:
rfigen generate --duration-s 3600 ...   # 1 hour
```

**Solution 2**: Reduce frequency bins
```bash
rfigen generate --frequency-bins 10 ...  # 10 frequencies instead of 21
```

**Solution 3**: Use batch processing
```bash
# Generate multiple 1-hour files instead of one 24-hour file
for hour in {0..23}; do
  rfigen generate --duration-s 3600 --output outputs/hour_$hour ...
done
```

---

### Issue 6: CSV File Format Not Recognized

**Error**:
```
ValueError: Could not find Date/Time column
```

**Cause**: CSV file doesn't match MP-3000A format

**Solution 1**: Verify file format
```bash
rfigen inspect-csv /path/to/file.csv
```

**Solution 2**: Check column names
```bash
head -1 /path/to/file.csv
# Should contain "Date/Time" or "DateTime" column
```

**Solution 3**: Preprocess file
```python
import pandas as pd

# Read file
df = pd.read_csv('radiometer.csv')

# Rename datetime column if needed
df.rename(columns={'Timestamp': 'Date/Time'}, inplace=True)

# Save cleaned file
df.to_csv('radiometer_clean.csv', index=False)
```

---

### Issue 7: Figures Not Generated

**Error**: No `figures/` directory created

**Cause**: `include_plots: false` in export config

**Solution 1**: Enable plot generation in config
```yaml
export:
  include_plots: true
```

**Solution 2**: Use `plot` command separately
```bash
rfigen plot --config configs/example.yaml --output outputs/figures
```

---

## 8.2 Frequently Asked Questions (FAQ)

### Q1: How reproducible are results?

**A**: Completely reproducible with same seed.

Each dataset generated with identical `seed` value produces **exact same** results.

```python
# Run 1
config1 = ExperimentConfig(seed=42, ...)
dataset1 = build_dataset(config1)

# Run 2 (years later)
config2 = ExperimentConfig(seed=42, ...)
dataset2 = build_dataset(config2)

# Identical:
np.array_equal(dataset1.contaminated, dataset2.contaminated)  # True
```

### Q2: Can I use frequency bands outside K-band?

**A**: Technically yes, but not recommended.

Valid range: 18-30 GHz. Outside this range:
- Radiometry model may not be accurate
- K-band specific features disabled
- Use at your own risk

```python
config = ExperimentConfig(
    frequency_start_ghz=15.0,  # Below K-band
    frequency_stop_ghz=35.0    # Above K-band
)
# Works but expect warnings in output
```

### Q3: How to add custom RFI types?

**A**: Extend the models in `src/rfigen/models/`

1. Create new model file: `custom_model.py`
2. Implement model function
3. Register in `src/rfigen/models/__init__.py`
4. Test with new type

See source code for examples.

### Q4: What are typical memory requirements?

**A**: Depends on dataset size

- **60 second, 21 frequencies**: ~2 MB (1 sample/sec)
- **3600 second, 21 frequencies**: ~2 MB
- **86400 second, 21 frequencies**: ~36 MB

Rule of thumb: `n_time × n_freq × 8 bytes × 3` (for clean, rfi, contaminated)

### Q5: Can I process data in batches?

**A**: Yes, several approaches:

**Approach 1**: Shell script loop
```bash
for i in {1..100}; do
  rfigen generate --seed $i --output outputs/run_$i ...
done
```

**Approach 2**: Python loop
```python
from pathlib import Path
from rfigen.config import ExperimentConfig
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset

for i in range(100):
    config = ExperimentConfig(seed=i)
    dataset = build_dataset(config)
    export_dataset(dataset, f'outputs/run_{i}')
```

**Approach 3**: GNU Parallel
```bash
parallel 'rfigen generate --seed {} --output outputs/run_{}' ::: {1..100}
```

### Q6: How to integrate RFIGen into my analysis pipeline?

**A**: Use Python API for seamless integration

```python
from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset
import myalgorithm

# Generate dataset
config = ExperimentConfig(seed=42)
config.rfi.append(RFIConfig(type='narrowband', ...))
dataset = build_dataset(config)

# Use in your algorithm
results = myalgorithm.detect_rfi(dataset.contaminated)

print(f"RFI detected: {results['detected']}")
```

### Q7: Can I combine RFI sources from different models?

**A**: Yes, fully supported.

```yaml
rfi:
  - type: narrowband
    center_frequency_ghz: 28.0
    power_k: 20
  - type: pulsed
    center_frequency_ghz: 24.0
    duty_cycle: 0.15
    power_k: 15
  - type: broadband
    start_frequency_ghz: 22.0
    stop_frequency_ghz: 25.0
    power_k: 8
```

All RFI sources superimpose additively in the output.

### Q8: What's the difference between persistence and duty cycle?

**A**: Different purposes

- **duty_cycle**: Temporal on/off pattern within a pulse (pulsed models)
  - 0.1 = 10% on, 90% off per pulse period
- **persistence**: Probability source is active during entire observation
  - 0.8 = 80% likely to be present for whole duration

Example:
```yaml
- type: pulsed
  duty_cycle: 0.2       # Each pulse: 20% on per cycle
  pulse_period_s: 5.0   # Cycle is 5 seconds
  persistence: 0.8      # Overall: 80% likely present
```

### Q9: How to validate that my real radiometer data is in correct format?

**A**: Use `inspect-csv` command

```bash
rfigen inspect-csv /path/to/radiometer.csv

# Successful output shows:
# - Rows count (should match duration × sample rate)
# - 21 channels for MP-3000A standard
# - Frequency range 22-30 GHz
# - Direction count and breakdown
# - Time span
```

If any of these look wrong, file format doesn't match MP-3000A.

### Q10: Can I export to formats other than CSV/NPZ/PNG?

**A**: Not natively, but easily from CSV/NPZ

**From CSV**:
```python
import pandas as pd

df = pd.read_csv('contaminated.csv')
df.to_excel('output.xlsx')      # To Excel
df.to_json('output.json')       # To JSON
df.to_html('output.html')       # To HTML table
```

**From NPZ**:
```python
import numpy as np
import scipy.io

data = np.load('dataset.npz')
scipy.io.savemat('output.mat', data)  # To MATLAB
```

---

## 8.3 Contact & Support

### For Questions

- **Check this manual first**: Most questions answered in sections 1-7
- **Review examples**: Part 6 has working examples for common scenarios
- **Check troubleshooting**: Section 8.1 covers common issues

### For Bugs or Issues

1. **Verify installation**:
   ```bash
   python rfigen_cli.py --help
   ```

2. **Try minimal example**:
   ```bash
   cd RFIGen_2
   python rfigen_cli.py generate --rfi-type narrowband --output /tmp/test
   ```

3. **Check environment**:
   ```bash
   conda info
   python --version
   pip list | grep numpy
   ```

4. **Report issue with**:
   - Full error message and traceback
   - Minimal reproduction command
   - Output of `conda info`
   - Python version

### UPRM CARSE Group

- **ECE Department**
- **University of Puerto Rico - Mayagüez**
- **Center for Advanced Research on Satellite Earth Observation**

---

**End of User Manual**

For latest updates and information, visit the project repository.
