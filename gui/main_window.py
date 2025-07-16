# file: gui/main_window.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import numpy as np
import os
import traceback
import csv
import logging
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

from .plot_manager import PlotManager
from .control_panel import ControlPanel
from .ai_assistant_panel import AIAssistantPanel
from data_io import read_ppd_file, parse_ppd_data
from signal_processing import process_data_pipeline, advanced_denoise_signal
from analysis.peak_analysis import find_peaks_valleys, calculate_peak_metrics, calculate_valley_metrics, calculate_intervals

class PhotometryViewer:
    def __init__(self, root):
        """Initialize the main window."""
        self.root = root
        self.root.title("Photometry Viewer")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set default downsampling factor for acceleration
        self.downsample_factor = 50
        
        # Initialize data storage
        self.primary_data = None
        self.secondary_data = None
        
        # Initialize visibility control variables
        self.primary_dff_var = tk.BooleanVar(value=True)
        self.primary_raw_var = tk.BooleanVar(value=True)
        self.primary_control_var = tk.BooleanVar(value=True)
        self.primary_ttl1_var = tk.BooleanVar(value=True)
        self.primary_ttl2_var = tk.BooleanVar(value=True)
        self.secondary_dff_var = tk.BooleanVar(value=True)
        self.secondary_raw_var = tk.BooleanVar(value=True)
        self.secondary_control_var = tk.BooleanVar(value=True)
        self.secondary_ttl1_var = tk.BooleanVar(value=True)
        self.secondary_ttl2_var = tk.BooleanVar(value=True)
        
        # Initialize blanking-related attributes
        self.blanking_active = False
        self.blanking_start_x = None
        self.blanking_rect = None
        self.blanking_ax = None
        self.blanking_regions = []

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create menu
        self.create_menu()
        
        # Create layout
        self.create_layout()
        
        # Initialize plot manager
        self.plot_manager = PlotManager(self.plot_frame)
        
        # Initialize filter parameters
        self._init_filter_params()
        
        # Initialize control panel
        self.control_panel = ControlPanel(self.control_frame, self)
        # 初始化metrics表格
        self._init_metrics_tables()
        
        # Initialize AI assistant panel
        self.ai_assistant = AIAssistantPanel(self.ai_frame, self)
        
        # Bind visibility variables
        self.bind_visibility_variables()
        
        # Connect events
        self.connect_events()
        
        logging.info("PhotometryViewer initialization completed")

    def create_layout(self):
        """Create the main layout of the application."""
        # Create horizontal split layout
        self.paned_window = ttk.PanedWindow(self.main_container, orient='horizontal')
        self.paned_window.pack(fill='both', expand=True)
        
        # Create plot frame (60% width)
        self.plot_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.plot_frame, weight=3)
        
        # Create right side tabbed interface (40% width)
        self.right_notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.right_notebook, weight=2)
        
        # Create control frame as first tab
        self.control_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.control_frame, text="Analysis Controls")
        
        # Create AI assistant frame as second tab
        self.ai_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.ai_frame, text="AI Assistant")
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief='sunken', padding=(5, 2))
        self.status_bar.pack(side='bottom', fill='x')

    def _init_filter_params(self):
        """Initialize filter parameters."""
        self.low_cutoff = tk.DoubleVar(value=0.001)
        self.high_cutoff = tk.DoubleVar(value=5.0)
        self.drift_degree = tk.IntVar(value=2)
        self.drift_correction = tk.BooleanVar(value=True)
        self.edge_protection = tk.BooleanVar(value=True)
        self.time_shift_s = tk.DoubleVar(value=0.0)
        self.artifact_threshold = tk.DoubleVar(value=3.0)
        self.denoise_aggressive = tk.BooleanVar(value=True)
        self.peak_prominence = tk.DoubleVar(value=5.0)
        self.peak_width_s = tk.DoubleVar(value=0.5)
        self.peak_distance_s = tk.DoubleVar(value=2.0)
        self.show_peaks = tk.BooleanVar(value=True)
        self.show_valleys = tk.BooleanVar(value=True)
        self.analysis_signal_source = tk.StringVar(value="Primary")
        self.filter_type = tk.StringVar(value='Bandpass')
        self.filter_order = tk.IntVar(value=2)
        self.zero_phase = tk.BooleanVar(value=True)
        self.downsample_factor = tk.IntVar(value=50)
        self.filter_raw_signals = tk.BooleanVar(value=True)
        
        # PSTH parameters
        self.psth_event_type = tk.StringVar(value='Peaks')
        self.psth_signal_source = tk.StringVar(value='Primary')
        self.psth_pre_time = tk.DoubleVar(value=5.0)
        self.psth_post_time = tk.DoubleVar(value=10.0)
        self.psth_bin_size = tk.DoubleVar(value=0.1)
        
        # Correlation parameters
        self.corr_signal1 = tk.StringVar(value='Primary ΔF/F')
        self.corr_signal2 = tk.StringVar(value='Secondary ΔF/F')
        self.corr_max_lag = tk.DoubleVar(value=10.0)
        self.corr_window = tk.DoubleVar(value=5.0)

    def update_psth_bin_size(self):
        """Update PSTH bin size based on effective sample rate."""
        try:
            # Get current downsample factor
            downsample_factor = self.downsample_factor.get()
            
            # Calculate effective sample rate (assume 1000 Hz original if no data loaded)
            effective_fs = 1000.0 / downsample_factor
            
            # Get data if available for more accurate calculation
            if self.primary_data and 'fs' in self.primary_data:
                effective_fs = self.primary_data['fs']
            elif self.secondary_data and 'fs' in self.secondary_data:
                effective_fs = self.secondary_data['fs']
            
            # Calculate appropriate bin size (minimum 2 samples per bin)
            min_bin_size = 2.0 / effective_fs
            
            # Set reasonable bin size (round to nearest 0.01)
            if effective_fs >= 50:  # High sample rate
                suggested_bin_size = 0.1
            elif effective_fs >= 20:  # Medium sample rate
                suggested_bin_size = 0.2
            else:  # Low sample rate
                suggested_bin_size = 0.5
            
            # Ensure bin size is at least minimum
            suggested_bin_size = max(suggested_bin_size, min_bin_size)
            
            # Update the bin size
            self.psth_bin_size.set(suggested_bin_size)
            
            print(f"Updated PSTH bin size to {suggested_bin_size:.3f}s (effective fs: {effective_fs:.1f} Hz)")
            
        except Exception as e:
            print(f"Error updating PSTH bin size: {e}")

    def create_menu(self):
        """Create the main menu bar."""
        # 设置全局菜单字体
        self.root.option_add('*Menu.font', 'TkDefaultFont 14')
        self.menu_bar = tk.Menu(self.root, font=('TkDefaultFont', 14))
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Primary File", command=lambda: self.open_file(is_secondary=False))
        file_menu.add_command(label="Load Secondary File", command=lambda: self.open_file(is_secondary=True))
        file_menu.add_command(label="Clear Secondary", command=self.clear_secondary)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Reset View", command=self.reset_view)
        view_menu.add_command(label="Toggle Legend", command=self.toggle_legend)
        
        # Analysis menu
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Detect Peaks", command=self.detect_peaks)
        analysis_menu.add_command(label="Detect Valleys", command=self.detect_valleys)
        analysis_menu.add_command(label="Clear Peaks", command=self.clear_peaks)
        analysis_menu.add_command(label="Clear Valleys", command=self.clear_valleys)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Export Metrics", command=lambda: self.export_metrics('Peak'))
        
        # AI Assistant menu
        ai_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="AI Assistant", menu=ai_menu)
        ai_menu.add_command(label="Share Data Context", command=self.share_data_with_ai)
        ai_menu.add_command(label="API Settings", command=self.show_ai_settings)
        ai_menu.add_command(label="Clear Chat", command=self.clear_ai_chat)
        ai_menu.add_separator()
        ai_menu.add_command(label="Help", command=self.show_ai_help)
        
        # Performance menu
        perf_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Performance", menu=perf_menu)
        perf_menu.add_command(label="GPU Status", command=self.show_gpu_status)
        perf_menu.add_command(label="Benchmark GPU", command=self.benchmark_gpu)
        perf_menu.add_command(label="Memory Usage", command=self.show_memory_usage)

    def open_file(self, is_secondary=False):
        """Open and load a PPD file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("PPD files", "*.ppd"), ("All files", "*.*")]
        )
        if not file_path:
            return
        def load_and_process():
            try:
                self.update_status("Loading and processing data...")
                result = read_ppd_file(file_path)
                if not result:
                    raise ValueError("Failed to read PPD file")
                header, data_bytes = result['header'], result['data_bytes']
                params = self.get_params_as_dict()
                downsample_factor = params['downsample_factor'] if not hasattr(params['downsample_factor'], 'get') else params['downsample_factor'].get()
                print(f"Loading data with downsample_factor: {downsample_factor}")
                data = parse_ppd_data(data_bytes, header, downsample_factor=downsample_factor)
                if not data:
                    raise ValueError("Failed to parse PPD data")
                data['path'] = file_path
                if is_secondary:
                    self.secondary_data = data
                    # Update file display for secondary file with sample rate
                    fs_original = data.get('fs_original', data.get('fs', 'Unknown'))
                    downsample_factor = data.get('downsample_factor', 1)
                    fs_display = f"{fs_original:.0f} Hz"
                    if downsample_factor > 1:
                        fs_display += f" (downsampled to {fs_original/downsample_factor:.0f} Hz)"
                    self.control_panel.update_file_display(secondary_file=file_path, secondary_fs=fs_display)
                else:
                    self.primary_data = data
                    # Update file display for primary file with sample rate
                    fs_original = data.get('fs_original', data.get('fs', 'Unknown'))
                    downsample_factor = data.get('downsample_factor', 1)
                    fs_display = f"{fs_original:.0f} Hz"
                    if downsample_factor > 1:
                        fs_display += f" (downsampled to {fs_original/downsample_factor:.0f} Hz)"
                    self.control_panel.update_file_display(primary_file=file_path, primary_fs=fs_display)
                
                # Update PSTH bin size based on new data
                self.update_psth_bin_size()
                
                # Only plot dF/F by default
                self.plot_manager.update_plots(self.primary_data, self.secondary_data, plot_only_dff=True)
                self.update_status(f"Loaded {'secondary' if is_secondary else 'primary'} file: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                traceback.print_exc()
        threading.Thread(target=load_and_process, daemon=True).start()

    def update_filter(self):
        """Update the signal processing with current filter parameters."""
        if not self.primary_data:
            return
        self.clear_detection('Peak')
        self.clear_detection('Valley')
        self.update_status("Applying filters...")
        def process_and_update():
            params = self.get_params_as_dict()
            filter_type = params['filter_type'] if not hasattr(params['filter_type'], 'get') else params['filter_type'].get()
            filter_order = params['filter_order'] if not hasattr(params['filter_order'], 'get') else params['filter_order'].get()
            zero_phase = params['zero_phase'] if not hasattr(params['zero_phase'], 'get') else params['zero_phase'].get()
            low_cutoff = params['low_cutoff'] if not hasattr(params['low_cutoff'], 'get') else params['low_cutoff'].get()
            high_cutoff = params['high_cutoff'] if not hasattr(params['high_cutoff'], 'get') else params['high_cutoff'].get()
            drift_correction = params['drift_correction'] if not hasattr(params['drift_correction'], 'get') else params['drift_correction'].get()
            drift_degree = params['drift_degree'] if not hasattr(params['drift_degree'], 'get') else params['drift_degree'].get()
            downsample_factor = params['downsample_factor'] if not hasattr(params['downsample_factor'], 'get') else params['downsample_factor'].get()
            edge_protection = params['edge_protection'] if not hasattr(params['edge_protection'], 'get') else params['edge_protection'].get()
            filter_raw_signals = params['filter_raw_signals'] if not hasattr(params['filter_raw_signals'], 'get') else params['filter_raw_signals'].get()
            # Process primary data
            if self.primary_data:
                time_raw = self.primary_data['time_raw']
                analog_1_raw = self.primary_data['analog_1_raw']
                analog_2_raw = self.primary_data['analog_2_raw']
                fs = self.primary_data['fs']
                time_ds, dff_ds, raw1_ds, raw2_ds, drift_ds, artifact_mask = process_data_pipeline(
                    time_raw=time_raw,
                    signal_raw=analog_1_raw,
                    control_raw=analog_2_raw,
                    fs=fs,
                    low_cutoff=low_cutoff,
                    high_cutoff=high_cutoff,
                    filter_type=filter_type,
                    filter_order=filter_order,
                    zero_phase=zero_phase,
                    drift_correction=drift_correction,
                    drift_degree=drift_degree,
                    downsample_factor=downsample_factor,
                    edge_protection=edge_protection,
                    filter_raw_signals=filter_raw_signals
                )
                self.primary_data['time'] = time_ds
                self.primary_data['dff'] = dff_ds
                self.primary_data['raw1'] = raw1_ds
                self.primary_data['raw2'] = raw2_ds
                self.primary_data['fit'] = drift_ds
                self.primary_data['artifact_mask'] = artifact_mask
            # Process secondary data
            if self.secondary_data:
                time_raw = self.secondary_data['time_raw']
                analog_1_raw = self.secondary_data['analog_1_raw']
                analog_2_raw = self.secondary_data['analog_2_raw']
                fs = self.secondary_data['fs']
                time_ds, dff_ds, raw1_ds, raw2_ds, drift_ds, artifact_mask = process_data_pipeline(
                    time_raw=time_raw,
                    signal_raw=analog_1_raw,
                    control_raw=analog_2_raw,
                    fs=fs,
                    low_cutoff=low_cutoff,
                    high_cutoff=high_cutoff,
                    filter_type=filter_type,
                    filter_order=filter_order,
                    zero_phase=zero_phase,
                    drift_correction=drift_correction,
                    drift_degree=drift_degree,
                    downsample_factor=downsample_factor,
                    edge_protection=edge_protection,
                    filter_raw_signals=filter_raw_signals
                )
                self.secondary_data['time'] = time_ds
                self.secondary_data['dff'] = dff_ds
                self.secondary_data['raw1'] = raw1_ds
                self.secondary_data['raw2'] = raw2_ds
                self.secondary_data['fit'] = drift_ds
                self.secondary_data['artifact_mask'] = artifact_mask
            self.plot_manager.update_plots(self.primary_data, self.secondary_data, plot_only_dff=True)
            self.update_status('Filters applied successfully.')
        threading.Thread(target=process_and_update, daemon=True).start()

    def run_detection(self, mode):
        """Run peak or valley detection on the selected signal."""
        source = self.analysis_signal_source.get()
        data = self.primary_data if source == "Primary" else self.secondary_data
        
        if not data or data.get('dff') is None:
            messagebox.showinfo("Info", f"No processed data for {source} signal.")
            return
        
        try:
            fs_ds = data['fs']
            params = {
                'prominence': self.peak_prominence.get(),
                'width_s': self.peak_width_s.get(),
                'distance_s': self.peak_distance_s.get()
            }
            
            peaks, valleys = find_peaks_valleys(data['dff'], data['time'], fs_ds, **params)
            
            if mode == 'Peak':
                # Always store peaks data, even if empty
                data['peaks'] = peaks
                # Calculate metrics if peaks found
                if peaks['indices'].size > 0:
                    data['peak_metrics'] = calculate_peak_metrics(peaks, valleys, data['dff'], data['time'])
                else:
                    data['peak_metrics'] = None
                    
                # Update results window regardless of whether peaks were found
                result_text = f"Peak Detection Results\n"
                result_text += f"=" * 30 + "\n"
                result_text += f"Signal: {source}\n"
                result_text += f"Peaks detected: {len(peaks['indices'])}\n"
                result_text += f"Prominence threshold: {params['prominence']:.2f}\n"
                result_text += f"Width threshold: {params['width_s']:.2f}s\n"
                result_text += f"Distance threshold: {params['distance_s']:.2f}s\n"
                
                if len(peaks['indices']) > 0:
                    result_text += f"Mean peak height: {np.mean(peaks['heights']):.3f}\n"
                    result_text += f"Peak height range: {np.min(peaks['heights']):.3f} - {np.max(peaks['heights']):.3f}\n"
                    if len(peaks['times']) > 1:
                        result_text += f"Mean inter-peak interval: {np.mean(np.diff(peaks['times'])):.2f}s\n"
                    result_text += f"\nPeak times (first 10): {list(peaks['times'][:10])}\n"
                    result_text += f"\nPeak data is now available for PSTH analysis.\n"
                else:
                    result_text += f"No peaks found with current parameters.\n"
                    result_text += f"Try adjusting prominence, width, or distance thresholds.\n"
                
                self.update_peak_results(result_text)
                
            else:  # Valley
                # Always store valleys data, even if empty
                data['valleys'] = valleys
                # Calculate metrics if valleys found
                if valleys['indices'].size > 0:
                    data['valley_metrics'] = calculate_valley_metrics(peaks, valleys, data['dff'], data['time'])
                else:
                    data['valley_metrics'] = None
                
            # Update results window regardless of whether valleys were found
            result_text = f"Valley Detection Results\n"
            result_text += f"=" * 30 + "\n"
            result_text += f"Signal: {source}\n"
            result_text += f"Valleys detected: {len(valleys['indices'])}\n"
            result_text += f"Prominence threshold: {params['prominence']:.2f}\n"
            result_text += f"Width threshold: {params['width_s']:.2f}s\n"
            result_text += f"Distance threshold: {params['distance_s']:.2f}s\n"
            
            if len(valleys['indices']) > 0:
                result_text += f"Mean valley depth: {np.mean(valleys['depths']):.3f}\n"
                result_text += f"Valley depth range: {np.min(valleys['depths']):.3f} - {np.max(valleys['depths']):.3f}\n"
                if len(valleys['times']) > 1:
                    result_text += f"Mean inter-valley interval: {np.mean(np.diff(valleys['times'])):.2f}s\n"
                result_text += f"\nValley times (first 10): {list(valleys['times'][:10])}\n"
                result_text += f"\nValley data is now available for PSTH analysis.\n"
            else:
                result_text += f"No valleys found with current parameters.\n"
                result_text += f"Try adjusting prominence, width, or distance thresholds.\n"
            
            self.update_peak_results(result_text)
        
            # Update displays and metrics regardless of detection results
            self.update_peak_display()
            self.populate_metrics_table()
            
            # Update status
            status_msg = f"{mode} detection completed"
            if mode == 'Peak' and peaks['indices'].size > 0:
                status_msg += f": {len(peaks['indices'])} peaks found"
            elif mode == 'Valley' and valleys['indices'].size > 0:
                status_msg += f": {len(valleys['indices'])} valleys found"
            else:
                status_msg += ": no events found"
            self.update_status(status_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run {mode.lower()} detection: {str(e)}")
            logging.error(f"Error in run_detection: {str(e)}")
            import traceback
            traceback.print_exc()

    def populate_metrics_table(self):
        """Populate the metrics tables with peak and valley data."""
        # Clear existing data
        self.peak_metrics_tree.delete(*self.peak_metrics_tree.get_children())
        self.valley_metrics_tree.delete(*self.valley_metrics_tree.get_children())
        
        # Update primary data metrics
        if self.primary_data and self.primary_data.get('peak_metrics'):
            metrics = self.primary_data['peak_metrics']
            for i, (area, fwhm, rise, decay) in enumerate(zip(
                metrics['area'], metrics['fwhm'], metrics['rise_time'], metrics['decay_time']
            )):
                self.peak_metrics_tree.insert('', 'end', values=(
                    i + 1,
                    f"{self.primary_data['peaks']['times'][i]:.2f}",
                    f"{self.primary_data['peaks']['heights'][i]:.2f}",
                    f"{fwhm:.2f}",
                    f"{area:.2f}",
                    f"{rise:.2f}",
                    f"{decay:.2f}"
                ))
        
        if self.primary_data and self.primary_data.get('valley_metrics'):
            metrics = self.primary_data['valley_metrics']
            for i, (area, fwhm) in enumerate(zip(metrics['area_above'], metrics['fwhm'])):
                self.valley_metrics_tree.insert('', 'end', values=(
                    i + 1,
                    f"{self.primary_data['valleys']['times'][i]:.2f}",
                    f"{self.primary_data['valleys']['depths'][i]:.2f}",
                    f"{fwhm:.2f}",
                    f"{area:.2f}"
                ))
        
        # Update secondary data metrics
        if self.secondary_data and self.secondary_data.get('peak_metrics'):
            metrics = self.secondary_data['peak_metrics']
            for i, (area, fwhm, rise, decay) in enumerate(zip(
                metrics['area'], metrics['fwhm'], metrics['rise_time'], metrics['decay_time']
            )):
                self.peak_metrics_tree.insert('', 'end', values=(
                    f"S{i + 1}",
                    f"{self.secondary_data['peaks']['times'][i]:.2f}",
                    f"{self.secondary_data['peaks']['heights'][i]:.2f}",
                    f"{fwhm:.2f}",
                    f"{area:.2f}",
                    f"{rise:.2f}",
                    f"{decay:.2f}"
                ))
        
        if self.secondary_data and self.secondary_data.get('valley_metrics'):
            metrics = self.secondary_data['valley_metrics']
            for i, (area, fwhm) in enumerate(zip(metrics['area_above'], metrics['fwhm'])):
                self.valley_metrics_tree.insert('', 'end', values=(
                    f"S{i + 1}",
                    f"{self.secondary_data['valleys']['times'][i]:.2f}",
                    f"{self.secondary_data['valleys']['depths'][i]:.2f}",
                    f"{fwhm:.2f}",
                    f"{area:.2f}"
                ))

    def analyze_intervals(self, mode):
        """Analyze intervals between peaks or valleys."""
        source = self.analysis_signal_source.get()
        data = self.primary_data if source == "Primary" else self.secondary_data
        
        if not data:
            messagebox.showinfo("Info", f"No {source.lower()} data loaded.")
            return
        
        if mode == 'Peak' and data.get('peaks'):
            times = data['peaks']['times']
        elif mode == 'Valley' and data.get('valleys'):
            times = data['valleys']['times']
        else:
            messagebox.showinfo("Info", f"No {mode.lower()}s detected in {source.lower()} data.")
            return
        
        intervals = calculate_intervals(times)
        if intervals:
            message = (
                f"{mode} Intervals Analysis:\n"
                f"Count: {intervals['count']}\n"
                f"Mean: {intervals['mean']:.2f}s\n"
                f"Median: {intervals['median']:.2f}s\n"
                f"Std: {intervals['std']:.2f}s\n"
                f"Min: {intervals['min']:.2f}s\n"
                f"Max: {intervals['max']:.2f}s"
            )
            messagebox.showinfo(f"{mode} Intervals", message)

    def export_metrics(self, mode):
        """Export peak or valley metrics to a CSV file."""
        source = self.analysis_signal_source.get()
        data = self.primary_data if source == "Primary" else self.secondary_data
        
        if not data:
            messagebox.showinfo("Info", f"No {source.lower()} data loaded.")
            return
        
        if mode == 'Peak' and data.get('peak_metrics'):
            metrics = data['peak_metrics']
            times = data['peaks']['times']
            heights = data['peaks']['heights']
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title=f"Export {source} Peak Metrics"
            )
            if filename:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (s)', 'Height', 'FWHM (s)', 'Area', 'Rise Time (s)', 'Decay Time (s)'])
                    for i in range(len(times)):
                        writer.writerow([
                            f"{times[i]:.2f}",
                            f"{heights[i]:.2f}",
                            f"{metrics['fwhm'][i]:.2f}",
                            f"{metrics['area'][i]:.2f}",
                            f"{metrics['rise_time'][i]:.2f}",
                            f"{metrics['decay_time'][i]:.2f}"
                        ])
                self.update_status(f"Exported peak metrics to {os.path.basename(filename)}")
        
        elif mode == 'Valley' and data.get('valley_metrics'):
            metrics = data['valley_metrics']
            times = data['valleys']['times']
            depths = data['valleys']['depths']
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title=f"Export {source} Valley Metrics"
            )
            if filename:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (s)', 'Depth', 'FWHM (s)', 'Area Above'])
                    for i in range(len(times)):
                        writer.writerow([
                            f"{times[i]:.2f}",
                            f"{depths[i]:.2f}",
                            f"{metrics['fwhm'][i]:.2f}",
                            f"{metrics['area_above'][i]:.2f}"
                        ])
                self.update_status(f"Exported valley metrics to {os.path.basename(filename)}")
        
        else:
            messagebox.showinfo("Info", f"No {mode.lower()}s detected in {source.lower()} data.")

    def get_params_as_dict(self):
        """Get all parameters as a dictionary, always returning values not tk.Variable objects."""
        return {
            'filter_type': self.filter_type.get() if hasattr(self, 'filter_type') else 'Bandpass',
            'filter_order': self.filter_order.get() if hasattr(self, 'filter_order') else 2,
            'zero_phase': self.zero_phase.get() if hasattr(self, 'zero_phase') else True,
            'low_cutoff': self.low_cutoff.get() if hasattr(self, 'low_cutoff') else 0.001,
            'high_cutoff': self.high_cutoff.get() if hasattr(self, 'high_cutoff') else 5.0,
            'drift_correction': self.drift_correction.get() if hasattr(self, 'drift_correction') else True,
            'drift_degree': self.drift_degree.get() if hasattr(self, 'drift_degree') else 2,
            'downsample_factor': self.downsample_factor.get() if hasattr(self, 'downsample_factor') else 50,
            'edge_protection': self.edge_protection.get() if hasattr(self, 'edge_protection') else True,
            'filter_raw_signals': self.filter_raw_signals.get() if hasattr(self, 'filter_raw_signals') else True,
            'artifact_threshold': self.artifact_threshold.get() if hasattr(self, 'artifact_threshold') else 3.0,
            'denoise_aggressive': self.denoise_aggressive.get() if hasattr(self, 'denoise_aggressive') else True,
            'peak_prominence': self.peak_prominence.get() if hasattr(self, 'peak_prominence') else 5.0,
            'peak_width_s': self.peak_width_s.get() if hasattr(self, 'peak_width_s') else 0.5,
            'peak_distance_s': self.peak_distance_s.get() if hasattr(self, 'peak_distance_s') else 2.0
        }

    def clear_secondary(self):
        """Clear the secondary data and update the display."""
        self.secondary_data = None
        self.plot_manager.update_plots(self.primary_data, None)
        # Clear secondary file display
        self.control_panel.clear_file_display(clear_secondary=True)
        self.update_status("Secondary data cleared")

    def update_window_title(self):
        """Update the window title based on loaded files."""
        title = "Photometry Viewer"
        if self.primary_data:
            title += f" - {os.path.basename(self.primary_data['path'])}"
        if self.secondary_data:
            title += f" + {os.path.basename(self.secondary_data['path'])}"
        self.root.title(title)

    def clear_detection(self, mode):
        key = f"{mode.lower()}s"; getattr(self, f"clear_{key}")()

    def update_peak_display(self, *args):
        """Update the display of peaks and valleys on the plot."""
        # Clear existing annotations
        self.plot_manager.clear_annotations('peaks')
        self.plot_manager.clear_annotations('valleys')
        
        # Update primary data display (in ax1)
        if self.primary_data and self.primary_data.get('dff') is not None:
            if self.show_peaks.get() and self.primary_data.get('peaks'):
                peaks = self.primary_data['peaks']
                if peaks['indices'].any():
                    self.plot_manager.draw_points(
                        'peaks',
                        self.plot_manager.ax1,
                        peaks['times'],
                        peaks['heights'],
                        color='red',
                        marker='^',
                        s=100,
                        label='Peaks'
                    )
            
            if self.show_valleys.get() and self.primary_data.get('valleys'):
                valleys = self.primary_data['valleys']
                if valleys['indices'].any():
                    self.plot_manager.draw_points(
                        'valleys',
                        self.plot_manager.ax1,
                        valleys['times'],
                        valleys['depths'],
                        color='blue',
                        marker='v',
                        s=100,
                        label='Valleys'
                    )
        
        # Update secondary data display (in ax2)
        if self.secondary_data and self.secondary_data.get('dff') is not None:
            if self.show_peaks.get() and self.secondary_data.get('peaks'):
                peaks = self.secondary_data['peaks']
                if peaks['indices'].any():
                    self.plot_manager.draw_points(
                        'peaks',
                        self.plot_manager.ax2,
                        peaks['times'],
                        peaks['heights'],
                        color='red',
                        marker='^',
                        s=100,
                        label='Peaks'
                    )
            
            if self.show_valleys.get() and self.secondary_data.get('valleys'):
                valleys = self.secondary_data['valleys']
                if valleys['indices'].any():
                    self.plot_manager.draw_points(
                        'valleys',
                        self.plot_manager.ax2,
                        valleys['times'],
                        valleys['depths'],
                        color='blue',
                        marker='v',
                        s=100,
                        label='Valleys'
                    )
        
        self.plot_manager.redraw()

    def highlight_artifacts(self):
        """Highlight detected artifacts on the plot."""
        self.plot_manager.clear_annotations('artifacts')
        
        # Update primary data artifacts (in ax1)
        if self.primary_data and self.primary_data.get('artifact_mask') is not None:
            mask = self.primary_data['artifact_mask']
            if np.any(mask):
                self.plot_manager.draw_points(
                    'artifacts',
                    self.plot_manager.ax1,
                    self.primary_data['time'][mask],
                    self.primary_data['dff'][mask],
                    color='red',
                    marker='x',
                    s=100,
                    label='Artifacts'
                )
        
        # Update secondary data artifacts (in ax2)
        if self.secondary_data and self.secondary_data.get('artifact_mask') is not None:
            mask = self.secondary_data['artifact_mask']
            if np.any(mask):
                self.plot_manager.draw_points(
                    'artifacts',
                    self.plot_manager.ax2,
                    self.secondary_data['time'][mask],
                    self.secondary_data['dff'][mask],
                    color='red',
                    marker='x',
                    s=100,
                    label='Artifacts'
                )
        
        self.plot_manager.redraw()

    def run_advanced_denoising(self):
        """Run advanced denoising on the signals."""
        # Process primary data
        if self.primary_data and self.primary_data.get('dff') is not None:
            denoised = advanced_denoise_signal(
                self.primary_data['dff'],
                self.primary_data['time'],
                self.primary_data['artifact_mask'],
                self.primary_data.get('raw2'),
                self.denoise_aggressive.get()
            )
            if denoised is not None:
                self.primary_data['dff'] = denoised
        
        # Process secondary data
        if self.secondary_data and self.secondary_data.get('dff') is not None:
            denoised = advanced_denoise_signal(
                self.secondary_data['dff'],
                self.secondary_data['time'],
                self.secondary_data['artifact_mask'],
                self.secondary_data.get('raw2'),
                self.denoise_aggressive.get()
            )
            if denoised is not None:
                self.secondary_data['dff'] = denoised
        
        self.plot_manager.update_plots(self.primary_data, self.secondary_data)

    def reset_denoising(self): self.update_filter()

    def toggle_blanking_mode(self):
        """Toggle the blanking mode for manual artifact removal."""
        is_active = self.blanking_button['text'] == "Enable Selection Mode"
        self.blanking_button.config(
            text="Disable Selection Mode" if is_active else "Enable Selection Mode",
            bg="salmon" if is_active else "SystemButtonFace"
        )
        self.plot_manager.canvas.get_tk_widget().config(cursor="crosshair" if is_active else "")
        self.blanking_active = is_active

    def clear_all_blanking(self): self.blanking_regions = []; self.update_filter()

    def reapply_all_blanking(self):
        """Reapply all blanking regions to the signals."""
        if not self.blanking_regions:
            return
            
        for data in [self.primary_data, self.secondary_data]:
            if not data or data.get('dff') is None:
                continue
                
            for region in self.blanking_regions:
                mask = (data['time'] >= region['start']) & (data['time'] <= region['end'])
                if not np.any(mask):
                    continue
                    
                # Find the values before and after the blanked region
                pre_indices = np.where(data['time'] < region['start'])[0]
                post_indices = np.where(data['time'] > region['end'])[0]
                
                if len(pre_indices) > 0 and len(post_indices) > 0:
                    start_val = data['dff'][pre_indices[-1]]
                    end_val = data['dff'][post_indices[0]]
                    # Interpolate between the values
                    data['dff'][mask] = np.linspace(start_val, end_val, np.sum(mask))

    def connect_events(self):
        """Connect all event handlers."""
        # Initialize state variables
        self.ctrl_pressed = False
        self.blanking_active = False
        self.blanking_rect = None
        self.blanking_start_x = None
        
        # Connect keyboard events
        self.root.bind('<Control-Key>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        
        # Connect mouse events
        self.plot_manager.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.plot_manager.canvas.mpl_connect('button_press_event', self.on_blanking_press)
        self.plot_manager.canvas.mpl_connect('motion_notify_event', self.on_blanking_motion)
        self.plot_manager.canvas.mpl_connect('button_release_event', self.on_blanking_release)

    def on_key_press(self, event):
        """Handle key press events."""
        if event.keysym in ('Control_L', 'Control_R'):
            self.ctrl_pressed = True
    
    def on_key_release(self, event):
        """Handle key release events."""
        if event.keysym in ('Control_L', 'Control_R'):
            self.ctrl_pressed = False
    
    def get_data_bounds(self):
        """Get data bounds for zoom limiting."""
        bounds = {'x_min': 0, 'x_max': 100, 'y_min': -50, 'y_max': 50}  # Default bounds
        
        # Get actual data bounds from loaded data
        if self.primary_data and 'time' in self.primary_data:
            time_data = self.primary_data['time']
            if len(time_data) > 0:
                bounds['x_min'] = float(np.min(time_data))
                bounds['x_max'] = float(np.max(time_data))
        
        if self.secondary_data and 'time' in self.secondary_data:
            time_data = self.secondary_data['time']
            if len(time_data) > 0:
                bounds['x_max'] = max(bounds['x_max'], float(np.max(time_data)))
        
        # Use the current plot manager's scale for Y bounds
        if hasattr(self.plot_manager, 'max_scale'):
            bounds['y_min'] = -4.0 * self.plot_manager.max_scale
            bounds['y_max'] = 6.0 * self.plot_manager.max_scale
        
        return bounds

    def on_scroll(self, event):
        """Handle mouse scroll events for zooming with limits to prevent freezing."""
        if event.inaxes is None:
            return
        # 判断Ctrl键（matplotlib事件兼容性处理）
        ctrl_pressed = False
        if hasattr(event, 'key') and event.key == 'control':
            ctrl_pressed = True
        elif hasattr(event, 'guiEvent') and hasattr(event.guiEvent, 'state'):
            # Windows下Ctrl为0x0004
            ctrl_pressed = (event.guiEvent.state & 0x0004) != 0
        # 滚轮方向
        if event.button == 'up':
            factor = 0.9
        else:
            factor = 1.1
        ax = event.inaxes
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        
        # Get data bounds to set reasonable zoom limits
        data_bounds = self.get_data_bounds()
        
        if ctrl_pressed:
            # Y轴缩放
            new_ylim = [ydata - (ydata - cur_ylim[0]) * factor,
                        ydata + (cur_ylim[1] - ydata) * factor]
            # Limit Y zoom to prevent freezing
            y_range = new_ylim[1] - new_ylim[0]
            if y_range > data_bounds['y_max'] * 10:  # Max 10x the data range
                new_ylim = [data_bounds['y_min'] - data_bounds['y_max'], 
                            data_bounds['y_max'] + data_bounds['y_max']]
            elif y_range < data_bounds['y_max'] * 0.001:  # Min 0.1% of data range
                center = (new_ylim[0] + new_ylim[1]) / 2
                half_range = data_bounds['y_max'] * 0.0005
                new_ylim = [center - half_range, center + half_range]
            ax.set_ylim(new_ylim)
        else:
            # X轴缩放
            new_xlim = [xdata - (xdata - cur_xlim[0]) * factor,
                        xdata + (cur_xlim[1] - xdata) * factor]
            # Limit X zoom to prevent freezing
            x_range = new_xlim[1] - new_xlim[0]
            if x_range > data_bounds['x_max'] * 10:  # Max 10x the data range
                new_xlim = [data_bounds['x_min'] - data_bounds['x_max'], 
                            data_bounds['x_max'] + data_bounds['x_max']]
            elif x_range < data_bounds['x_max'] * 0.001:  # Min 0.1% of data range
                center = (new_xlim[0] + new_xlim[1]) / 2
                half_range = data_bounds['x_max'] * 0.0005
                new_xlim = [center - half_range, center + half_range]
            ax.set_xlim(new_xlim)
        self.plot_manager.canvas.draw_idle()

    def on_blanking_press(self, event):
        """Handle mouse press events for blanking mode."""
        if self.blanking_active and event.inaxes:
            self.blanking_start_x = event.xdata
            self.blanking_ax = event.inaxes

    def on_blanking_motion(self, event):
        """Handle mouse motion events for blanking mode."""
        if (self.blanking_active and 
            event.inaxes == self.blanking_ax and 
            hasattr(self, 'blanking_start_x') and 
            self.blanking_start_x is not None):
            
            # Remove previous rectangle if it exists
            if hasattr(self, 'blanking_rect') and self.blanking_rect:
                self.blanking_rect.remove()
            
            # Create new rectangle
            self.blanking_rect = self.blanking_ax.fill_between(
                [self.blanking_start_x, event.xdata],
                *self.blanking_ax.get_ylim(),
                facecolor='gray',
                alpha=0.4
            )
            
            # Redraw the canvas
            self.plot_manager.canvas.draw_idle()

    def on_blanking_release(self, event):
        """Handle mouse release events for blanking mode."""
        if (self.blanking_active and 
            event.inaxes == self.blanking_ax and 
            hasattr(self, 'blanking_start_x') and 
            self.blanking_start_x is not None):
            
            # Get the current data
            data = self.plot_manager.get_current_data()
            if not data:
                return
            
            # Get the time array
            time = data.get('time', [])
            if not time:
                return
            
            # Find the indices for the blanking region
            start_idx = np.searchsorted(time, self.blanking_start_x)
            end_idx = np.searchsorted(time, event.xdata)
            
            # Ensure start_idx is less than end_idx
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
            
            # Add the blanking region
            if 'blanking_regions' not in data:
                data['blanking_regions'] = []
            data['blanking_regions'].append((start_idx, end_idx))
            
            # Reapply blanking
            self.reapply_all_blanking()
            
            # Reset blanking state
            self.blanking_start_x = None
            self.blanking_rect = None
            
            # Redraw the canvas
            self.plot_manager.canvas.draw_idle()

    def apply_time_shift(self):
        """Apply time shift to the secondary signal."""
        if not self.secondary_data:
            messagebox.showinfo("Info", "No secondary data loaded.")
            return
        
        shift = self.time_shift_s.get()
        if shift == 0:
            return
        
        # Apply shift to all time arrays
        self.secondary_data['time'] = self.secondary_data['time'] + shift
        self.secondary_data['time_raw'] = self.secondary_data['time_raw'] + shift
        
        # Update plots
        self.plot_manager.update_plots(self.primary_data, self.secondary_data)

    def on_closing(self): self.root.quit(); self.root.destroy()

    def reset_view(self):
        """Reset the plot view to show all data."""
        if self.primary_data or self.secondary_data:
            self.plot_manager.ax1.relim()
            self.plot_manager.ax1.autoscale_view()
            self.plot_manager.ax2.relim()
            self.plot_manager.ax2.autoscale_view()
            self.plot_manager.redraw()

    def toggle_legend(self):
        """Toggle the visibility of the plot legend."""
        if self.plot_manager.ax1.get_legend():
            self.plot_manager.ax1.get_legend().set_visible(not self.plot_manager.ax1.get_legend().get_visible())
        if self.plot_manager.ax2.get_legend():
            self.plot_manager.ax2.get_legend().set_visible(not self.plot_manager.ax2.get_legend().get_visible())
        self.plot_manager.redraw()

    def detect_peaks(self):
        """Detect peaks in the selected signal."""
        self.run_detection('Peak')
    
    def detect_valleys(self):
        """Detect valleys in the selected signal."""
        self.run_detection('Valley')
    
    def clear_peaks(self):
        """Clear all peak detections."""
        try:
            # Clear primary data peak information
            if self.primary_data:
                self.primary_data['peaks'] = {'indices': np.array([]), 'times': np.array([]), 'heights': np.array([])}
                self.primary_data['peak_metrics'] = None
            
            # Clear secondary data peak information  
            if self.secondary_data:
                self.secondary_data['peaks'] = {'indices': np.array([]), 'times': np.array([]), 'heights': np.array([])}
                self.secondary_data['peak_metrics'] = None
            
            # Update results window
            result_text = f"Peak Detection Results\n"
            result_text += f"=" * 30 + "\n"
            result_text += f"All peak detections have been cleared.\n"
            result_text += f"Run peak detection to find new peaks.\n"
            result_text += f"Peak data is no longer available for PSTH analysis.\n\n"
            self.update_peak_results(result_text)
            
            # Update all dependent displays
            self.update_peak_display()
            self.populate_metrics_table()
            self.update_status("Peak detections cleared - ready for new detection")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear peaks: {str(e)}")
            logging.error(f"Error in clear_peaks: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def clear_valleys(self):
        """Clear all valley detections."""
        try:
            # Clear primary data valley information
            if self.primary_data:
                self.primary_data['valleys'] = {'indices': np.array([]), 'times': np.array([]), 'depths': np.array([])}
                self.primary_data['valley_metrics'] = None
            
            # Clear secondary data valley information  
            if self.secondary_data:
                self.secondary_data['valleys'] = {'indices': np.array([]), 'times': np.array([]), 'depths': np.array([])}
                self.secondary_data['valley_metrics'] = None
            
            # Update results window
            result_text = f"Valley Detection Results\n"
            result_text += f"=" * 30 + "\n"
            result_text += f"All valley detections have been cleared.\n"
            result_text += f"Run valley detection to find new valleys.\n"
            result_text += f"Valley data is no longer available for PSTH analysis.\n\n"
            self.update_peak_results(result_text)
            
            # Update all dependent displays
            self.update_peak_display()
            self.populate_metrics_table()
            self.update_status("Valley detections cleared - ready for new detection")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear valleys: {str(e)}")
            logging.error(f"Error in clear_valleys: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_plot_visibility(self):
        """Update the visibility of different signal types."""
        visibility = {
            'primary_dff': self.primary_dff_var.get(),
            'primary_raw': self.primary_raw_var.get(),
            'primary_control': self.primary_control_var.get(),
            'primary_ttl1': self.primary_ttl1_var.get(),
            'primary_ttl2': self.primary_ttl2_var.get(),
            'secondary_dff': self.secondary_dff_var.get(),
            'secondary_raw': self.secondary_raw_var.get(),
            'secondary_control': self.secondary_control_var.get(),
            'secondary_ttl1': self.secondary_ttl1_var.get(),
            'secondary_ttl2': self.secondary_ttl2_var.get()
        }
        self.plot_manager.update_visibility(**visibility)

    def update_status(self, message):
        """Update the status bar with a message."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    # AI Assistant menu handlers
    def share_data_with_ai(self):
        """Share current data context with AI assistant."""
        if hasattr(self, 'ai_assistant'):
            self.ai_assistant.share_data_context()
    
    def show_ai_settings(self):
        """Show AI assistant settings."""
        if hasattr(self, 'ai_assistant'):
            self.ai_assistant.show_api_settings()
    
    def clear_ai_chat(self):
        """Clear AI chat history."""
        if hasattr(self, 'ai_assistant'):
            self.ai_assistant.clear_chat()
    
    def show_ai_help(self):
        """Show AI assistant help."""
        help_text = """
🤖 AI Scientific Assistant Help

The AI Assistant can help you with:
• Analyzing signal patterns and correlations
• Testing statistical hypotheses
• Generating custom plots and visualizations
• Discovering biomarkers and insights
• Interpreting experimental results

How to use:
1. Set up your Claude API key in AI Assistant > API Settings
2. Load your photometry data
3. Share data context with the AI
4. Ask questions or request analysis in natural language

Example questions:
• "What's the correlation between raw signals?"
• "Are there periodic patterns in my data?"
• "Test if peak amplitudes are significantly different"
• "Generate a plot showing signal stability over time"

The AI has full access to your current data state and can provide contextual analysis and insights.
        """
        messagebox.showinfo("AI Assistant Help", help_text.strip())
    
    # GPU Performance monitoring methods
    def show_gpu_status(self):
        """Show GPU acceleration status."""
        try:
            from gpu_processing import gpu_accel
            device_info = gpu_accel.get_device_info()
            
            status_text = f"""
🚀 GPU Acceleration Status

Status: {device_info.get('status', 'Unknown')}
Devices: {device_info.get('devices', 0)}
Memory Total: {device_info.get('memory_total_gb', 0):.1f} GB
Memory Free: {device_info.get('memory_free_gb', 0):.1f} GB
Memory Used: {device_info.get('memory_used_percent', 0):.1f}%

Libraries:
• NumPy: Available
• SciPy: Available
• Numba: {'Available' if gpu_accel.cuda_available else 'Not Available'}
• CuPy: {'Available' if gpu_accel.gpu_available else 'Not Available'}

Performance Tips:
• Data > 10MB automatically uses GPU
• Use GPU for large datasets
• Monitor memory usage for optimal performance
            """
            
            messagebox.showinfo("GPU Status", status_text.strip())
            
        except Exception as e:
            messagebox.showerror("GPU Status", f"Error getting GPU status: {str(e)}")
    
    def benchmark_gpu(self):
        """Run GPU benchmark."""
        try:
            from gpu_processing import benchmark_gpu_performance
            
            # Show progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("GPU Benchmark")
            progress_dialog.geometry("300x100")
            progress_dialog.resizable(False, False)
            
            ttk.Label(progress_dialog, text="Running GPU benchmark...").pack(pady=20)
            progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
            progress_bar.pack(fill='x', padx=20, pady=10)
            progress_bar.start()
            
            # Run benchmark in thread
            def run_benchmark():
                try:
                    results = benchmark_gpu_performance()
                    
                    # Format results
                    result_text = "🏁 GPU Benchmark Results\n\n"
                    result_text += f"GPU Available: {results['gpu_available']}\n\n"
                    
                    for test_name, result in results['tests'].items():
                        speedup = result['speedup']
                        result_text += f"{test_name}:\n"
                        result_text += f"  CPU: {result['cpu_time']:.4f}s\n"
                        result_text += f"  GPU: {result['gpu_time']:.4f}s\n"
                        result_text += f"  Speedup: {speedup:.2f}x\n\n"
                    
                    # Show results in main thread
                    self.root.after(0, lambda: [
                        progress_dialog.destroy(),
                        messagebox.showinfo("GPU Benchmark", result_text)
                    ])
                    
                except Exception as e:
                    self.root.after(0, lambda: [
                        progress_dialog.destroy(),
                        messagebox.showerror("GPU Benchmark", f"Benchmark failed: {str(e)}")
                    ])
            
            threading.Thread(target=run_benchmark, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("GPU Benchmark", f"Error starting benchmark: {str(e)}")
    
    def show_memory_usage(self):
        """Show memory usage information."""
        try:
            import psutil
            from gpu_processing import gpu_accel
            
            # System memory
            system_memory = psutil.virtual_memory()
            
            # GPU memory
            gpu_info = gpu_accel.get_device_info()
            
            memory_text = f"""
💾 Memory Usage

System Memory:
• Total: {system_memory.total / 1024**3:.1f} GB
• Available: {system_memory.available / 1024**3:.1f} GB
• Used: {system_memory.percent:.1f}%

GPU Memory:
• Total: {gpu_info.get('memory_total_gb', 0):.1f} GB
• Free: {gpu_info.get('memory_free_gb', 0):.1f} GB
• Used: {gpu_info.get('memory_used_percent', 0):.1f}%

Data Size Guidelines:
• < 10MB: CPU processing
• > 10MB: GPU processing
• > 1GB: Consider downsampling
            """
            
            messagebox.showinfo("Memory Usage", memory_text.strip())
            
        except Exception as e:
            messagebox.showerror("Memory Usage", f"Error getting memory info: {str(e)}")

    def bind_visibility_variables(self):
        """Bind visibility variables to the control panel."""
        if hasattr(self, 'control_panel'):
            self.primary_dff_var = self.control_panel.primary_dff_var
            self.primary_raw_var = self.control_panel.primary_raw_var
            self.primary_control_var = self.control_panel.primary_control_var
            self.primary_ttl1_var = self.control_panel.primary_ttl1_var
            self.primary_ttl2_var = self.control_panel.primary_ttl2_var
            self.secondary_dff_var = self.control_panel.secondary_dff_var
            self.secondary_raw_var = self.control_panel.secondary_raw_var
            self.secondary_control_var = self.control_panel.secondary_control_var
            self.secondary_ttl1_var = self.control_panel.secondary_ttl1_var
            self.secondary_ttl2_var = self.control_panel.secondary_ttl2_var

    def _init_metrics_tables(self):
        """初始化并布局峰值和谷值metrics表格。"""
        # 创建表格Frame
        metrics_frame = ttk.Frame(self.control_frame)
        metrics_frame.pack(fill='both', expand=True, padx=5, pady=5)
        # 峰值表
        self.peak_metrics_tree = ttk.Treeview(metrics_frame, columns=("#", "Time", "Height", "FWHM", "Area", "Rise", "Decay"), show='headings', height=6)
        for col in ("#", "Time", "Height", "FWHM", "Area", "Rise", "Decay"):
            self.peak_metrics_tree.heading(col, text=col)
            self.peak_metrics_tree.column(col, width=70, anchor='center')
        self.peak_metrics_tree.pack(fill='x', pady=2)
        # 谷值表
        self.valley_metrics_tree = ttk.Treeview(metrics_frame, columns=("#", "Time", "Depth", "FWHM", "Area Above"), show='headings', height=6)
        for col in ("#", "Time", "Depth", "FWHM", "Area Above"):
            self.valley_metrics_tree.heading(col, text=col)
            self.valley_metrics_tree.column(col, width=70, anchor='center')
        self.valley_metrics_tree.pack(fill='x', pady=2)

    def show_all_signals(self):
        """Show all signals on the plot (not just dF/F)."""
        self.plot_manager.update_plots(self.primary_data, self.secondary_data, plot_only_dff=False)
        self.update_status("All signals displayed.")
    
    def show_filtered_raw_signals(self):
        """Show filtered raw signals to visualize filter effects."""
        if not self.primary_data and not self.secondary_data:
            messagebox.showinfo("Info", "No data loaded. Please load data first.")
            return
        
        # Show all signals including filtered raw signals
        self.plot_manager.update_plots(self.primary_data, self.secondary_data, plot_only_dff=False)
        self.update_status("Filtered raw signals displayed. Use 'Apply Signal Visibility' to toggle signals.")
        
    def generate_psth(self):
        """Generate PSTH (Peri-Stimulus Time Histogram) around detected events."""
        try:
            # Get parameters
            event_type = self.psth_event_type.get()
            signal_source = self.psth_signal_source.get()
            pre_time = self.psth_pre_time.get()
            post_time = self.psth_post_time.get()
            bin_size = self.psth_bin_size.get()
            
            # Validate parameters
            if pre_time <= 0 or post_time <= 0 or bin_size <= 0:
                messagebox.showerror("Error", "Time windows and bin size must be positive values.")
                return
            
            # Get the appropriate data
            data = self.primary_data if signal_source == 'Primary' else self.secondary_data
            if not data or data.get('dff') is None:
                messagebox.showinfo("Info", f"No processed {signal_source.lower()} data available.\nLoad data and apply filters first.")
                return
            
            # Get event times with comprehensive checking
            event_times = None
            if event_type == 'Peaks':
                # Check if peaks data exists and is valid
                if not data.get('peaks'):
                    messagebox.showinfo("Info", f"No peak data found in {signal_source.lower()} data.\nPlease run peak detection first.")
                    return
                
                peaks_data = data['peaks']
                peaks_times = peaks_data.get('times')
                if peaks_times is None or (hasattr(peaks_times, '__len__') and len(peaks_times) == 0):
                    messagebox.showinfo("Info", f"No peaks detected in {signal_source.lower()} data.\nPlease run peak detection first or adjust detection parameters.")
                    return
                
                event_times = peaks_data['times']
                
            else:  # Valleys
                # Check if valleys data exists and is valid
                if not data.get('valleys'):
                    messagebox.showinfo("Info", f"No valley data found in {signal_source.lower()} data.\nPlease run valley detection first.")
                    return
                
                valleys_data = data['valleys']
                valleys_times = valleys_data.get('times')
                if valleys_times is None or (hasattr(valleys_times, '__len__') and len(valleys_times) == 0):
                    messagebox.showinfo("Info", f"No valleys detected in {signal_source.lower()} data.\nPlease run valley detection first or adjust detection parameters.")
                    return
                
                event_times = valleys_data['times']
            
            # Final validation of event times
            if event_times is None or (hasattr(event_times, '__len__') and len(event_times) == 0):
                messagebox.showinfo("Info", f"No valid {event_type.lower()} times found.\nPlease run {event_type.lower()} detection first.")
                return
            
            # Convert to numpy array if needed
            if not isinstance(event_times, np.ndarray):
                event_times = np.array(event_times)
            
            # Get signal data
            time = data['time']
            signal = data['dff']
            
            # Validate signal data
            if (time is None or signal is None or 
                (hasattr(time, '__len__') and len(time) == 0) or 
                (hasattr(signal, '__len__') and len(signal) == 0)):
                messagebox.showerror("Error", f"Invalid {signal_source.lower()} signal data.\nPlease reload and reprocess the data.")
                return
            
            # Check that event times are within signal time range
            time_min, time_max = np.min(time), np.max(time)
            valid_events = (event_times >= time_min + pre_time) & (event_times <= time_max - post_time)
            
            if not np.any(valid_events):
                messagebox.showinfo("Info", f"No {event_type.lower()} are within the valid time range.\nPre-time: {pre_time:.1f}s, Post-time: {post_time:.1f}s\nSignal duration: {time_max - time_min:.1f}s")
                return
            
            # Filter to valid events
            event_times = event_times[valid_events]
            
            self.update_status(f"Generating PSTH for {len(event_times)} {event_type.lower()}...")
            print(f"PSTH: Using {len(event_times)} {event_type.lower()} from {signal_source.lower()} data")
            
            # Calculate PSTH
            time_bins = np.arange(-pre_time, post_time + bin_size, bin_size)
            psth_matrix = []
            valid_events = 0
            
            for event_time in event_times:
                # Find indices for this event window
                start_idx = np.searchsorted(time, event_time - pre_time)
                end_idx = np.searchsorted(time, event_time + post_time)
                
                if start_idx < 0 or end_idx >= len(time):
                    continue  # Skip events too close to edges
                
                # Extract signal for this event
                event_time_rel = time[start_idx:end_idx] - event_time
                event_signal = signal[start_idx:end_idx]
                
                # Interpolate to common time grid
                if len(event_time_rel) > 1:
                    interp_signal = np.interp(time_bins[:-1] + bin_size/2, event_time_rel, event_signal)
                    psth_matrix.append(interp_signal)
                    valid_events += 1
            
            if valid_events == 0:
                messagebox.showinfo("Info", "No valid events found for PSTH analysis.")
                return
            
            # Convert to array and calculate statistics
            psth_matrix = np.array(psth_matrix)
            psth_mean = np.mean(psth_matrix, axis=0)
            psth_sem = np.std(psth_matrix, axis=0) / np.sqrt(valid_events)
            
            # Plot PSTH
            self.control_panel.psth_ax.clear()
            time_centers = time_bins[:-1] + bin_size/2
            
            # Plot mean with error bars
            self.control_panel.psth_ax.plot(time_centers, psth_mean, 'b-', linewidth=2, label=f'Mean (n={valid_events})')
            self.control_panel.psth_ax.fill_between(time_centers, 
                                                   psth_mean - psth_sem, 
                                                   psth_mean + psth_sem, 
                                                   alpha=0.3, color='blue', label='SEM')
            
            # Add event marker
            self.control_panel.psth_ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, label=f'{event_type[:-1]} Time')
            
            # Formatting
            self.control_panel.psth_ax.set_xlabel('Time relative to event (s)')
            self.control_panel.psth_ax.set_ylabel('ΔF/F (%)')
            self.control_panel.psth_ax.set_title(f'PSTH: {signal_source} Signal around {event_type}')
            self.control_panel.psth_ax.legend()
            self.control_panel.psth_ax.grid(True, alpha=0.3)
            
            # Update canvas
            self.control_panel.psth_fig.tight_layout()
            self.control_panel.psth_canvas.draw()
            
            # Update results window
            result_text = f"PSTH Analysis Results\n"
            result_text += f"=" * 30 + "\n"
            result_text += f"Signal: {signal_source}\n"
            result_text += f"Event type: {event_type}\n"
            result_text += f"Valid events: {valid_events}\n"
            result_text += f"Pre-event window: {pre_time:.1f}s\n"
            result_text += f"Post-event window: {post_time:.1f}s\n"
            result_text += f"Bin size: {bin_size:.3f}s\n"
            result_text += f"Total bins: {len(time_bins)-1}\n"
            result_text += f"Mean baseline: {np.mean(psth_mean[:int(pre_time/bin_size)]):.3f}\n"
            result_text += f"Mean peak response: {np.max(psth_mean):.3f}\n"
            result_text += f"Peak response time: {time_centers[np.argmax(psth_mean)]:.2f}s\n"
            result_text += f"Response duration: {post_time:.1f}s\n\n"
            
            self.update_psth_results(result_text)
            
            self.update_status(f"PSTH generated: {valid_events} {event_type.lower()} analyzed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PSTH: {str(e)}")
    
    def get_signal_data(self, signal_name):
        """Get signal data by name."""
        if signal_name == 'Primary ΔF/F' and self.primary_data and 'dff' in self.primary_data:
            return self.primary_data['time'], self.primary_data['dff']
        elif signal_name == 'Primary Raw' and self.primary_data and 'raw' in self.primary_data:
            return self.primary_data['time'], self.primary_data['raw']
        elif signal_name == 'Secondary ΔF/F' and self.secondary_data and 'dff' in self.secondary_data:
            return self.secondary_data['time'], self.secondary_data['dff']
        elif signal_name == 'Secondary Raw' and self.secondary_data and 'raw' in self.secondary_data:
            return self.secondary_data['time'], self.secondary_data['raw']
        else:
            return None, None
    
    def calculate_pearson_correlation(self):
        """Calculate Pearson correlation between two signals."""
        try:
            # Get selected signals
            signal1_name = self.corr_signal1.get()
            signal2_name = self.corr_signal2.get()
            
            time1, signal1 = self.get_signal_data(signal1_name)
            time2, signal2 = self.get_signal_data(signal2_name)
            
            if time1 is None or time2 is None:
                messagebox.showerror("Error", "Selected signals not available")
                return
            
            # Interpolate to common time grid
            common_time = np.linspace(max(time1[0], time2[0]), min(time1[-1], time2[-1]), 
                                    min(len(time1), len(time2)))
            
            signal1_interp = np.interp(common_time, time1, signal1)
            signal2_interp = np.interp(common_time, time2, signal2)
            
            # Calculate correlation
            correlation = np.corrcoef(signal1_interp, signal2_interp)[0, 1]
            
            # Display results
            result_text = f"Pearson Correlation Analysis\n"
            result_text += f"Signal 1: {signal1_name}\n"
            result_text += f"Signal 2: {signal2_name}\n"
            result_text += f"Correlation coefficient: {correlation:.4f}\n"
            result_text += f"Data points: {len(common_time)}\n"
            result_text += f"Time range: {common_time[0]:.1f} - {common_time[-1]:.1f} s\n\n"
            
            self.update_correlation_results(result_text)
            
            # Plot signals
            self.control_panel.corr_ax.clear()
            self.control_panel.corr_ax.plot(common_time, signal1_interp, 'b-', label=signal1_name, alpha=0.7)
            self.control_panel.corr_ax.plot(common_time, signal2_interp, 'r-', label=signal2_name, alpha=0.7)
            self.control_panel.corr_ax.set_xlabel('Time (s)')
            self.control_panel.corr_ax.set_ylabel('Signal')
            self.control_panel.corr_ax.set_title(f'Pearson Correlation: r = {correlation:.4f}')
            self.control_panel.corr_ax.legend()
            self.control_panel.corr_ax.grid(True, alpha=0.3)
            self.control_panel.corr_fig.tight_layout()
            self.control_panel.corr_canvas.draw()
            
            self.update_status(f"Pearson correlation calculated: r = {correlation:.4f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate Pearson correlation: {str(e)}")
    
    def calculate_cross_correlation(self):
        """Calculate cross-correlation between two signals."""
        try:
            # Get selected signals
            signal1_name = self.corr_signal1.get()
            signal2_name = self.corr_signal2.get()
            
            time1, signal1 = self.get_signal_data(signal1_name)
            time2, signal2 = self.get_signal_data(signal2_name)
            
            if time1 is None or time2 is None:
                messagebox.showerror("Error", "Selected signals not available")
                return
            
            # Interpolate to common time grid
            common_time = np.linspace(max(time1[0], time2[0]), min(time1[-1], time2[-1]), 
                                    min(len(time1), len(time2)))
            
            signal1_interp = np.interp(common_time, time1, signal1)
            signal2_interp = np.interp(common_time, time2, signal2)
            
            # Calculate cross-correlation
            cross_corr = np.correlate(signal1_interp, signal2_interp, mode='full')
            cross_corr = cross_corr / (np.linalg.norm(signal1_interp) * np.linalg.norm(signal2_interp))
            
            # Create lag array
            dt = common_time[1] - common_time[0]
            max_lag = self.corr_max_lag.get()
            max_lag_samples = int(max_lag / dt)
            
            center = len(cross_corr) // 2
            lag_start = max(0, center - max_lag_samples)
            lag_end = min(len(cross_corr), center + max_lag_samples + 1)
            
            cross_corr_trimmed = cross_corr[lag_start:lag_end]
            lags = np.arange(lag_start - center, lag_end - center) * dt
            
            # Find peak correlation
            peak_idx = np.argmax(np.abs(cross_corr_trimmed))
            peak_lag = lags[peak_idx]
            peak_corr = cross_corr_trimmed[peak_idx]
            
            # Display results
            result_text = f"Cross-Correlation Analysis\n"
            result_text += f"Signal 1: {signal1_name}\n"
            result_text += f"Signal 2: {signal2_name}\n"
            result_text += f"Peak correlation: {peak_corr:.4f}\n"
            result_text += f"Optimal lag: {peak_lag:.2f} s\n"
            result_text += f"Max lag analyzed: ±{max_lag:.1f} s\n\n"
            
            self.update_correlation_results(result_text)
            
            # Plot cross-correlation
            self.control_panel.corr_ax.clear()
            self.control_panel.corr_ax.plot(lags, cross_corr_trimmed, 'b-', linewidth=2)
            self.control_panel.corr_ax.axvline(x=peak_lag, color='red', linestyle='--', alpha=0.7, 
                                             label=f'Peak: {peak_corr:.4f} at {peak_lag:.2f}s')
            self.control_panel.corr_ax.set_xlabel('Lag (s)')
            self.control_panel.corr_ax.set_ylabel('Cross-correlation')
            self.control_panel.corr_ax.set_title(f'Cross-Correlation: {signal1_name} vs {signal2_name}')
            self.control_panel.corr_ax.legend()
            self.control_panel.corr_ax.grid(True, alpha=0.3)
            self.control_panel.corr_fig.tight_layout()
            self.control_panel.corr_canvas.draw()
            
            self.update_status(f"Cross-correlation calculated: peak = {peak_corr:.4f} at {peak_lag:.2f}s")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate cross-correlation: {str(e)}")
    
    def calculate_granger_causality(self):
        """Calculate Granger causality between two signals."""
        try:
            # Get selected signals
            signal1_name = self.corr_signal1.get()
            signal2_name = self.corr_signal2.get()
            
            time1, signal1 = self.get_signal_data(signal1_name)
            time2, signal2 = self.get_signal_data(signal2_name)
            
            if time1 is None or time2 is None:
                messagebox.showerror("Error", "Selected signals not available")
                return
            
            # Interpolate to common time grid
            common_time = np.linspace(max(time1[0], time2[0]), min(time1[-1], time2[-1]), 
                                    min(len(time1), len(time2)))
            
            signal1_interp = np.interp(common_time, time1, signal1)
            signal2_interp = np.interp(common_time, time2, signal2)
            
            # Simple Granger causality test using linear regression
            # This is a simplified version - for full analysis, use statsmodels
            
            # Create lagged variables (using 5 lags as default)
            lags = 5
            n = len(signal1_interp) - lags
            
            # Test if signal1 Granger-causes signal2
            X1 = np.zeros((n, lags * 2))  # Both signals as predictors
            X2 = np.zeros((n, lags))      # Only signal2 as predictor
            y = signal2_interp[lags:]     # Future values of signal2
            
            for i in range(lags):
                X1[:, i] = signal1_interp[lags-1-i:lags-1-i+n]  # Lagged signal1
                X1[:, lags+i] = signal2_interp[lags-1-i:lags-1-i+n]  # Lagged signal2
                X2[:, i] = signal2_interp[lags-1-i:lags-1-i+n]  # Lagged signal2
            
            # Fit models
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import mean_squared_error
            
            model1 = LinearRegression().fit(X1, y)  # Full model
            model2 = LinearRegression().fit(X2, y)  # Restricted model
            
            # Calculate F-statistic
            rss1 = mean_squared_error(y, model1.predict(X1)) * len(y)
            rss2 = mean_squared_error(y, model2.predict(X2)) * len(y)
            
            f_stat = ((rss2 - rss1) / lags) / (rss1 / (len(y) - 2*lags - 1))
            
            # Test if signal2 Granger-causes signal1
            y_rev = signal1_interp[lags:]
            X1_rev = np.zeros((n, lags * 2))
            X2_rev = np.zeros((n, lags))
            
            for i in range(lags):
                X1_rev[:, i] = signal2_interp[lags-1-i:lags-1-i+n]  # Lagged signal2
                X1_rev[:, lags+i] = signal1_interp[lags-1-i:lags-1-i+n]  # Lagged signal1
                X2_rev[:, i] = signal1_interp[lags-1-i:lags-1-i+n]  # Lagged signal1
            
            model1_rev = LinearRegression().fit(X1_rev, y_rev)
            model2_rev = LinearRegression().fit(X2_rev, y_rev)
            
            rss1_rev = mean_squared_error(y_rev, model1_rev.predict(X1_rev)) * len(y_rev)
            rss2_rev = mean_squared_error(y_rev, model2_rev.predict(X2_rev)) * len(y_rev)
            
            f_stat_rev = ((rss2_rev - rss1_rev) / lags) / (rss1_rev / (len(y_rev) - 2*lags - 1))
            
            # Display results
            result_text = f"Granger Causality Analysis\n"
            result_text += f"Signal 1: {signal1_name}\n"
            result_text += f"Signal 2: {signal2_name}\n"
            result_text += f"Lags used: {lags}\n"
            result_text += f"Data points: {n}\n\n"
            result_text += f"H0: {signal1_name} does not Granger-cause {signal2_name}\n"
            result_text += f"F-statistic: {f_stat:.4f}\n"
            result_text += f"H0: {signal2_name} does not Granger-cause {signal1_name}\n"
            result_text += f"F-statistic: {f_stat_rev:.4f}\n\n"
            result_text += f"Note: Higher F-statistic suggests stronger causality\n"
            result_text += f"Use proper statistical test for p-values\n\n"
            
            self.update_correlation_results(result_text)
            
            # Plot F-statistics
            self.control_panel.corr_ax.clear()
            categories = [f'{signal1_name}\n→ {signal2_name}', f'{signal2_name}\n→ {signal1_name}']
            f_stats = [f_stat, f_stat_rev]
            
            bars = self.control_panel.corr_ax.bar(categories, f_stats, color=['blue', 'red'], alpha=0.7)
            self.control_panel.corr_ax.set_ylabel('F-statistic')
            self.control_panel.corr_ax.set_title('Granger Causality F-statistics')
            self.control_panel.corr_ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, f_val in zip(bars, f_stats):
                height = bar.get_height()
                self.control_panel.corr_ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                              f'{f_val:.3f}', ha='center', va='bottom')
            
            self.control_panel.corr_fig.tight_layout()
            self.control_panel.corr_canvas.draw()
            
            self.update_status(f"Granger causality calculated: F1→2 = {f_stat:.3f}, F2→1 = {f_stat_rev:.3f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate Granger causality: {str(e)}")
    
    def calculate_rolling_correlation(self):
        """Calculate rolling correlation between two signals."""
        try:
            # Get selected signals
            signal1_name = self.corr_signal1.get()
            signal2_name = self.corr_signal2.get()
            
            time1, signal1 = self.get_signal_data(signal1_name)
            time2, signal2 = self.get_signal_data(signal2_name)
            
            if time1 is None or time2 is None:
                messagebox.showerror("Error", "Selected signals not available")
                return
            
            # Interpolate to common time grid
            common_time = np.linspace(max(time1[0], time2[0]), min(time1[-1], time2[-1]), 
                                    min(len(time1), len(time2)))
            
            signal1_interp = np.interp(common_time, time1, signal1)
            signal2_interp = np.interp(common_time, time2, signal2)
            
            # Calculate rolling correlation
            window_size = self.corr_window.get()
            dt = common_time[1] - common_time[0]
            window_samples = int(window_size / dt)
            
            rolling_corr = []
            rolling_time = []
            
            for i in range(window_samples//2, len(signal1_interp) - window_samples//2):
                start_idx = i - window_samples//2
                end_idx = i + window_samples//2
                
                corr = np.corrcoef(signal1_interp[start_idx:end_idx], 
                                 signal2_interp[start_idx:end_idx])[0, 1]
                rolling_corr.append(corr)
                rolling_time.append(common_time[i])
            
            rolling_corr = np.array(rolling_corr)
            rolling_time = np.array(rolling_time)
            
            # Calculate statistics
            mean_corr = np.nanmean(rolling_corr)
            std_corr = np.nanstd(rolling_corr)
            max_corr = np.nanmax(rolling_corr)
            min_corr = np.nanmin(rolling_corr)
            
            # Display results
            result_text = f"Rolling Correlation Analysis\n"
            result_text += f"Signal 1: {signal1_name}\n"
            result_text += f"Signal 2: {signal2_name}\n"
            result_text += f"Window size: {window_size:.1f} s\n"
            result_text += f"Data points: {len(rolling_corr)}\n\n"
            result_text += f"Mean correlation: {mean_corr:.4f}\n"
            result_text += f"Std deviation: {std_corr:.4f}\n"
            result_text += f"Max correlation: {max_corr:.4f}\n"
            result_text += f"Min correlation: {min_corr:.4f}\n\n"
            
            self.update_correlation_results(result_text)
            
            # Plot rolling correlation
            self.control_panel.corr_ax.clear()
            self.control_panel.corr_ax.plot(rolling_time, rolling_corr, 'b-', linewidth=2, 
                                          label=f'Rolling correlation (window: {window_size:.1f}s)')
            self.control_panel.corr_ax.axhline(y=mean_corr, color='red', linestyle='--', alpha=0.7, 
                                             label=f'Mean: {mean_corr:.4f}')
            self.control_panel.corr_ax.fill_between(rolling_time, mean_corr - std_corr, mean_corr + std_corr, 
                                                  alpha=0.2, color='red', label='±1 SD')
            self.control_panel.corr_ax.set_xlabel('Time (s)')
            self.control_panel.corr_ax.set_ylabel('Correlation Coefficient')
            self.control_panel.corr_ax.set_title(f'Rolling Correlation: {signal1_name} vs {signal2_name}')
            self.control_panel.corr_ax.legend()
            self.control_panel.corr_ax.grid(True, alpha=0.3)
            self.control_panel.corr_fig.tight_layout()
            self.control_panel.corr_canvas.draw()
            
            self.update_status(f"Rolling correlation calculated: mean = {mean_corr:.4f} ± {std_corr:.4f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate rolling correlation: {str(e)}")
    
    def display_correlation_results(self, text):
        """Display correlation results in the text area."""
        # Use the new update function
        self.update_correlation_results(text)
        
        # Update plot view for AI assistant
        if hasattr(self, 'ai_assistant') and self.ai_assistant:
            self.ai_assistant.update_claude_with_current_view()
    
    def update_peak_results(self, result_text):
        """Update the peak-valley analysis results window."""
        if hasattr(self.control_panel, 'peak_results'):
            self.control_panel.peak_results.config(state='normal')
            self.control_panel.peak_results.delete(1.0, tk.END)
            self.control_panel.peak_results.insert(tk.END, result_text)
            self.control_panel.peak_results.config(state='disabled')
            
            # Send to AI assistant if available
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                self.ai_assistant.add_system_message(f"Peak-Valley Analysis Results:\n{result_text}")
    
    def update_psth_results(self, result_text):
        """Update the PSTH analysis results window."""
        if hasattr(self.control_panel, 'psth_results'):
            self.control_panel.psth_results.config(state='normal')
            self.control_panel.psth_results.delete(1.0, tk.END)
            self.control_panel.psth_results.insert(tk.END, result_text)
            self.control_panel.psth_results.config(state='disabled')
            
            # Send to AI assistant if available
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                self.ai_assistant.add_system_message(f"PSTH Analysis Results:\n{result_text}")
    
    def update_correlation_results(self, result_text):
        """Update the correlation analysis results window."""
        if hasattr(self.control_panel, 'correlation_results'):
            self.control_panel.correlation_results.delete(1.0, tk.END)
            self.control_panel.correlation_results.insert(tk.END, result_text)
            
            # Send to AI assistant if available
            if hasattr(self, 'ai_assistant') and self.ai_assistant:
                self.ai_assistant.add_system_message(f"Correlation Analysis Results:\n{result_text}")