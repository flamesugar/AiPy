# file: gui/plot_manager.py

import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import os
import matplotlib
matplotlib.use('TkAgg')

class PlotManager:
    """A class to manage all Matplotlib plotting activities, including interactive legends."""
    
    # Class-level font parameters
    FONT_PARAMS = {
        'title': {'size': 14, 'weight': 'bold'},
        'label': {'size': 12},
        'tick': {'size': 10},
        'legend': {'size': 10}
    }
    
    def __init__(self, parent):
        """Initialize the plot manager."""
        self.parent = parent
        self.fig = plt.figure(figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        
        # Create subplots with reduced spacing
        self.fig.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.2)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212, sharex=self.ax1)
        
        # Configure subplots
        self.configure_subplots()
        
        # Add load data buttons
        self.add_load_buttons()
        
        # Initialize data storage
        self.primary_data = None
        self.secondary_data = None
        
        # Initialize detection markers
        self.peak_markers = {'primary': [], 'secondary': []}
        self.valley_markers = {'primary': [], 'secondary': []}
        
        # Connect legend click events
        self.connect_legend_events()

        # 初始化颜色映射
        self.colors = {
            'primary': {'dff': 'tab:blue', 'raw': 'tab:orange', 'isos': 'tab:green', 'fit': 'tab:purple', 'ttl1': 'tab:gray', 'ttl2': 'tab:cyan'},
            'secondary': {'dff': 'tab:red', 'raw': 'tab:brown', 'isos': 'tab:olive', 'fit': 'tab:pink', 'ttl1': 'tab:gray', 'ttl2': 'tab:cyan'}
        }
        # 初始化曲线和注释存储
        self.lines = {}
        self.annotations = {'peaks': [], 'valleys': [], 'artifacts': []}
        
        # Initialize normalization parameters
        self.norm_ranges = {}
        self.max_scale = 20.0  # Default scale

    def add_load_buttons(self):
        """Add load data buttons to the plot."""
        # Create button frame
        self.button_frame = tk.Frame(self.parent)
        self.button_frame.pack(side='top', fill='x', padx=5, pady=2)
        
        # Add load buttons
        if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'open_file'):
            self.load_primary_btn = tk.Button(
                self.button_frame, 
                text="Load Primary Data",
                command=lambda: self.parent.master.open_file(is_secondary=False)
            )
            self.load_primary_btn.pack(side='left', padx=5)
            
            self.load_secondary_btn = tk.Button(
                self.button_frame,
                text="Load Secondary Data",
                command=lambda: self.parent.master.open_file(is_secondary=True)
            )
            self.load_secondary_btn.pack(side='left', padx=5)
        else:
            self.load_primary_btn = tk.Button(
                self.button_frame, 
                text="Load Primary Data (disabled)",
                state='disabled'
            )
            self.load_primary_btn.pack(side='left', padx=5)
            self.load_secondary_btn = tk.Button(
                self.button_frame,
                text="Load Secondary Data (disabled)",
                state='disabled'
            )
            self.load_secondary_btn.pack(side='left', padx=5)

    def configure_subplots(self):
        """Configure the subplots with proper styling."""
        # Configure primary plot (File 1)
        self.ax1.set_title('Primary File Signals', fontdict=self.FONT_PARAMS['title'])
        self.ax1.set_ylabel('ΔF/F (%) / Normalized Signal', fontdict=self.FONT_PARAMS['label'])
        self.ax1.tick_params(axis='both', which='major', labelsize=self.FONT_PARAMS['tick']['size'])
        self.ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Configure secondary plot (File 2)
        self.ax2.set_title('Secondary File Signals', fontdict=self.FONT_PARAMS['title'])
        self.ax2.set_xlabel('Time (s)', fontdict=self.FONT_PARAMS['label'])
        self.ax2.set_ylabel('ΔF/F (%) / Normalized Signal', fontdict=self.FONT_PARAMS['label'])
        self.ax2.tick_params(axis='both', which='major', labelsize=self.FONT_PARAMS['tick']['size'])
        self.ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Legends will be added when data is plotted
        
        # Tight layout to reduce whitespace
        self.fig.tight_layout()

    def calculate_dynamic_scale(self, dff_signal):
        """Calculate dynamic y-scale based on actual signal range after filtering."""
        if dff_signal is None or len(dff_signal) == 0:
            return 20.0  # Default scale
        
        # Use actual signal range with some padding for better visualization
        signal_min = np.min(dff_signal)
        signal_max = np.max(dff_signal)
        signal_range = signal_max - signal_min
        
        # Add 20% padding to the signal range for better visualization
        scale = signal_range * 0.6  # Use 60% of range as scale for normalization
        
        # Ensure minimum scale for very flat signals
        scale = max(scale, 5.0)
        
        print(f"Dynamic scale calculated: {scale:.2f} (range: {signal_range:.2f}, min: {signal_min:.2f}, max: {signal_max:.2f})")
        
        return scale
    
    def get_normalization_ranges(self, primary_scale, secondary_scale=None):
        """Get normalization ranges based on dynamic scales."""
        # Use the larger scale for consistent normalization
        max_scale = max(primary_scale, secondary_scale or primary_scale)
        
        # Define ranges with good separation, each signal gets a band of width = max_scale
        band_width = max_scale
        ranges = {
            'control': (-3.0 * max_scale, -3.0 * max_scale + band_width),
            'raw': (-2.0 * max_scale, -2.0 * max_scale + band_width),
            'fit': (1.5 * max_scale, 1.5 * max_scale + band_width),
            'ttl1': (3.0 * max_scale, 3.0 * max_scale + band_width),
            'ttl2': (4.5 * max_scale, 4.5 * max_scale + band_width)
        }
        return ranges, max_scale
    
    def normalize_signal(self, signal, target_range=(0, 1)):
        """Normalize signal to target range."""
        if signal is None or len(signal) == 0:
            return None
        signal_min = np.min(signal)
        signal_max = np.max(signal)
        if signal_max == signal_min:
            return np.full_like(signal, target_range[0])
        # Normalize to [0, 1] then scale to target range
        normalized = (signal - signal_min) / (signal_max - signal_min)
        return normalized * (target_range[1] - target_range[0]) + target_range[0]

    def update_visibility(self, **kwargs):
        """Update visibility of different signal types."""
        visibility_map = {
            'primary_dff': ('primary', 'dff'),
            'primary_raw': ('primary', 'raw'),
            'primary_control': ('primary', 'isos'),
            'primary_ttl1': ('primary', 'digital1'),
            'primary_ttl2': ('primary', 'digital2'),
            'secondary_dff': ('secondary', 'dff'),
            'secondary_raw': ('secondary', 'raw'),
            'secondary_control': ('secondary', 'isos'),
            'secondary_ttl1': ('secondary', 'digital1'),
            'secondary_ttl2': ('secondary', 'digital2')
        }
        
        for key, value in kwargs.items():
            if key in visibility_map:
                signal_type, signal_name = visibility_map[key]
                line_key = f'{signal_type}_{signal_name}'
                if line_key in self.lines:
                    self.lines[line_key].set_visible(value)
        
        self.redraw()

    def update_plots(self, primary_data, secondary_data=None, plot_only_dff=False):
        """Update all plots with new data. Primary data in ax1, secondary data in ax2."""
        self.clear_all_plots()
        
        # Calculate dynamic scales based on ΔF/F signals
        primary_scale = self.calculate_dynamic_scale(primary_data.get('dff') if primary_data else None)
        secondary_scale = self.calculate_dynamic_scale(secondary_data.get('dff') if secondary_data else None)
        
        # Get normalization ranges and max scale
        self.norm_ranges, self.max_scale = self.get_normalization_ranges(primary_scale, secondary_scale)
        
        # Plot primary data in first panel (ax1)
        if primary_data:
            self.plot_dff(primary_data, 'primary', ax=self.ax1)
            if not plot_only_dff:
                self.plot_raw(primary_data, 'primary', ax=self.ax1)
                self.plot_isos(primary_data, 'primary', ax=self.ax1)
                self.plot_fit(primary_data, 'primary', ax=self.ax1)
                self.plot_digital1(primary_data, 'primary', ax=self.ax1)
                self.plot_digital2(primary_data, 'primary', ax=self.ax1)
        
        # Plot secondary data in second panel (ax2)
        if secondary_data:
            self.plot_dff(secondary_data, 'secondary', ax=self.ax2)
            if not plot_only_dff:
                self.plot_raw(secondary_data, 'secondary', ax=self.ax2)
                self.plot_isos(secondary_data, 'secondary', ax=self.ax2)
                self.plot_fit(secondary_data, 'secondary', ax=self.ax2)
                self.plot_digital1(secondary_data, 'secondary', ax=self.ax2)
                self.plot_digital2(secondary_data, 'secondary', ax=self.ax2)
        
        # Set automatic y-limits based on the calculated scale
        self.set_automatic_ylimits()
        
        self.redraw()

    def plot_dff(self, data, signal_type, ax=None):
        """Plots dF/F signal."""
        if data and data.get('time', np.array([])).size > 0 and data.get('dff', np.array([])).size > 0:
            time = data['time']
            dff = data['dff']
            path = data.get('path', f'{signal_type.capitalize()} Data')
            # Extract filename without extension for shorter label
            filename = os.path.splitext(os.path.basename(path))[0]
            color = self.colors[signal_type]['dff']
            ax = ax or self.ax1
            line, = ax.plot(time, dff, color=color, label=f"ΔF/F Signal")
            self.lines[f'{signal_type}_dff'] = line

    def plot_raw(self, data, signal_type, ax=None):
        """Plots normalized raw signal."""
        if data and data.get('time', np.array([])).size > 0 and data.get('raw1', np.array([])).size > 0:
            time = data['time']
            # Use dynamic normalization range
            target_range = getattr(self, 'norm_ranges', {}).get('raw', (-15, -5))
            raw = self.normalize_signal(data['raw1'], target_range=target_range)
            path = data.get('path', f'{signal_type.capitalize()} Data')
            color = self.colors[signal_type]['raw']
            ax = ax or (self.ax1 if signal_type == 'primary' else self.ax2)
            line, = ax.plot(time, raw, color=color, label=f"Raw Signal")
            self.lines[f'{signal_type}_raw'] = line

    def plot_isos(self, data, signal_type, ax=None):
        """Plots normalized isosbestic signal."""
        if data and data.get('time', np.array([])).size > 0 and data.get('raw2', np.array([])).size > 0:
            time = data['time']
            # Use dynamic normalization range
            target_range = getattr(self, 'norm_ranges', {}).get('control', (-25, -15))
            isos = self.normalize_signal(data['raw2'], target_range=target_range)
            path = data.get('path', f'{signal_type.capitalize()} Data')
            color = self.colors[signal_type]['isos']
            ax = ax or (self.ax1 if signal_type == 'primary' else self.ax2)
            line, = ax.plot(time, isos, color=color, label=f"Control Signal")
            self.lines[f'{signal_type}_isos'] = line

    def plot_fit(self, data, signal_type, ax=None):
        """Plots normalized fitted bleaching correction."""
        if data and data.get('time', np.array([])).size > 0 and data.get('fit', np.array([])).size > 0:
            time = data['time']
            # Use dynamic normalization range
            target_range = getattr(self, 'norm_ranges', {}).get('fit', (15, 25))
            fit = self.normalize_signal(data['fit'], target_range=target_range)
            path = data.get('path', f'{signal_type.capitalize()} Data')
            color = self.colors[signal_type]['fit']
            ax = ax or (self.ax1 if signal_type == 'primary' else self.ax2)
            line, = ax.plot(time, fit, color=color, linestyle='--', label=f"Fitted Baseline")
            self.lines[f'{signal_type}_fit'] = line

    def plot_digital1(self, data, signal_type, ax=None):
        """Plots digital input 1 signal."""
        if data and data.get('time_raw', np.array([])).size > 0 and data.get('digital1', np.array([])).size > 0:
            time_raw = data['time_raw']
            digital1 = data['digital1']
            path = data.get('path', f'{signal_type.capitalize()} Data')
            color = self.colors[signal_type]['ttl1']
            ax = ax or (self.ax1 if signal_type == 'primary' else self.ax2)
            # Use dynamic normalization range
            target_range = getattr(self, 'norm_ranges', {}).get('ttl1', (35, 45))
            digital1_norm = digital1 * (target_range[1] - target_range[0]) + target_range[0]
            line, = ax.plot(time_raw, digital1_norm, color=color, drawstyle='steps-post', label=f"TTL1 Signal", linewidth=2)
            self.lines[f'{signal_type}_digital1'] = line
            
    def plot_digital2(self, data, signal_type, ax=None):
        """Plots digital input 2 signal."""
        if data and data.get('time_raw', np.array([])).size > 0 and data.get('digital2', np.array([])).size > 0:
            time_raw = data['time_raw']
            digital2 = data['digital2']
            path = data.get('path', f'{signal_type.capitalize()} Data')
            color = self.colors[signal_type]['ttl2']
            ax = ax or (self.ax1 if signal_type == 'primary' else self.ax2)
            # Use dynamic normalization range
            target_range = getattr(self, 'norm_ranges', {}).get('ttl2', (50, 60))
            digital2_norm = digital2 * (target_range[1] - target_range[0]) + target_range[0]
            line, = ax.plot(time_raw, digital2_norm, color=color, drawstyle='steps-post', label=f"TTL2 Signal", linewidth=2)
            self.lines[f'{signal_type}_digital2'] = line

    def clear_all_plots(self):
        """Clear all plots."""
        self.ax1.clear()
        self.ax2.clear()
        
        # Reset titles and labels
        self.ax1.set_title('Primary File Signals', fontdict=self.FONT_PARAMS['title'])
        self.ax1.set_ylabel('ΔF/F (%) / Normalized Signal', fontsize=self.FONT_PARAMS['label']['size'])
        self.ax1.grid(True, linestyle='--', alpha=0.7)
        
        self.ax2.set_title('Secondary File Signals', fontdict=self.FONT_PARAMS['title'])
        self.ax2.set_ylabel('ΔF/F (%) / Normalized Signal', fontsize=self.FONT_PARAMS['label']['size'])
        self.ax2.set_xlabel('Time (s)', fontsize=self.FONT_PARAMS['label']['size'])
        self.ax2.grid(True, linestyle='--', alpha=0.7)
        
        self.lines = {}
    
    def set_automatic_ylimits(self):
        """Set automatic y-limits based on the calculated scale."""
        if hasattr(self, 'max_scale') and self.max_scale:
            # Set y-limits to show all normalized signals with good spacing
            # Main ΔF/F signal should be centered around 0 with ±max_scale range
            y_min = -3.5 * self.max_scale  # Bottom padding for control signals
            y_max = 6.0 * self.max_scale   # Top padding for TTL signals
            
            self.ax1.set_ylim(y_min, y_max)
            self.ax2.set_ylim(y_min, y_max)
    
    def clear_secondary_plots(self):
        """Clear only secondary signal plots."""
        for line in self.lines.values():
            if line:
                line.remove()
        self.lines = {}
        self.ax1.legend()
        self.ax2.legend()
    
    def clear_annotations(self, annotation_type):
        """Clear specific type of annotations from the plot."""
        if annotation_type in self.annotations:
            for ann in self.annotations[annotation_type]:
                try:
                    # Try to remove from both axes
                    if ann in self.ax1.collections:
                        ann.remove()
                    elif ann in self.ax2.collections:
                        ann.remove()
                except (ValueError, AttributeError):
                    # If removal fails, try alternative method
                    try:
                        ann.set_visible(False)
                    except:
                        pass
            self.annotations[annotation_type] = []
            self.redraw()

    def draw_points(self, point_type, ax, x, y, **kwargs):
        """Draw points on the plot."""
        if x is not None and y is not None and x.size > 0 and y.size > 0:
            scatter = ax.scatter(x, y, **kwargs)
            if point_type in self.annotations:
                self.annotations[point_type].append(scatter)
            self.redraw()

    def connect_legend_events(self):
        """Connect legend click events for both axes."""
        self.fig.canvas.mpl_connect('button_press_event', self.on_legend_click)
    
    def on_legend_click(self, event):
        """Handle legend click events to toggle line visibility."""
        # Check if click is on legend
        if event.inaxes is None:
            return
            
        # Get the axes that was clicked
        ax = event.inaxes
        
        # Check if click is within legend bounds
        legend = ax.get_legend()
        if legend is None:
            return
            
        # Check if click is on legend
        if legend.contains(event)[0]:
            # Find which legend item was clicked
            for legline, origline in zip(legend.get_lines(), legend.get_texts()):
                if legline.contains(event)[0]:
                    # Find the corresponding line in our lines dictionary
                    label = origline.get_text()
                    line_key = self.find_line_key_by_label(label)
                    if line_key and line_key in self.lines:
                        # Toggle visibility
                        line = self.lines[line_key]
                        is_visible = not line.get_visible()
                        line.set_visible(is_visible)
                        
                        # Update legend line appearance
                        legline.set_alpha(1.0 if is_visible else 0.3)
                        
                        # Redraw canvas
                        self.canvas.draw()
                        break
    
    def find_line_key_by_label(self, label):
        """Find the line key corresponding to a legend label."""
        label_map = {
            'ΔF/F Signal': ['primary_dff', 'secondary_dff'],
            'Raw Signal': ['primary_raw', 'secondary_raw'],
            'Control Signal': ['primary_isos', 'secondary_isos'],
            'Fitted Baseline': ['primary_fit', 'secondary_fit'],
            'TTL1 Signal': ['primary_digital1', 'secondary_digital1'],
            'TTL2 Signal': ['primary_digital2', 'secondary_digital2']
        }
        
        if label in label_map:
            # Return the first matching key found in our lines dictionary
            for key in label_map[label]:
                if key in self.lines:
                    return key
        return None

    def redraw(self):
        """Redraw the canvas."""
        # Create legends with picker enabled
        legend1 = self.ax1.legend(loc='upper right', fontsize=self.FONT_PARAMS['legend']['size'])
        legend2 = self.ax2.legend(loc='upper right', fontsize=self.FONT_PARAMS['legend']['size'])
        
        # Enable picking on legend items
        if legend1:
            legend1.set_picker(True)
            for legline in legend1.get_lines():
                legline.set_picker(True)
                legline.set_pickradius(10)
        
        if legend2:
            legend2.set_picker(True)
            for legline in legend2.get_lines():
                legline.set_picker(True)
                legline.set_pickradius(10)
        
        self.fig.tight_layout()
        self.canvas.draw()
        
    def on_legend_pick(self, event):
        """Handle legend picking to toggle line visibility."""
        # Ensure event and artists are valid
        if event is None or event.artist is None:
            return
            
        legline = event.artist
        origline = legline.origline
        
        # Ensure origline is a valid Line2D object
        if not isinstance(origline, matplotlib.lines.Line2D):
            return

        is_visible = not origline.get_visible()
        origline.set_visible(is_visible)

        # Find the line's key in our lines dictionary to store state
        # Iterate over a copy of keys in case the dictionary is modified during iteration
        for key in list(self.lines.keys()):
             line_obj = self.lines.get(key) # Use .get() to avoid KeyError if key is removed
             if line_obj is not None and line_obj == origline:
                 line_obj.set_visible(is_visible)
                 break

        legline.set_alpha(1.0 if is_visible else 0.2)
        self.canvas.draw()

    def get_current_data(self):
        """Get the current data being displayed."""
        if hasattr(self, 'master') and hasattr(self.master, 'primary_data'):
            return self.master.primary_data
        return None