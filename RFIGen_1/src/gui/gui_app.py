"""RFI Generator GUI Application"""
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from RFIGen_1.src.config.config_loader import load_config, save_config
from RFIGen_1.src.models.radiometry import generate_synthetic_dataset
from RFIGen_1.src.models.signal_mixer import generate_rfi_sources, mix_signals


class RFIGeneratorGUI:
    """Main GUI application for RFI Generator."""

    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("RFI Generator - K-band RFI Synthesis Tool")
        self.root.geometry("1400x900")
        
        self.config: Dict[str, Any] = {}
        self.current_config_path: Optional[Path] = None
        self.generated_data: Optional[pd.DataFrame] = None
        self.mixed_data: Optional[pd.DataFrame] = None
        self.rfi_info: Dict[str, Any] = {}
        
        self._create_ui()
        self._load_default_config()
        
    def _create_ui(self) -> None:
        """Create the user interface."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Configuration", command=self._load_config)
        file_menu.add_command(label="Save Configuration", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        left_frame = ttk.Frame(main_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self._create_radiometry_controls(left_frame)
        self._create_rfi_controls(left_frame)
        self._create_action_buttons(left_frame)
        
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.time_frame = ttk.Frame(self.notebook)
        self.freq_frame = ttk.Frame(self.notebook)
        self.spec_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.time_frame, text="Time Domain")
        self.notebook.add(self.freq_frame, text="Frequency Domain")
        self.notebook.add(self.spec_frame, text="RFI Map")
        
        self.time_canvas = None
        self.freq_canvas = None
        self.spec_canvas = None
        
    def _create_radiometry_controls(self, parent: ttk.Frame) -> None:
        """Create radiometry configuration controls."""
        frame = ttk.LabelFrame(parent, text="Radiometry Settings", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="Datasets:").grid(row=0, column=0, sticky=tk.W)
        self.n_datasets = ttk.Spinbox(frame, from_=1, to=100, width=10)
        self.n_datasets.set(5)
        self.n_datasets.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(frame, text="Noise Std (K):").grid(row=1, column=0, sticky=tk.W)
        self.noise_std = ttk.Spinbox(frame, from_=0.0, to=10.0, increment=0.1, width=10)
        self.noise_std.set(0.5)
        self.noise_std.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(frame, text="Seed:").grid(row=2, column=0, sticky=tk.W)
        self.seed = ttk.Spinbox(frame, from_=0, to=999999, width=10)
        self.seed.set(12345)
        self.seed.grid(row=2, column=1, sticky=tk.W)
        
    def _create_rfi_controls(self, parent: ttk.Frame) -> None:
        """Create RFI configuration controls."""
        frame = ttk.LabelFrame(parent, text="RFI Settings", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame, text="RFI Sources:").grid(row=0, column=0, sticky=tk.W)
        self.n_sources = ttk.Spinbox(frame, from_=0, to=20, width=10)
        self.n_sources.set(3)
        self.n_sources.grid(row=0, column=1, sticky=tk.W)
        
        self.source_types_var = {}
        source_types = ["satellite", "aircraft", "ground", "narrowband", "pulsed"]
        for i, stype in enumerate(source_types):
            var = tk.BooleanVar(value=(i < 3))
            self.source_types_var[stype] = var
            ttk.Checkbutton(frame, text=stype, variable=var).grid(
                row=2+i//2, column=1+i%2, sticky=tk.W
            )
    
    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create action buttons."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=20)
        
        self.generate_btn = ttk.Button(
            frame, text="Generate Data", command=self._on_generate
        )
        self.generate_btn.pack(fill=tk.X, pady=5)
        
        self.export_btn = ttk.Button(
            frame, text="Export Data", command=self._on_export, state=tk.DISABLED
        )
        self.export_btn.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(frame, text="Ready", foreground="blue")
        self.status_label.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=5)
    
    def _load_default_config(self) -> None:
        """Load default configuration."""
        config_path = Path(__file__).parent.parent / "config" / "examples" / "base_config.yaml"
        if config_path.exists():
            try:
                self.config = load_config(config_path)
                self.current_config_path = config_path
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.config = load_config(Path(file_path))
                self.current_config_path = Path(file_path)
                messagebox.showinfo("Success", "Configuration loaded!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        if not self.current_config_path:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".yaml",
                filetypes=[("YAML files", "*.yaml *.yml")]
            )
            if not file_path:
                return
            self.current_config_path = Path(file_path)
        
        try:
            self.config["run"]["n_datasets"] = int(self.n_datasets.get())
            self.config["radiometry"]["noise_std_k"] = float(self.noise_std.get())
            self.config["run"]["seed"] = int(self.seed.get())
            
            save_config(self.current_config_path, self.config)
            messagebox.showinfo("Success", f"Saved to {self.current_config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")
    
    def _on_generate(self) -> None:
        """Generate synthetic data with RFI."""
        self.generate_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Generating...", foreground="orange")
        self.root.update()
        
        thread = threading.Thread(target=self._generate_data)
        thread.daemon = True
        thread.start()
    
    def _generate_data(self) -> None:
        """Generate data in background thread."""
        try:
            n_datasets = int(self.n_datasets.get())
            noise_std = float(self.noise_std.get())
            seed = int(self.seed.get())
            n_sources = int(self.n_sources.get())
            
            selected_types = [k for k, v in self.source_types_var.items() if v.get()]
            source_classes = selected_types if selected_types else ["satellite"]
            
            rng = np.random.default_rng(seed)
            self.generated_data = generate_synthetic_dataset(
                n_dataframes=n_datasets,
                noise_std=noise_std,
                seed=seed,
                output_dir="outputs/"
            )
            
            if isinstance(self.generated_data, pd.DataFrame):
                self.generated_data = [self.generated_data]
            
            if n_sources > 0:
                sources = generate_rfi_sources(n_sources, source_classes, rng)
                self.mixed_data, self.rfi_info = mix_signals(
                    self.generated_data, sources, rng
                )
            else:
                self.mixed_data = self.generated_data
                self.rfi_info = {}
            
            self.root.after(0, self._update_visualizations)
            self.root.after(0, lambda: self._on_generate_complete())
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))
            self.root.after(0, lambda: self._on_generate_complete())
    
    def _update_visualizations(self) -> None:
        """Update visualization plots."""
        if self.generated_data is None:
            return
        
        try:
            data = self.generated_data[0] if isinstance(self.generated_data, list) else self.generated_data
            mixed = self.mixed_data[0] if isinstance(self.mixed_data, list) else self.mixed_data
            
            freq_cols = [col for col in data.columns if str(col).startswith("Ch")]
            
            if len(freq_cols) > 0:
                self._plot_time_domain(data, mixed, freq_cols)
                self._plot_frequency_domain(data, mixed, freq_cols)
                self._plot_spectrogram(data, mixed, freq_cols)
        except Exception as e:
            print(f"Visualization error: {e}")
    
    def _plot_time_domain(self, data, mixed, freq_cols) -> None:
        """Plot time domain signals."""
        if self.time_canvas:
            self.time_canvas.get_tk_widget().destroy()
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        col = freq_cols[len(freq_cols)//2]
        ax.plot(data[col], label="Clean", alpha=0.7)
        ax.plot(mixed[col], label="With RFI", alpha=0.7)
        ax.set_xlabel("Time Index")
        ax.set_ylabel("Brightness Temperature (K)")
        ax.set_title(f"Time Domain - {col}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.time_canvas = FigureCanvasTkAgg(fig, master=self.time_frame)
        self.time_canvas.draw()
        self.time_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _plot_frequency_domain(self, data, mixed, freq_cols) -> None:
        """Plot frequency domain signals."""
        if self.freq_canvas:
            self.freq_canvas.get_tk_widget().destroy()
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        frequencies = []
        values_clean = []
        values_mixed = []
        
        for col in freq_cols:
            try:
                freq = float(str(col).split()[-1])
                frequencies.append(freq)
                values_clean.append(data[col].mean())
                values_mixed.append(mixed[col].mean())
            except (ValueError, IndexError):
                pass
        
        if frequencies:
            ax.plot(frequencies, values_clean, marker='o', label="Clean", alpha=0.7)
            ax.plot(frequencies, values_mixed, marker='s', label="With RFI", alpha=0.7)
            ax.set_xlabel("Frequency (GHz)")
            ax.set_ylabel("Mean Brightness Temperature (K)")
            ax.set_title("Frequency Spectrum")
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        self.freq_canvas = FigureCanvasTkAgg(fig, master=self.freq_frame)
        self.freq_canvas.draw()
        self.freq_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _plot_spectrogram(self, data, mixed, freq_cols) -> None:
        """Plot RFI contamination map."""
        if self.spec_canvas:
            self.spec_canvas.get_tk_widget().destroy()
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        if len(freq_cols) > 1:
            matrix = np.array([mixed[col].values - data[col].values for col in freq_cols[:20]])
            im = ax.imshow(matrix, aspect='auto', cmap='RdBu_r', origin='lower')
            ax.set_xlabel("Time Index")
            ax.set_ylabel("Frequency Channel")
            ax.set_title("RFI Contamination Map")
            fig.colorbar(im, ax=ax, label="RFI Power (K)")
        
        self.spec_canvas = FigureCanvasTkAgg(fig, master=self.spec_frame)
        self.spec_canvas.draw()
        self.spec_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _on_generate_complete(self) -> None:
        """Handle generation completion."""
        self.progress.stop()
        self.generate_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Ready", foreground="green")
    
    def _on_export(self) -> None:
        """Export generated data."""
        if self.mixed_data is None:
            messagebox.showwarning("Warning", "No data to export.")
            return
        
        folder = filedialog.askdirectory(title="Select export folder")
        if folder:
            try:
                data_to_export = self.mixed_data if isinstance(self.mixed_data, list) else [self.mixed_data]
                for i, df in enumerate(data_to_export):
                    df.to_csv(f"{folder}/rfi_data_{i:03d}.csv", index=False)
                
                with open(f"{folder}/metadata.json", "w") as f:
                    json.dump(self.rfi_info, f, indent=2, default=str)
                
                messagebox.showinfo("Success", f"Exported to {folder}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = """RFI Generator v0.1.0

A synthetic RFI generator for K-band radiometric data.

Developed by: ECE Department
University of Puerto Rico - Mayagüez

Features:
- Interactive RFI generation
- Multiple source types
- Real-time visualization
- CSV export"""
        
        messagebox.showinfo("About RFI Generator", about_text)


def launch_gui() -> None:
    """Launch the GUI application."""
    root = tk.Tk()
    app = RFIGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
