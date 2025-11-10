# Import necessary libraries
import tkinter as tk                        # Library for creating graphical user interfaces (GUI)
from tkinter import ttk                     # Themed widgets extension for tkinter
import numpy as np                          # Library for numerical operations and arrays
import matplotlib.pyplot as plt              # Library for plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # Embeds matplotlib figures in Tkinter


# Main application class
class SignalApp:
    def __init__(self, root):
        self.root = root                                   # Main application window
        self.root.title("Synthetic RFI Generator")         # Window title

        # Create notebook tabs
        self.tab_control = ttk.Notebook(root)                                 # Tab control container
        self.tab1 = ttk.Frame(self.tab_control)                               # Tab 1 (Sinusoidal)
        self.tab2 = ttk.Frame(self.tab_control)                               # Tab 2 (Gaussian Noise)
        self.tab3 = ttk.Frame(self.tab_control)                               # Tab 3 (Combined)
        self.tab4 = ttk.Frame(self.tab_control)                               # NEW: Amplitude Table (freq on X, amplitude on Y)
        self.tab_control.add(self.tab1, text='Sinusoidal')                    # Add Sinusoidal tab
        self.tab_control.add(self.tab2, text='Gaussian Noise')                # Add Gaussian tab
        self.tab_control.add(self.tab3, text='Sinusoidal + Gaussian Noise')   # Add Combined tab
        self.tab_control.add(self.tab4, text='Amplitude Table')               # new:
        self.tab_control.pack(expand=1, fill="both")                          # Display notebook on window

        # Default parameters
        self.n = tk.IntVar(value=100)                          # Number of samples
        self.amplitude = tk.DoubleVar(value=1.0)               # Amplitude of the sinusoidal signal
        self.frequency = tk.DoubleVar(value=1.0)               # Frequency in Hz
        self.phase = tk.DoubleVar(value=0.0)                   # Phase in radians
        self.a = tk.IntVar(value=0)                            # (Unused variable, can be extended)
        self.mu = tk.DoubleVar(value=0.0)                      # Mean value of Gaussian noise
        self.sigma = tk.DoubleVar(value=0.1)                   # Standard deviation of Gaussian noise
        self.duration = 1.0                                    # Signal duration (seconds)
        self.t = np.linspace(0, self.duration, self.n.get())   # Time vector
        self.sinusoidal = np.zeros(self.n.get())               # Placeholder for sinusoidal signal
        self.gaussiannoise = np.zeros(self.n.get())            # Placeholder for Gaussian noise
        self.seed = tk.IntVar(value=0)                         # Random seed (0 means auto-generate)

         # ----- NEW: frequency points for the table tab -----
        self.freq_points = [
            22, 22.234, 22.5, 23, 23.034, 23.5, 23.834, 24, 24.5, 25,
            25.5, 26, 26.234, 26.5, 27, 27.5, 28, 28.5, 29, 29.5, 30
        ]
        # Global amplitude that will be applied to ALL frequencies
        self.global_amp = tk.DoubleVar(value=1.0)
        # One DoubleVar per frequency to display/edit the amplitude “row” (locked to global via button)
        self.amp_vars = [tk.DoubleVar(value=self.global_amp.get()) for _ in self.freq_points]
        self.sel_vars = [tk.BooleanVar(value=False) for _ in self.freq_points]  # NEW: checkboxes to select freqs for noise


        # Build all three tabs
        self.build_sine_tab()          # Create Sinusoidal tab
        self.build_gaussian_tab()      # Create Gaussian Noise tab
        self.build_combined_tab()      # Create Combined tab
        self.build_table_tab()         # Create Frecuancy tab

    # --- Tab 1: Sinusoidal Signal ---
    def build_sine_tab(self):
        frame_controls = ttk.LabelFrame(self.tab1, text="⚙️Parameters")   # Control panel frame
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")      # Left-side placement

        # Number of samples
        ttk.Label(frame_controls, text="Number of samples:").pack(pady=5)
        tk.Spinbox(frame_controls, from_=10, to=10000, textvariable=self.n, width=10).pack()

        # Amplitude input
        ttk.Label(frame_controls, text="Amplitude:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.amplitude, width=10).pack()

        # Frequency input
        ttk.Label(frame_controls, text="Frequency (Hz):").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.frequency, width=10).pack()

        # Phase input
        ttk.Label(frame_controls, text="Phase:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.phase, width=10).pack()

        # Plot button
        ttk.Button(frame_controls, text="Plot", command=self.plot_sine).pack(pady=10)

        # Matplotlib figure embedded in Tkinter
        self.sine_fig, self.sine_ax = plt.subplots(figsize=(5, 4))                # Create figure and axes
        self.sine_canvas = FigureCanvasTkAgg(self.sine_fig, master=self.tab1)     # Embed figure in tab
        self.sine_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)  # Show plot

    def plot_sine(self):
        # Get the number of samples and update the time vector
        n = self.n.get()
        self.t = np.linspace(0, self.duration, n)

        # Get parameters from GUI inputs
        amplitude = self.amplitude.get()
        frequency = self.frequency.get()
        phase = self.phase.get()

        # Generate the sinusoidal wave: y = A * sin(2πft + φ)
        y = amplitude * np.sin(2 * np.pi * frequency * self.t + phase)
        self.sinusoidal = y   # Store it for later use (combined plot)

        # Plot the waveform
        self.sine_ax.clear()                            # Clear old plot
        self.sine_ax.plot(self.t, y, color='blue')      # Plot blue line
        self.sine_ax.set_title(f'Sinusoidal ({n} samples)')  # Set title
        self.sine_ax.set_xlabel('Time (s)')             # Label X-axis
        self.sine_ax.set_ylabel('Amplitude')            # Label Y-axis
        self.sine_ax.grid(True)                         # Enable grid
        self.sine_canvas.draw()                         # Redraw canvas

    # --- Tab 2: Gaussian Noise ---
    def build_gaussian_tab(self):
        frame_controls = ttk.LabelFrame(self.tab2, text="⚙️Parameters")          # Control panel frame
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")

        # Number of samples
        ttk.Label(frame_controls, text="Number of samples:").pack(pady=5)
        tk.Spinbox(frame_controls, from_=10, to=10000, textvariable=self.n, width=10).pack()

        # Random seed input
        ttk.Label(frame_controls, text="Seed:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.seed, width=10).pack()

        # Mean (μ)
        ttk.Label(frame_controls, text="Mean (μ):").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.mu, width=10).pack()

        # Standard deviation (σ)
        ttk.Label(frame_controls, text="Standard deviation (σ):").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.sigma, width=10).pack()

        # Plot button
        ttk.Button(frame_controls, text="Plot", command=self.plot_gaussian).pack(pady=10)

        # Matplotlib figure for Gaussian noise
        self.gauss_fig, self.gauss_ax = plt.subplots(figsize=(5, 4))              # Create figure
        self.gauss_canvas = FigureCanvasTkAgg(self.gauss_fig, master=self.tab2)   # Embed figure
        self.gauss_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def plot_gaussian(self):
        n = self.n.get()                     # Number of samples

        # Retrieve or generate seed
        seed = int(self.seed.get())
        if seed == 0:                        # If seed is 0, create a random one
            seed = int(np.random.randint(0, np.iinfo(np.int32).max))
            self.seed.set(seed)              # Display generated seed in entry box
        np.random.seed(seed)                 # Set the random seed

        # Get mean and std. deviation values
        mu = self.mu.get()
        sigma = self.sigma.get()

        # Generate Gaussian noise
        noise = np.random.normal(mu, sigma, n)
        self.gaussiannoise = noise           # Store noise array for later use

        # Plot noise
        self.gauss_ax.clear()
        self.gauss_ax.plot(self.t, noise, color='gray')        # Gray noise line
        self.gauss_ax.set_title("Gaussian Noise")              # Title
        self.gauss_ax.set_xlabel("Time (s)")                   # X label
        self.gauss_ax.set_ylabel("Amplitude")                  # Y label
        self.gauss_ax.grid(True)
        self.gauss_canvas.draw()                               # Update figure on GUI

    # --- Tab 3: Combined Signal (Sine + Noise) ---
    def build_combined_tab(self):
        frame_controls = ttk.LabelFrame(self.tab3, text="⚙️Parameters")          # Control panel
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")

        # Plot button for combined signal
        ttk.Button(frame_controls, text="Plot", command=self.plot_combined).pack(pady=10)

        # Matplotlib figure for combined plot
        self.combo_fig, self.combo_ax = plt.subplots(figsize=(5, 4))
        self.combo_canvas = FigureCanvasTkAgg(self.combo_fig, master=self.tab3)
        self.combo_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def plot_combined(self):
        n = self.n.get()                         # Number of samples
        y = self.sinusoidal                      # Retrieve last generated sinusoidal signal
        noise = self.gaussiannoise               # Retrieve last generated Gaussian noise
        y_total = y + noise                      # Combine both signals (add them)

        # Plot all three components
        self.combo_ax.clear()
        self.combo_ax.plot(self.t, y, 'b--', label='Sinusoidal')                  # Blue dashed line
        self.combo_ax.plot(self.t, noise, color='gray', alpha=0.5, label='Gaussian noise')  # Gray noise
        self.combo_ax.plot(self.t, y_total, 'r-', linewidth=2, label='Signal + Noise')      # Red combined line
        self.combo_ax.set_title(f'Signal with Gaussian Noise ({n} samples)')      # Title
        self.combo_ax.set_xlabel('Time (s)')                                      # X-axis
        self.combo_ax.set_ylabel('Amplitude')                                     # Y-axis
        self.combo_ax.legend()                                                    # Add legend
        self.combo_ax.grid(True)                                                  # Enable grid
        self.combo_canvas.draw()                                                  # Refresh canvas

    # === TAB 4: Amplitude Table (Freq on X, Amplitude on Y) =====

    def build_table_tab(self):  # NEW
        """Builds the new tab: amplitude vs frequency and noisy spectrum."""  # NEW
        controls = ttk.LabelFrame(self.tab4, text="⚙️Controls")  # NEW
        controls.pack(side="left", padx=10, pady=10, fill="y")  # NEW

        # ---- Controls for global amplitude ----
        ttk.Label(controls, text="Global amplitude:").pack(pady=(8, 2))  # NEW
        tk.Spinbox(  # NEW
            controls, from_=-1e6, to=1e6, increment=0.1,
            textvariable=self.global_amp, width=10
        ).pack()  # NEW

        ttk.Button(controls, text="Apply to all", command=self.apply_global_amplitude).pack(pady=8)  # NEW

        ttk.Separator(controls, orient="horizontal").pack(fill="x", pady=6)  # NEW

        # ---- Gaussian noise parameters ----
        ttk.Label(controls, text="Noise parameters (for selected freqs):").pack(pady=(6, 2))  # NEW
        row_noise = ttk.Frame(controls)  # NEW
        row_noise.pack(pady=2)  # NEW
        ttk.Label(row_noise, text="Seed: ").grid(row=0, column=0, sticky="e")  # NEW
        tk.Entry(row_noise, textvariable=self.seed, width=10).grid(row=0, column=1, padx=4)  # NEW

        row_noise2 = ttk.Frame(controls)  # NEW
        row_noise2.pack(pady=2)  # NEW
        ttk.Label(row_noise2, text="μ: ").grid(row=0, column=0, sticky="e")  # NEW
        tk.Entry(row_noise2, textvariable=self.mu, width=10).grid(row=0, column=1, padx=4)  # NEW

        row_noise3 = ttk.Frame(controls)  # NEW
        row_noise3.pack(pady=2)  # NEW
        ttk.Label(row_noise3, text="σ: ").grid(row=0, column=0, sticky="e")  # NEW
        tk.Entry(row_noise3, textvariable=self.sigma, width=10).grid(row=0, column=1, padx=4)  # NEW

        ttk.Button(controls, text="Plot spectra", command=self.plot_spectra).pack(pady=10)  # NEW

        hint = ttk.Label(  # NEW
            controls,
            text="Select freqs (checkboxes) to receive\nGaussian noise. Then click Plot spectra.",
            justify="left"
        )  # NEW
        hint.pack(pady=6)  # NEW

        # ---- Table area with frequencies and amplitudes ----
        table_frame = ttk.Frame(self.tab4)  # NEW
        table_frame.pack(side="top", fill="x", expand=False, padx=10, pady=10)  # NEW

        ttk.Label(table_frame, text="Frequency (GHz) →", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w", padx=4, pady=4)  # NEW
        for j, f in enumerate(self.freq_points, start=1):  # NEW
            ttk.Label(table_frame, text=str(f)).grid(row=0, column=j, padx=2, pady=4)  # NEW

        ttk.Label(table_frame, text="Add noise?").grid(row=1, column=0, sticky="w", padx=4, pady=2)  # NEW
        for j, var in enumerate(self.sel_vars, start=1):  # NEW
            tk.Checkbutton(table_frame, variable=var).grid(row=1, column=j, padx=2, pady=2)  # NEW

        ttk.Label(table_frame, text="Amplitude ↓", font=('Segoe UI', 9, 'bold')).grid(row=2, column=0, sticky="w", padx=4, pady=4)  # NEW
        for j, var in enumerate(self.amp_vars, start=1):  # NEW
            tk.Spinbox(  # NEW
                table_frame, from_=-1e6, to=1e6, increment=0.1,
                textvariable=var, width=7
            ).grid(row=2, column=j, padx=2, pady=2)  # NEW

        # ---- Figures for clean and noisy spectra ----
        figs_frame = ttk.Frame(self.tab4)  # NEW
        figs_frame.pack(side="bottom", fill="both", expand=True, padx=10, pady=4)  # NEW

        self.spec_fig, self.spec_ax = plt.subplots(figsize=(6, 3))  # NEW
        self.spec_canvas = FigureCanvasTkAgg(self.spec_fig, master=figs_frame)  # NEW
        self.spec_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)  # NEW

        self.noisy_fig, self.noisy_ax = plt.subplots(figsize=(6, 3))  # NEW
        self.noisy_canvas = FigureCanvasTkAgg(self.noisy_fig, master=figs_frame)  # NEW
        self.noisy_canvas.get_tk_widget().pack(side="bottom", fill="both", expand=True)  # NEW

    def apply_global_amplitude(self):  # NEW
        """Set all amplitude cells to the same value (global_amp)."""  # NEW
        value = self.global_amp.get()  # NEW
        for var in self.amp_vars:  # NEW
            var.set(value)  # NEW

    def plot_spectra(self):  # NEW
        """Plot (1) the clean spectrum and (2) the spectrum with Gaussian noise on selected freqs."""  # NEW
        freqs = np.array(self.freq_points, dtype=float)  # NEW
        amps = np.array([v.get() for v in self.amp_vars], dtype=float)  # NEW

        # --- Clean spectrum ---
        self.spec_ax.clear()  # NEW
        self.spec_ax.plot(freqs, amps, marker='o')  # NEW
        self.spec_ax.set_title("Spectrum: Amplitude vs Frequency (clean)")  # NEW
        self.spec_ax.set_xlabel("Frequency (GHz)")  # NEW
        self.spec_ax.set_ylabel("Amplitude")  # NEW
        self.spec_ax.grid(True)  # NEW
        self.spec_canvas.draw()  # NEW

        # --- Noisy spectrum ---
        seed = int(self.seed.get())  # NEW
        if seed == 0:  # NEW
            seed = int(np.random.randint(0, np.iinfo(np.int32).max))  # NEW
            self.seed.set(seed)  # NEW
        np.random.seed(seed)  # NEW

        mu = float(self.mu.get())  # NEW
        sigma = float(self.sigma.get())  # NEW

        selections = np.array([sv.get() for sv in self.sel_vars], dtype=bool)  # NEW
        noise = np.zeros_like(amps, dtype=float)  # NEW
        if np.any(selections):  # NEW
            noise[selections] = np.random.normal(mu, sigma, size=selections.sum())  # NEW

        amps_noisy = amps + noise  # NEW

        self.noisy_ax.clear()  # NEW
        self.noisy_ax.plot(freqs, amps_noisy, marker='o')  # NEW
        self.noisy_ax.set_title("Spectrum with Gaussian Noise (selected freqs)")  # NEW
        self.noisy_ax.set_xlabel("Frequency (GHz)")  # NEW
        self.noisy_ax.set_ylabel("Amplitude")  # NEW
        self.noisy_ax.grid(True)  # NEW
        self.noisy_canvas.draw()  # NEW



# --- Main program ---
if __name__ == "__main__":
    root = tk.Tk()               # Create main Tkinter window
    app = SignalApp(root)        # Create instance of the app
    root.mainloop()              # Start Tkinter event loop
