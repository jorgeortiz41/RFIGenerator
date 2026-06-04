# gui_app.py
# ============================================================
# RFIGen Graphical User Interface
# ------------------------------------------------------------
# GUI connected to the modular RFIGen pipeline:
#
# Config → Dataset Builder → Signal Mixer → Export → Visualization
# ============================================================

from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# ------------------------------------------------------------
# Make sure project root is available for imports
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config.config_loader import load_config
from src.config.config_parser import ConfigValidationError, parse_and_validate_config
from src.data.dataset_builder import build_dataset
from src.visualization.plots import generate_visualization_products


class RFIGenApp:
    """
    Main GUI application for RFIGen.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RFIGen — Synthetic RFI Generator")
        self.root.geometry("900x650")

        # GUI variables
        self.config_path = tk.StringVar(value="src/config/examples/base_config.yaml")
        self.records = tk.StringVar(value="3")
        self.output_prefix = tk.StringVar(value="gui_test")
        self.enable_export = tk.BooleanVar(value=True)
        self.enable_plots = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Build the GUI layout.
        """

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="RFIGen — Synthetic RFI Generator",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w", pady=(0, 12))

        # ----------------------------------------------------
        # Config section
        # ----------------------------------------------------
        config_frame = ttk.LabelFrame(main, text="Configuration File", padding=10)
        config_frame.pack(fill="x", pady=6)

        row = ttk.Frame(config_frame)
        row.pack(fill="x")

        ttk.Entry(row, textvariable=self.config_path).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8),
        )

        ttk.Button(row, text="Browse", command=self.browse_config).pack(side="right")

        # ----------------------------------------------------
        # Run settings
        # ----------------------------------------------------
        settings_frame = ttk.LabelFrame(main, text="Run Settings", padding=10)
        settings_frame.pack(fill="x", pady=6)

        row1 = ttk.Frame(settings_frame)
        row1.pack(fill="x", pady=4)

        ttk.Label(row1, text="Records override:").pack(side="left")
        ttk.Entry(row1, textvariable=self.records, width=12).pack(side="left", padx=8)

        ttk.Label(row1, text="Output prefix:").pack(side="left", padx=(20, 0))
        ttk.Entry(row1, textvariable=self.output_prefix, width=20).pack(side="left", padx=8)

        row2 = ttk.Frame(settings_frame)
        row2.pack(fill="x", pady=4)

        ttk.Checkbutton(
            row2,
            text="Export CSV / NPY / Metadata",
            variable=self.enable_export,
        ).pack(side="left", padx=(0, 20))

        ttk.Checkbutton(
            row2,
            text="Generate visualization figures",
            variable=self.enable_plots,
        ).pack(side="left")

        # ----------------------------------------------------
        # Action buttons
        # ----------------------------------------------------
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=10)

        self.run_button = ttk.Button(
            button_frame,
            text="Run RFIGen Pipeline",
            command=self.run_pipeline_threaded,
        )
        self.run_button.pack(side="left")

        ttk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log,
        ).pack(side="left", padx=8)

        ttk.Button(
            button_frame,
            text="Open Outputs Folder",
            command=self.open_outputs_folder,
        ).pack(side="left", padx=8)

        # ----------------------------------------------------
        # Log output
        # ----------------------------------------------------
        log_frame = ttk.LabelFrame(main, text="Log", padding=8)
        log_frame.pack(fill="both", expand=True, pady=6)

        self.log_text = tk.Text(log_frame, wrap="word", height=22)
        self.log_text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")

        self.log_text.configure(yscrollcommand=scroll.set)

        self.log("Ready.")
        self.log("Select a config file and click 'Run RFIGen Pipeline'.")

    def browse_config(self) -> None:
        """
        Select YAML or JSON config file.
        """

        path = filedialog.askopenfilename(
            title="Select RFIGen Config File",
            filetypes=[
                ("Config files", "*.yaml *.yml *.json"),
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.config_path.set(path)

    def log(self, message: str) -> None:
        """
        Add text to the GUI log.
        """

        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_log(self) -> None:
        """
        Clear log window.
        """

        self.log_text.delete("1.0", "end")

    def open_outputs_folder(self) -> None:
        """
        Open outputs folder in Windows Explorer.
        """

        outputs = PROJECT_ROOT / "outputs"
        outputs.mkdir(exist_ok=True)

        try:
            import os
            os.startfile(outputs)
        except Exception as exc:
            messagebox.showerror("Open Folder Error", str(exc))

    def run_pipeline_threaded(self) -> None:
        """
        Run the pipeline in a background thread so the GUI does not freeze.
        """

        thread = threading.Thread(target=self.run_pipeline, daemon=True)
        thread.start()

    def run_pipeline(self) -> None:
        """
        Run the full RFIGen pipeline from the GUI.
        """

        self.run_button.configure(state="disabled")

        try:
            self.log("")
            self.log("============================================")
            self.log("Running RFIGen Pipeline")
            self.log("============================================")

            config_path = Path(self.config_path.get()).expanduser()

            self.log(f"Config file: {config_path}")

            raw_config = load_config(config_path)
            config = parse_and_validate_config(raw_config)

            self.log("Config loaded successfully.")
            self.log(f"Project: {config['project']['name']}")
            self.log(f"Profile: {config['project']['profile']}")
            self.log(
                f"Frequency band: "
                f"{config['frequency']['band']['min_ghz']}–"
                f"{config['frequency']['band']['max_ghz']} GHz"
            )
            self.log(f"Center frequency: {config['frequency']['center_ghz']} GHz")
            self.log(f"Configured RFI sources: {len(config.get('rfi_sources', []))}")

            records_text = self.records.get().strip()
            records_override = int(records_text) if records_text else None

            output_prefix = self.output_prefix.get().strip()
            if not output_prefix:
                output_prefix = str(config["run"]["output_prefix"])

            self.log("")
            self.log("Generating dataset...")

            dataset_result, exported_files = build_dataset(
                config=config,
                records_override=records_override,
                output_prefix=output_prefix,
                export=self.enable_export.get(),
            )

            self.log("Dataset generated successfully.")
            self.log(f"Clean dataset shape: {dataset_result.clean_df.shape}")
            self.log(f"Contaminated dataset shape: {dataset_result.contaminated_df.shape}")
            self.log(f"RFI matrix shape: {dataset_result.rfi_matrix.shape}")
            self.log(f"Channels: {dataset_result.channel_cols}")

            if exported_files:
                self.log("")
                self.log("Exported files:")
                for name, path in exported_files.items():
                    self.log(f"  {name}: {path}")
            else:
                self.log("")
                self.log("No dataset files exported.")

            figure_files = {}

            if self.enable_plots.get():
                self.log("")
                self.log("Generating visualization figures...")

                figure_files = generate_visualization_products(
                    mixer_result=dataset_result,
                    config=config,
                    output_prefix=output_prefix,
                )

            if figure_files:
                self.log("")
                self.log("Figure files:")
                for name, path in figure_files.items():
                    self.log(f"  {name}: {path}")
            else:
                self.log("")
                self.log("No figures generated.")

            self.log("")
            self.log("Done.")

        except ConfigValidationError as exc:
            self.log("")
            self.log("Config validation failed:")
            self.log(str(exc))
            messagebox.showerror("Config Validation Error", str(exc))

        except Exception as exc:
            self.log("")
            self.log("Pipeline failed:")
            self.log(str(exc))
            messagebox.showerror("Pipeline Error", str(exc))

        finally:
            self.run_button.configure(state="normal")


def main() -> None:
    root = tk.Tk()
    app = RFIGenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()