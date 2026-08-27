"""Tkinter GUI for interactive RFI generation."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from rfigen.config import ExperimentConfig, RFIConfig
from rfigen.dataset import build_dataset
from rfigen.export_data import export_dataset
from rfigen.visualization import (
    plot_direction_profiles,
    plot_direction_spectrogram,
    plot_frequency,
    plot_profile_for_direction,
    plot_spectrogram,
    plot_time_series,
)


class RFIGenApp(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.dataset = None
        self.canvas = None
        self.toolbar = None
        self.direction_labels: list[str] = []
        self.direction_values: list[tuple[float, float]] = []
        self.pack(fill=tk.BOTH, expand=True)
        self._build_controls()
        self._build_plot_area()
        self.generate()

    def _build_controls(self) -> None:
        panel = ttk.Frame(self)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.rfi_type = tk.StringVar(value="narrowband")
        self.enable_rfi = tk.BooleanVar(value=False)
        self.center = tk.DoubleVar(value=22.235)
        self.bandwidth = tk.DoubleVar(value=80.0)
        self.power = tk.DoubleVar(value=25.0)
        self.duration = tk.DoubleVar(value=60.0)
        self.sample_rate = tk.DoubleVar(value=1.0)
        self.plot_kind = tk.StringVar(value="profiles")
        self.direction = tk.StringVar(value="")

        row = 0
        ttk.Checkbutton(panel, text="Add RFI", variable=self.enable_rfi).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1
        ttk.Label(panel, text="RFI Type").grid(row=row, column=0, sticky="w")
        ttk.OptionMenu(panel, self.rfi_type, self.rfi_type.get(), "narrowband", "broadband", "pulsed", "bursty", "chirp", "am").grid(row=row, column=1, sticky="ew")
        row += 1
        for label, variable in (
            ("Center GHz", self.center),
            ("Bandwidth MHz", self.bandwidth),
            ("Power K", self.power),
            ("Duration s", self.duration),
            ("Sample Hz", self.sample_rate),
        ):
            ttk.Label(panel, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Entry(panel, textvariable=variable, width=12).grid(row=row, column=1, sticky="ew", pady=3)
            row += 1

        ttk.Label(panel, text="View").grid(row=row, column=0, sticky="w")
        ttk.OptionMenu(panel, self.plot_kind, self.plot_kind.get(), "profiles", "direction profile", "direction spectrogram", "spectrogram", "time", "frequency").grid(row=row, column=1, sticky="ew")
        row += 1
        ttk.Label(panel, text="Direction").grid(row=row, column=0, sticky="w")
        self.direction_menu = ttk.OptionMenu(panel, self.direction, "")
        self.direction_menu.grid(row=row, column=1, sticky="ew")
        row += 1

        ttk.Button(panel, text="Generate", command=self.generate).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12, 3))
        row += 1
        ttk.Button(panel, text="Export Dataset", command=self.export).grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)
        panel.columnconfigure(1, weight=1)

    def _build_plot_area(self) -> None:
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def generate(self) -> None:
        try:
            rfi_entries = []
            if self.enable_rfi.get():
                rfi_entries.append(
                    RFIConfig(
                        type=self.rfi_type.get(),
                        center_frequency_ghz=self.center.get(),
                        bandwidth_mhz=self.bandwidth.get(),
                        power_k=self.power.get(),
                        duty_cycle=0.2,
                        pulse_period_s=4.0,
                        persistence=1.0,
                    )
                )
            config = ExperimentConfig(
                duration_s=self.duration.get(),
                sample_rate_hz=self.sample_rate.get(),
                frequency_bins=21,
                rfi=rfi_entries,
            )
            self.dataset = build_dataset(config)
            self._refresh_directions()
            self._draw_plot()
        except Exception as exc:
            messagebox.showerror("RFIGen", str(exc))

    def export(self) -> None:
        if self.dataset is None:
            messagebox.showwarning("RFIGen", "Generate a dataset first.")
            return
        target = filedialog.askdirectory(title="Choose export directory")
        if not target:
            return
        output = export_dataset(self.dataset, Path(target))
        messagebox.showinfo("RFIGen", f"Dataset exported to {output}")

    def _draw_plot(self) -> None:
        if self.dataset is None:
            return
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar is not None:
            self.toolbar.destroy()

        view = self.plot_kind.get()
        if view == "time":
            fig = plot_time_series(self.dataset, self.center.get())
        elif view == "frequency":
            fig = plot_frequency(self.dataset)
        elif view == "profiles":
            fig = plot_direction_profiles(self.dataset)
        elif view == "direction profile":
            azimuth, elevation = self._selected_direction()
            fig = plot_profile_for_direction(self.dataset, azimuth, elevation)
        elif view == "direction spectrogram":
            azimuth, elevation = self._selected_direction()
            fig = plot_direction_spectrogram(self.dataset, azimuth, elevation)
        else:
            fig = plot_spectrogram(self.dataset)

        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _refresh_directions(self) -> None:
        if self.dataset is None or self.dataset.azimuth_deg is None or self.dataset.elevation_deg is None:
            self.direction_values = [(0.0, 0.0)]
        else:
            self.direction_values = sorted(
                {
                    (float(azimuth), float(elevation))
                    for azimuth, elevation in zip(self.dataset.azimuth_deg, self.dataset.elevation_deg, strict=True)
                }
            )
        self.direction_labels = [f"az={azimuth:g}, el={elevation:g}" for azimuth, elevation in self.direction_values]
        if not self.direction.get() or self.direction.get() not in self.direction_labels:
            self.direction.set(self.direction_labels[0])
        menu = self.direction_menu["menu"]
        menu.delete(0, "end")
        for label in self.direction_labels:
            menu.add_command(label=label, command=lambda value=label: self.direction.set(value))

    def _selected_direction(self) -> tuple[float, float]:
        if not self.direction_values:
            return 0.0, 0.0
        try:
            index = self.direction_labels.index(self.direction.get())
        except ValueError:
            index = 0
        return self.direction_values[index]


def run_gui() -> None:
    root = tk.Tk()
    root.title("RFIGen - Synthetic K-Band RFI Generator")
    root.geometry("1100x720")
    RFIGenApp(root)
    root.mainloop()
