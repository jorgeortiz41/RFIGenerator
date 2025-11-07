import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SignalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Synthetic RFI Generator")

        # Create tabs
        self.tab_control = ttk.Notebook(root)
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab3 = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab1, text='Sinusoidal')
        self.tab_control.add(self.tab2, text='Gaussian Noise')
        self.tab_control.add(self.tab3, text='Sinusoidal + Gaussian Noise')
        self.tab_control.pack(expand=1, fill="both")

        # Default parameters
        self.n = tk.IntVar(value=100)
        self.amplitude = tk.DoubleVar(value=1.0)
        self.frequency = tk.DoubleVar(value=1.0)
        self.phase = tk.DoubleVar(value=0.0)
        self.a = tk.IntVar(value=0)
        self.mu = tk.DoubleVar(value=0.0)
        self.sigma = tk.DoubleVar(value=0.1)
        self.duration = 1.0  # seconds
        self.t = np.linspace(0, self.duration, self.n.get())
        self.sinusoidal = np.zeros(self.n.get())
        self.gaussiannoise = np.zeros(self.n.get())# 1 second
        self.seed = tk.IntVar(value=0)

        # --- Tab 1: Senoidal ---
        self.build_sine_tab()

        # --- Tab 2: Gaussiano ---
        self.build_gaussian_tab()

        # --- Tab 3: Combinada ---
        self.build_combined_tab()

    def build_sine_tab(self):
        frame_controls = ttk.LabelFrame(self.tab1, text="⚙️Parameters")
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")

        ttk.Label(frame_controls, text="Number of samples:").pack(pady=5)
        tk.Spinbox(frame_controls, from_=10, to=10000, textvariable=self.n, width=10).pack()

        ttk.Label(frame_controls, text="Amplitude:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.amplitude, width=10).pack()

        ttk.Label(frame_controls, text="Frequency:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.frequency, width=10).pack()

        ttk.Label(frame_controls, text="Phase:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.phase, width=10).pack()

        ttk.Button(frame_controls, text="Plot", command=self.plot_sine).pack(pady=10)

        self.sine_fig, self.sine_ax = plt.subplots(figsize=(5, 4))
        self.sine_canvas = FigureCanvasTkAgg(self.sine_fig, master=self.tab1)
        self.sine_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def plot_sine(self):
        n = self.n.get()
        self.t = np.linspace(0, self.duration, n)  # update time vector

        amplitude = self.amplitude.get()
        frequency = self.frequency.get()
        phase = self.phase.get()

        y = amplitude * np.sin(2 * np.pi * frequency * self.t + phase)
        self.sinusoidal = y

        self.sine_ax.clear()
        self.sine_ax.plot(self.t, y, color='blue')
        self.sine_ax.set_title(f'Senoidal ({n} puntos)')
        self.sine_ax.set_xlabel('Tiempo (s)')
        self.sine_ax.set_ylabel('Amplitud')
        self.sine_ax.grid(True)
        self.sine_canvas.draw()

    def build_gaussian_tab(self):
        frame_controls = ttk.LabelFrame(self.tab2, text="⚙️Parameters")
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")

        ttk.Label(frame_controls, text="Number of samples:").pack(pady=5)
        tk.Spinbox(frame_controls, from_=10, to=10000, textvariable=self.n, width=10).pack()

        ttk.Label(frame_controls, text="Seed:").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.seed, width=10).pack()

        ttk.Label(frame_controls, text="Mean (μ):").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.mu, width=10).pack()

        ttk.Label(frame_controls, text="Standard deviation (σ):").pack(pady=5)
        tk.Entry(frame_controls, textvariable=self.sigma, width=10).pack()

        ttk.Button(frame_controls, text="Plot", command=self.plot_gaussian).pack(pady=10)

        self.gauss_fig, self.gauss_ax = plt.subplots(figsize=(5, 4))
        self.gauss_canvas = FigureCanvasTkAgg(self.gauss_fig, master=self.tab2)
        self.gauss_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def plot_gaussian(self):
        n = self.n.get()
        seed = np.random.randint(2**32 - 1)
        self.seed.set(seed)
        self.t = np.linspace(0, self.duration, n)  # same time vector

        mu = self.mu.get()
        sigma = self.sigma.get()
        np.random.default_rng(seed)

        noise = np.random.normal(mu, sigma, n)
        self.gaussiannoise = noise

        self.gauss_ax.clear()
        self.gauss_ax.plot(self.t, noise, color='gray')
        self.gauss_ax.set_title("Ruido Gaussiano")
        self.gauss_ax.set_xlabel("Tiempo (s)")
        self.gauss_ax.set_ylabel("Amplitud")
        self.gauss_ax.grid(True)
        self.gauss_canvas.draw()

    def build_combined_tab(self):
        frame_controls = ttk.LabelFrame(self.tab3, text="⚙️Parameters")
        frame_controls.pack(side="left", padx=10, pady=10, fill="y")

        ttk.Button(frame_controls, text="Plot", command=self.plot_combined).pack(pady=10)

        self.combo_fig, self.combo_ax = plt.subplots(figsize=(5, 4))
        self.combo_canvas = FigureCanvasTkAgg(self.combo_fig, master=self.tab3)
        self.combo_canvas.get_tk_widget().pack(side="right", fill="both", expand=True)

    def plot_combined(self):
        n = self.n.get()
        y = self.sinusoidal
        noise = self.gaussiannoise
        y_total = y + noise

        self.combo_ax.clear()
        self.combo_ax.plot(self.t, y, 'b--', label='Seno puro')
        self.combo_ax.plot(self.t, noise, color='gray', alpha=0.5, label='Ruido gaussiano')
        self.combo_ax.plot(self.t, y_total, 'r-', linewidth=2, label='Seno + Ruido')
        self.combo_ax.set_title(f'Seno con Ruido Gaussiano ({n} puntos)')
        self.combo_ax.set_xlabel('Tiempo (s)')
        self.combo_ax.set_ylabel('Amplitud')
        self.combo_ax.legend()
        self.combo_ax.grid(True)
        self.combo_canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = SignalApp(root)
    root.mainloop()
