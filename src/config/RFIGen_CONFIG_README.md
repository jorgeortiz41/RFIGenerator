
# RFIGen Configuration File Reference

This document defines the structure and meaning of every field supported in RFIGen YAML/JSON configuration files.
It is intended for researchers generating synthetic K-band radiometric datasets.

The configuration file controls the entire signal-generation pipeline:

Configuration → Radiometry → RFI Generation → Composition → Dataset → Export → Visualization → Interfaces

---

# Top-Level Structure

A valid configuration file may contain the following sections:

project
run
frequency
radiometry
rfi_sources
composition
dataset
export
visualization
interfaces
validation

Only `project`, `run`, `frequency`, `composition`, `dataset`, and `export` are strictly required.
Other sections are optional but recommended.

---

# project

Metadata describing the experiment.

name: Project name  
version: Configuration version  
profile: Preset identifier  
description: Human-readable explanation  

---

# run

Controls sampling resolution and reproducibility.

seed: RNG seed for reproducibility  
n_samples: Number of samples per signal  
sample_rate_hz: Sampling frequency  
duration_s: Signal duration (must equal n_samples / sample_rate_hz)  
output_prefix: Prefix for exported filenames  

---

# frequency

Defines spectral observation window.

band.min_ghz: Lower band boundary  
band.max_ghz: Upper band boundary  
center_ghz: Center observation frequency  
span_mhz: Total spectral span  

---

# radiometry (optional)

Controls clean baseline atmospheric signal.

baseline_type: Radiometric model name  
mean_tb_k: Mean brightness temperature  
variability_tb_k: Natural variation  
instrument_noise_std_k: Sensor noise  
drift_per_second_k: Slow temporal drift  

Optional atmosphere subfields:

water_vapor_profile: Atmospheric profile model  
cloud_liquid_water_mm: Cloud contribution  
air_mass_factor: Elevation-dependent scaling  

---

# rfi_sources

List of synthetic interference emitters.

Each entry represents one transmitter.

Common fields:

id: Unique emitter name  
type: Signal model  
enabled: Enable/disable emitter  
center_offset_mhz: Offset from center frequency  
bandwidth_mhz: Spectral width  
power_dbm: Signal strength  
persistence: Fraction of time signal exists  
modulation: Modulation type  

Supported types:

narrowband
broadband
pulsed
bursty
time_varying_frequency
amplitude_modulated

Extra parameters per type:

pulsed:
duty_cycle: Fraction of time active  
pulse_period_ms: Pulse repetition interval  

bursty:
burst_rate_hz: Bursts per second  
burst_duration_ms: Burst length  

---

# composition

Controls contamination injection.

inject_rfi: Enable contamination  
contamination_target: clean_only / contaminated_only / both  
amplitude_scaling_mode: linear / db  
spectral_overlap_policy: add_power / overwrite / clip  
domain_match: time / frequency / time_frequency  
snr_db: Target signal-to-noise ratio  
normalize_output: Normalize final amplitude  

---

# dataset

Controls dataset creation behavior.

dataset_name: Dataset identifier  
records: Number of generated signals  
save_clean: Export clean signals  
save_contaminated: Export contaminated signals  
save_metadata: Export metadata  
include_labels: Include classification labels  

Optional split:

train / validation / test must sum to 1.0

Optional labels:

contaminated_flag: Binary contamination indicator  
source_type: RFI type label  
source_count: Number of emitters  

---

# export

Controls output formats and directories.

directory: Output folder  
formats.csv: Save CSV dataset  
formats.json_metadata: Save metadata JSON  
formats.mp3000a_style: Save MP-3000A-compatible format  
formats.npy: Save NumPy arrays  
filenames.clean: Clean dataset filename  
filenames.contaminated: Contaminated filename  
filenames.metadata: Metadata filename  
overwrite: Allow overwrite  

---

# visualization

Controls automatic plotting.

enabled: Enable plotting  
save_figures: Save plots to disk  
figure_directory: Plot output folder  
products.time_domain: Plot waveform  
products.frequency_spectrum: Plot FFT  
products.spectrogram: Plot spectrogram  

---

# interfaces

Controls CLI and GUI behavior.

cli.enabled: Enable CLI usage  
cli.allow_parameter_overrides: Allow runtime overrides  

gui.enabled: Enable GUI  
gui.realtime_preview: Live visualization updates  

---

# validation

Controls configuration safety enforcement.

enforce_k_band_limits: Restrict frequency range  
require_physical_plausibility: Reject unrealistic signals  
fail_on_invalid_ranges: Stop execution on invalid config  
