# file: gui/control_panel.py

import tkinter as tk
from tkinter import ttk
import logging
import os

class ControlPanel:
    """A class to manage the control panel of the application."""
    
    FONT_PARAMS = {
        'title': {'size': 16, 'weight': 'bold'},
        'label': {'size': 12},
        'button': {'size': 12},
        'slider': {'size': 11},
        'tab': {'size': 13}
    }

    def __init__(self, parent, master):
        """Initialize the control panel."""
        self.parent = parent
        self.master = master
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.analysis_tab = self.create_preprocess_tab(self.notebook)
        self.peak_tab = self.create_peak_tab(self.notebook)
        
        # Create PSTH tab
        self.psth_tab = self.create_psth_tab(self.notebook)
        
        # Create correlation analysis tab
        self.correlation_tab = self.create_correlation_tab(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.analysis_tab, text='PreProcess')
        self.notebook.add(self.peak_tab, text='Peak-Valley')
        self.notebook.add(self.psth_tab, text='PSTH')
        self.notebook.add(self.correlation_tab, text='Correlation')
        
        # Configure style
        self.configure_style()

    def configure_style(self):
        """Configure the ttk style for the control panel."""
        style = ttk.Style()
        style.configure('TNotebook.Tab', font=('TkDefaultFont', self.FONT_PARAMS['tab']['size']))
        style.configure('TLabel', font=('TkDefaultFont', self.FONT_PARAMS['label']['size']))
        style.configure('TButton', font=('TkDefaultFont', self.FONT_PARAMS['button']['size']))
        style.configure('TEntry', font=('TkDefaultFont', self.FONT_PARAMS['label']['size']))
        style.configure('TCheckbutton', font=('TkDefaultFont', self.FONT_PARAMS['label']['size']))
        style.configure('TCombobox', font=('TkDefaultFont', self.FONT_PARAMS['label']['size']))

    def create_preprocess_tab(self, parent):
        """Create the preprocess tab with all controls."""
        frame = ttk.Frame(parent, padding=10)
        
        # File name display at the top
        file_frame = ttk.LabelFrame(frame, text="Loaded Files", padding=5)
        file_frame.pack(fill='x', pady=(0, 10))
        self.create_file_display(file_frame)
        
        # Signal visibility controls
        visibility_frame = self.create_signal_visibility_frame(frame)
        visibility_frame.pack(fill='x', pady=(0, 10))
        
        # Add button to enable full plotting
        full_plot_btn = ttk.Button(frame, text="Show All Signals", command=self.master.show_all_signals)
        full_plot_btn.pack(fill='x', pady=(0, 10))
        
        # Filter parameters
        filter_frame = ttk.LabelFrame(frame, text="Filter Parameters", padding=5)
        filter_frame.pack(fill='x', pady=(0, 10))
        # Create filter controls
        self.create_filter_controls(filter_frame)
        
        # Add denoising controls
        self.create_denoising_controls(frame)
        
        return frame

    def create_analysis_tab(self, parent):
        """Create the analysis tab with all controls."""
        frame = ttk.Frame(parent, padding=10)
        
        # File name display at the top
        file_frame = ttk.LabelFrame(frame, text="Loaded Files", padding=5)
        file_frame.pack(fill='x', pady=(0, 10))
        self.create_file_display(file_frame)
        
        # Signal visibility controls
        visibility_frame = self.create_signal_visibility_frame(frame)
        visibility_frame.pack(fill='x', pady=(0, 10))
        
        # Add button to enable full plotting
        full_plot_btn = ttk.Button(frame, text="Show All Signals", command=self.master.show_all_signals)
        full_plot_btn.pack(fill='x', pady=(0, 10))
        
        # Filter parameters
        filter_frame = ttk.LabelFrame(frame, text="Filter Parameters", padding=5)
        filter_frame.pack(fill='x', pady=(0, 10))
        # Create filter controls
        self.create_filter_controls(filter_frame)
        
        return frame

    def create_filter_controls(self, parent):
        """Create filter control widgets."""
        # 滤波类型
        ttk.Label(parent, text='Filter Type:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.master.filter_type = getattr(self.master, 'filter_type', tk.StringVar(value='Bandpass'))
        ttk.Combobox(parent, textvariable=self.master.filter_type, values=['Lowpass', 'Highpass', 'Bandpass', 'Bandstop'], state='readonly', width=10).grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        # 阶数
        ttk.Label(parent, text='Order:').grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.master.filter_order = getattr(self.master, 'filter_order', tk.IntVar(value=2))
        ttk.Entry(parent, textvariable=self.master.filter_order, width=6).grid(row=0, column=3, sticky='ew', padx=5, pady=2)
        # 零相位
        ttk.Label(parent, text='Zero-phase:').grid(row=0, column=4, sticky='w', padx=5, pady=2)
        self.master.zero_phase = getattr(self.master, 'zero_phase', tk.BooleanVar(value=True))
        ttk.Checkbutton(parent, variable=self.master.zero_phase).grid(row=0, column=5, sticky='w', padx=5, pady=2)
        # 低通截止频率
        ttk.Label(parent, text='Lowpass (Hz):').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.master.low_cutoff = getattr(self.master, 'low_cutoff', tk.DoubleVar(value=0.001))
        lowpass_scale = tk.Scale(parent, from_=0.0001, to=0.01, resolution=0.0001, orient='horizontal', variable=self.master.low_cutoff, length=180)
        lowpass_scale.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        lowpass_entry = ttk.Entry(parent, textvariable=self.master.low_cutoff, width=8)
        lowpass_entry.grid(row=1, column=2, sticky='w', padx=5, pady=2)
        # 高通截止频率
        ttk.Label(parent, text='Highpass (Hz):').grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.master.high_cutoff = getattr(self.master, 'high_cutoff', tk.DoubleVar(value=5.0))
        highpass_scale = tk.Scale(parent, from_=0.01, to=10, resolution=0.01, orient='horizontal', variable=self.master.high_cutoff, length=180)
        highpass_scale.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        highpass_entry = ttk.Entry(parent, textvariable=self.master.high_cutoff, width=8)
        highpass_entry.grid(row=2, column=2, sticky='w', padx=5, pady=2)
        # Downsample
        ttk.Label(parent, text='Downsample:').grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.master.downsample_factor = getattr(self.master, 'downsample_factor', tk.IntVar(value=1))
        downsample_entry = ttk.Entry(parent, textvariable=self.master.downsample_factor, width=10)
        downsample_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        # Edge protection
        self.master.edge_protection = getattr(self.master, 'edge_protection', tk.BooleanVar(value=True))
        ttk.Checkbutton(parent, text='Edge Protection', variable=self.master.edge_protection).grid(row=3, column=2, columnspan=2, sticky='w', padx=5, pady=2)
        # Raw signal filtering option
        ttk.Label(parent, text='Apply to Raw Signals:').grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.master.filter_raw_signals = getattr(self.master, 'filter_raw_signals', tk.BooleanVar(value=True))
        ttk.Checkbutton(parent, text='Filter Raw Signals', variable=self.master.filter_raw_signals).grid(row=4, column=1, columnspan=2, sticky='w', padx=5, pady=2)
        
        # Apply按钮
        ttk.Button(parent, text='Apply Filter', command=self.master.update_filter).grid(row=5, column=0, columnspan=6, sticky='ew', padx=5, pady=8)
        
        # Show filtered raw signals button
        ttk.Button(parent, text='Show Filtered Raw Signals', command=self.master.show_filtered_raw_signals).grid(row=6, column=0, columnspan=6, sticky='ew', padx=5, pady=8)

    def create_drift_controls(self, parent):
        """Create drift correction control widgets."""
        # Drift correction
        ttk.Checkbutton(parent, text='Enable Drift Correction', variable=self.master.drift_correction).grid(row=0, column=0, columnspan=2, sticky='w', padx=5)
        
        # Drift degree
        ttk.Label(parent, text='Polynomial Degree:').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(parent, textvariable=self.master.drift_degree, width=10).grid(row=1, column=1, sticky='ew', padx=5)

    def create_denoising_controls(self, parent):
        """Create denoising controls for the preprocess tab."""
        # Create artifact detection controls
        artifact_frame = ttk.LabelFrame(parent, text='Artifact Detection', padding=5)
        artifact_frame.pack(fill='x', pady=(0, 10))
        
        # Artifact threshold with slider
        ttk.Label(artifact_frame, text='Threshold (Std Devs):').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        artifact_scale = tk.Scale(artifact_frame, from_=1.0, to=10.0, resolution=0.1, orient='horizontal', 
                                 variable=self.master.artifact_threshold, length=180)
        artifact_scale.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Entry(artifact_frame, textvariable=self.master.artifact_threshold, width=8).grid(row=0, column=2, sticky='w', padx=5, pady=2)
        
        # Highlight artifacts button
        ttk.Button(artifact_frame, text='Highlight Artifacts', 
                  command=self.master.highlight_artifacts).grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # Create denoising controls
        denoise_frame = ttk.LabelFrame(parent, text='Advanced Denoising', padding=5)
        denoise_frame.pack(fill='x', pady=(0, 10))
        
        # Aggressive denoising checkbox
        ttk.Checkbutton(denoise_frame, text='Aggressive Mode (Use Control Signal)', 
                       variable=self.master.denoise_aggressive).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # Denoising action buttons
        button_frame = ttk.Frame(denoise_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        ttk.Button(button_frame, text='Run Denoising', 
                  command=self.master.run_advanced_denoising).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Reset Denoising', 
                  command=self.master.reset_denoising).pack(side='left', padx=5)
        
        # Create manual blanking controls
        blank_frame = ttk.LabelFrame(parent, text='Manual Blanking', padding=5)
        blank_frame.pack(fill='x', pady=(0, 10))
        
        # Blanking buttons
        blank_button_frame = ttk.Frame(blank_frame)
        blank_button_frame.pack(fill='x', padx=5, pady=5)
        
        self.master.blanking_button = ttk.Button(blank_button_frame, text='Enable Selection Mode', 
                                               command=self.master.toggle_blanking_mode)
        self.master.blanking_button.pack(side='left', padx=5)
        ttk.Button(blank_button_frame, text='Clear All Blanking', 
                  command=self.master.clear_all_blanking).pack(side='left', padx=5)

    def create_denoising_tab(self, parent):
        """Create the denoising tab."""
        frame = ttk.Frame(parent, padding=5)
        
        # Create artifact detection controls
        artifact_frame = ttk.LabelFrame(frame, text='Artifact Detection', padding=5)
        artifact_frame.pack(fill='x', padx=5, pady=5)
        
        # Artifact threshold with slider
        ttk.Label(artifact_frame, text='Threshold (Std Devs):').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        artifact_scale = tk.Scale(artifact_frame, from_=1.0, to=10.0, resolution=0.1, orient='horizontal', 
                                 variable=self.master.artifact_threshold, length=180)
        artifact_scale.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Entry(artifact_frame, textvariable=self.master.artifact_threshold, width=8).grid(row=0, column=2, sticky='w', padx=5, pady=2)
        
        # Highlight artifacts button
        ttk.Button(artifact_frame, text='Highlight Artifacts', 
                  command=self.master.highlight_artifacts).grid(row=1, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        
        # Create denoising controls
        denoise_frame = ttk.LabelFrame(frame, text='Advanced Denoising', padding=5)
        denoise_frame.pack(fill='x', padx=5, pady=5)
        
        # Aggressive denoising checkbox
        ttk.Checkbutton(denoise_frame, text='Aggressive Mode (Use Control Signal)', 
                       variable=self.master.denoise_aggressive).grid(row=0, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        
        # Denoising action buttons
        button_frame = ttk.Frame(denoise_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        ttk.Button(button_frame, text='Run Denoising', 
                  command=self.master.run_advanced_denoising).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Reset Denoising', 
                  command=self.master.reset_denoising).pack(side='left', padx=5)
        
        # Create manual blanking controls
        blank_frame = ttk.LabelFrame(frame, text='Manual Blanking', padding=5)
        blank_frame.pack(fill='x', padx=5, pady=5)
        
        # Blanking buttons
        blank_button_frame = ttk.Frame(blank_frame)
        blank_button_frame.pack(fill='x', padx=5, pady=5)
        
        self.master.blanking_button = ttk.Button(blank_button_frame, text='Enable Selection Mode', 
                                               command=self.master.toggle_blanking_mode)
        self.master.blanking_button.pack(side='left', padx=5)
        ttk.Button(blank_button_frame, text='Clear All Blanking', 
                  command=self.master.clear_all_blanking).pack(side='left', padx=5)
        
        return frame

    def create_peak_tab(self, parent):
        """Create the peak-valley detection tab."""
        frame = ttk.Frame(parent, padding=5)
        
        # Create detection parameters frame
        params_frame = ttk.LabelFrame(frame, text='Detection Parameters', padding=5)
        params_frame.pack(fill='x', padx=5, pady=5)
        
        # Prominence with slider
        ttk.Label(params_frame, text='Prominence:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        prominence_scale = tk.Scale(params_frame, from_=0.1, to=20.0, resolution=0.1, orient='horizontal', 
                                  variable=self.master.peak_prominence, length=180)
        prominence_scale.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Entry(params_frame, textvariable=self.master.peak_prominence, width=8).grid(row=0, column=2, sticky='w', padx=5, pady=2)
        
        # Width with slider
        ttk.Label(params_frame, text='Width (s):').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        width_scale = tk.Scale(params_frame, from_=0.1, to=5.0, resolution=0.1, orient='horizontal', 
                              variable=self.master.peak_width_s, length=180)
        width_scale.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        ttk.Entry(params_frame, textvariable=self.master.peak_width_s, width=8).grid(row=1, column=2, sticky='w', padx=5, pady=2)
        
        # Distance with slider
        ttk.Label(params_frame, text='Min Distance (s):').grid(row=2, column=0, sticky='w', padx=5, pady=2)
        distance_scale = tk.Scale(params_frame, from_=0.0, to=30.0, resolution=0.5, orient='horizontal', 
                                 variable=self.master.peak_distance_s, length=180)
        distance_scale.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        ttk.Entry(params_frame, textvariable=self.master.peak_distance_s, width=8).grid(row=2, column=2, sticky='w', padx=5, pady=2)
        
        # Signal source
        ttk.Label(params_frame, text='Signal Source:').grid(row=3, column=0, sticky='w', padx=5, pady=2)
        ttk.Combobox(params_frame, textvariable=self.master.analysis_signal_source, 
                    values=['Primary', 'Secondary'], state='readonly', width=15).grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        
        # Create detection controls frame
        detection_frame = ttk.LabelFrame(frame, text='Detection Controls', padding=5)
        detection_frame.pack(fill='x', padx=5, pady=5)
        
        # Peak detection
        peak_frame = ttk.Frame(detection_frame)
        peak_frame.pack(fill='x', pady=2)
        ttk.Label(peak_frame, text='Peaks:', font=('TkDefaultFont', self.FONT_PARAMS['label']['size'], 'bold')).pack(side='left')
        ttk.Button(peak_frame, text='Detect', command=self.master.detect_peaks).pack(side='left', padx=5)
        ttk.Button(peak_frame, text='Clear', command=self.master.clear_peaks).pack(side='left', padx=5)
        ttk.Checkbutton(peak_frame, text='Show', variable=self.master.show_peaks,
                       command=self.master.update_peak_display).pack(side='left', padx=5)
        
        # Valley detection  
        valley_frame = ttk.Frame(detection_frame)
        valley_frame.pack(fill='x', pady=2)
        ttk.Label(valley_frame, text='Valleys:', font=('TkDefaultFont', self.FONT_PARAMS['label']['size'], 'bold')).pack(side='left')
        ttk.Button(valley_frame, text='Detect', command=self.master.detect_valleys).pack(side='left', padx=5)
        ttk.Button(valley_frame, text='Clear', command=self.master.clear_valleys).pack(side='left', padx=5)
        ttk.Checkbutton(valley_frame, text='Show', variable=self.master.show_valleys,
                       command=self.master.update_peak_display).pack(side='left', padx=5)
        
        # Clear all button
        ttk.Button(detection_frame, text='Clear All Detections', 
                  command=lambda: [self.master.clear_peaks(), self.master.clear_valleys()]).pack(pady=5)
        
        # Add parameter output window
        output_frame = ttk.LabelFrame(frame, text='Analysis Results', padding=5)
        output_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create results text area
        self.peak_results = tk.Text(output_frame, height=8, width=60, font=('Courier', 9))
        peak_scrollbar = ttk.Scrollbar(output_frame, orient='vertical', command=self.peak_results.yview)
        self.peak_results.configure(yscrollcommand=peak_scrollbar.set)
        
        self.peak_results.pack(side='left', fill='both', expand=True)
        peak_scrollbar.pack(side='right', fill='y')
        
        # Add initial message
        self.peak_results.insert(tk.END, "Peak-Valley Analysis Results\n")
        self.peak_results.insert(tk.END, "="*40 + "\n")
        self.peak_results.insert(tk.END, "Run peak or valley detection to see results here.\n\n")
        self.peak_results.config(state='disabled')
        
        # Create metrics table for time/height/FWHM/area/rise/decay
        metrics_frame = ttk.LabelFrame(frame, text='Peak-Valley Metrics', padding=5)
        metrics_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for metrics
        columns = ('Event', 'Time (s)', 'Height', 'FWHM (s)', 'Area', 'Rise (s)', 'Decay (s)')
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=columns, show='headings', height=6)
        
        # Configure column headings and widths
        for col in columns:
            self.metrics_tree.heading(col, text=col)
            self.metrics_tree.column(col, width=80, anchor='center')
        
        # Add scrollbar for metrics table
        metrics_scrollbar = ttk.Scrollbar(metrics_frame, orient='vertical', command=self.metrics_tree.yview)
        self.metrics_tree.configure(yscrollcommand=metrics_scrollbar.set)
        
        self.metrics_tree.pack(side='left', fill='both', expand=True)
        metrics_scrollbar.pack(side='right', fill='y')
        
        return frame

    def _create_signal_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Signal Processing")
        
        # Create controls frame
        frame = tk.Frame(tab)
        frame.pack(fill='x', pady=5, padx=5)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(5, weight=1)
        
        # Add controls with consistent font
        tk.Label(frame, text="Low Cutoff (Hz):", font=self.FONT_PARAMS['label']).grid(row=0, column=0, sticky='w')
        tk.Scale(frame, from_=0.0, to=0.1, resolution=0.001, orient='horizontal', 
                variable=self.master.low_cutoff, font=self.FONT_PARAMS['slider']).grid(row=0, column=1, sticky='ew')
        
        tk.Label(frame, text="High Cutoff (Hz):", font=self.FONT_PARAMS['label']).grid(row=0, column=2, sticky='w')
        tk.Scale(frame, from_=1.0, to=20.0, resolution=0.5, orient='horizontal', 
                variable=self.master.high_cutoff, font=self.FONT_PARAMS['slider']).grid(row=0, column=3, sticky='ew')
        
        tk.Label(frame, text="Downsample:", font=self.FONT_PARAMS['label']).grid(row=0, column=4, sticky='w')
        tk.Scale(frame, from_=1, to=100, orient='horizontal', 
                variable=self.master.downsample_factor, font=self.FONT_PARAMS['slider']).grid(row=0, column=5, sticky='ew')
        
        # Drift correction frame
        drift_frame = tk.Frame(tab)
        drift_frame.pack(fill='x', pady=5, padx=5)
        
        tk.Checkbutton(drift_frame, text="Drift Correction", variable=self.master.drift_correction,
                      font=self.FONT_PARAMS['label']).pack(side='left', padx=10)
        
        tk.Label(drift_frame, text="Poly Degree:", font=self.FONT_PARAMS['label']).pack(side='left')
        for i in range(1, 5):
            tk.Radiobutton(drift_frame, text=str(i), variable=self.master.drift_degree,
                          value=i, font=self.FONT_PARAMS['label']).pack(side='left')
        
        tk.Checkbutton(drift_frame, text="Enable Edge Protection", variable=self.master.edge_protection,
                      font=self.FONT_PARAMS['label']).pack(side='left', padx=10)
        
        # Apply button
        tk.Button(tab, text="Apply Filters", bg="lightgreen", command=self.master.update_filter,
                 font=self.FONT_PARAMS['button']).pack(pady=10)

    def _create_denoising_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="Denoising & Blanking")
        artifact_frame = tk.LabelFrame(tab, text="Artifact Detection", padx=5, pady=5); artifact_frame.pack(fill='x', pady=5)
        tk.Label(artifact_frame, text="Threshold (Std Devs):").pack(side='left', padx=5)
        tk.Scale(artifact_frame, from_=1.0, to=10.0, resolution=0.1, orient='horizontal', variable=self.master.artifact_threshold).pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(artifact_frame, text="Highlight Artifacts", command=self.master.highlight_artifacts).pack(side='left', padx=5)
        denoise_frame = tk.LabelFrame(tab, text="Advanced Denoising", padx=5, pady=5); denoise_frame.pack(fill='x', pady=5)
        tk.Checkbutton(denoise_frame, text="Aggressive Mode (Use Control Signal)", variable=self.master.denoise_aggressive).pack(side='left', padx=5)
        tk.Button(denoise_frame, text="Run Denoising", bg="lightblue", command=self.master.run_advanced_denoising).pack(side='left', padx=5)
        tk.Button(denoise_frame, text="Reset Denoising", command=self.master.reset_denoising).pack(side='left', padx=5)
        blank_frame = tk.LabelFrame(tab, text="Manual Blanking", padx=5, pady=5); blank_frame.pack(fill='x', pady=5)
        self.master.blanking_button = tk.Button(blank_frame, text="Enable Selection Mode", command=self.master.toggle_blanking_mode)
        self.master.blanking_button.pack(side='left', padx=5)
        tk.Button(blank_frame, text="Clear All Blanking", bg='salmon', command=self.master.clear_all_blanking).pack(side='left', padx=5)

    def _create_synchronization_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="Synchronization")
        frame = tk.LabelFrame(tab, text="Secondary File Time Shift", padx=5, pady=5); frame.pack(fill='x', pady=5)
        tk.Label(frame, text="Shift (s):").pack(side='left', padx=5)
        tk.Scale(frame, from_=-60.0, to=60.0, resolution=0.1, orient='horizontal', length=400, variable=self.master.time_shift_s).pack(side='left', fill='x', expand=True, padx=5)
        tk.Button(frame, text="Apply Shift", bg='lightgoldenrodyellow', command=self.master.apply_time_shift).pack(side='left', padx=5)

    def _create_peak_tab(self):
        """Create the peak detection tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Peak Detection")
        
        # Create controls frame
        controls_frame = tk.Frame(tab)
        controls_frame.pack(fill='x', pady=5, padx=5)
        
        # Create parameters frame
        params_frame = tk.Frame(controls_frame)
        params_frame.pack(fill='x', pady=5, padx=5)
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)
        params_frame.columnconfigure(5, weight=1)
        
        # Add parameter controls
        tk.Label(params_frame, text="Prominence:").grid(row=0, column=0, sticky='w')
        tk.Scale(params_frame, from_=0.1, to=20.0, resolution=0.1, orient='horizontal', 
                variable=self.master.peak_prominence).grid(row=0, column=1, sticky='ew')
        tk.Label(params_frame, text="Min Width (s):").grid(row=0, column=2, sticky='w')
        tk.Scale(params_frame, from_=0.1, to=5.0, resolution=0.1, orient='horizontal', 
                variable=self.master.peak_width_s).grid(row=0, column=3, sticky='ew')
        tk.Label(params_frame, text="Min Distance (s):").grid(row=0, column=4, sticky='w')
        tk.Scale(params_frame, from_=0, to=30.0, resolution=0.5, orient='horizontal', 
                variable=self.master.peak_distance_s).grid(row=0, column=5, sticky='ew')

        # Add action buttons
        action_frame = tk.Frame(controls_frame)
        action_frame.pack(fill='x', pady=5, padx=5)
        tk.Radiobutton(action_frame, text="Primary", variable=self.master.analysis_signal_source, 
                      value="Primary").pack(side='left', padx=5)
        tk.Radiobutton(action_frame, text="Secondary", variable=self.master.analysis_signal_source, 
                      value="Secondary").pack(side='left', padx=5)
        tk.Button(action_frame, text="Detect Peaks", command=lambda: self.master.run_detection('Peak'), 
                 bg='lightblue').pack(side='left', padx=10)
        tk.Button(action_frame, text="Clear Peaks", command=lambda: self.master.clear_detection('Peak')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Analyze Intervals", command=lambda: self.master.analyze_intervals('Peak')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Export Metrics", command=lambda: self.master.export_metrics('Peak')).pack(side='left', padx=5)
        tk.Checkbutton(action_frame, text="Show Peaks", variable=self.master.show_peaks).pack(side='left', padx=10)
        
        # Create metrics table
        table_frame = tk.Frame(tab)
        table_frame.pack(fill='both', expand=True, pady=5, padx=5)
        cols = ("#", "Time (s)", "Height", "Width (s)", "Area", "Rise (s)", "Decay (s)")
        self.master.peak_metrics_tree = ttk.Treeview(table_frame, columns=cols, show='headings')
        for col in cols:
            self.master.peak_metrics_tree.heading(col, text=col)
            self.master.peak_metrics_tree.column(col, width=100)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.master.peak_metrics_tree.yview)
        self.master.peak_metrics_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.master.peak_metrics_tree.pack(side='left', fill='both', expand=True)

    def _create_valley_tab(self):
        """Create the valley detection tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Valley Detection")
        
        # Create controls frame
        controls_frame = tk.Frame(tab)
        controls_frame.pack(fill='x', pady=5, padx=5)
        
        # Create parameters frame
        params_frame = tk.Frame(controls_frame)
        params_frame.pack(fill='x', pady=5, padx=5)
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)
        params_frame.columnconfigure(5, weight=1)
        
        # Add parameter controls
        tk.Label(params_frame, text="Prominence:").grid(row=0, column=0, sticky='w')
        tk.Scale(params_frame, from_=0.1, to=20.0, resolution=0.1, orient='horizontal', 
                variable=self.master.peak_prominence).grid(row=0, column=1, sticky='ew')
        tk.Label(params_frame, text="Min Width (s):").grid(row=0, column=2, sticky='w')
        tk.Scale(params_frame, from_=0.1, to=5.0, resolution=0.1, orient='horizontal', 
                variable=self.master.peak_width_s).grid(row=0, column=3, sticky='ew')
        tk.Label(params_frame, text="Min Distance (s):").grid(row=0, column=4, sticky='w')
        tk.Scale(params_frame, from_=0, to=30.0, resolution=0.5, orient='horizontal', 
                variable=self.master.peak_distance_s).grid(row=0, column=5, sticky='ew')

        # Add action buttons
        action_frame = tk.Frame(controls_frame)
        action_frame.pack(fill='x', pady=5, padx=5)
        tk.Radiobutton(action_frame, text="Primary", variable=self.master.analysis_signal_source, 
                      value="Primary").pack(side='left', padx=5)
        tk.Radiobutton(action_frame, text="Secondary", variable=self.master.analysis_signal_source, 
                      value="Secondary").pack(side='left', padx=5)
        tk.Button(action_frame, text="Detect Valleys", command=lambda: self.master.run_detection('Valley'), 
                 bg='lightblue').pack(side='left', padx=10)
        tk.Button(action_frame, text="Clear Valleys", command=lambda: self.master.clear_detection('Valley')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Analyze Intervals", command=lambda: self.master.analyze_intervals('Valley')).pack(side='left', padx=5)
        tk.Button(action_frame, text="Export Metrics", command=lambda: self.master.export_metrics('Valley')).pack(side='left', padx=5)
        tk.Checkbutton(action_frame, text="Show Valleys", variable=self.master.show_valleys).pack(side='left', padx=10)
        
        # Create metrics table
        table_frame = tk.Frame(tab)
        table_frame.pack(fill='both', expand=True, pady=5, padx=5)
        cols = ("#", "Time (s)", "Depth", "Width (s)", "Area Above")
        self.master.valley_metrics_tree = ttk.Treeview(table_frame, columns=cols, show='headings')
        for col in cols:
            self.master.valley_metrics_tree.heading(col, text=col)
            self.master.valley_metrics_tree.column(col, width=100)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.master.valley_metrics_tree.yview)
        self.master.valley_metrics_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.master.valley_metrics_tree.pack(side='left', fill='both', expand=True)

    def _create_psth_tab(self):
        tab = ttk.Frame(self.notebook); self.notebook.add(tab, text="PSTH Analysis")
        tk.Label(tab, text="PSTH controls will be added in a future step.").pack(pady=20)

    def create_signal_visibility_frame(self, parent):
        """Create frame for signal visibility controls."""
        frame = ttk.LabelFrame(parent, text="Signal Visibility", padding=5)
        
        # Primary signal visibility
        ttk.Label(frame, text="Primary Signal:", font=self.FONT_PARAMS['label']).pack(anchor='w', pady=(5,0))
        primary_frame = ttk.Frame(frame)
        primary_frame.pack(fill='x', padx=5, pady=2)
        
        self.primary_dff_var = tk.BooleanVar(value=True)
        self.primary_raw_var = tk.BooleanVar(value=True)
        self.primary_control_var = tk.BooleanVar(value=True)
        self.primary_ttl1_var = tk.BooleanVar(value=True)
        self.primary_ttl2_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(primary_frame, text="ΔF/F", variable=self.primary_dff_var).pack(side='left', padx=5)
        ttk.Checkbutton(primary_frame, text="Raw", variable=self.primary_raw_var).pack(side='left', padx=5)
        ttk.Checkbutton(primary_frame, text="Control", variable=self.primary_control_var).pack(side='left', padx=5)
        ttk.Checkbutton(primary_frame, text="TTL1", variable=self.primary_ttl1_var).pack(side='left', padx=5)
        ttk.Checkbutton(primary_frame, text="TTL2", variable=self.primary_ttl2_var).pack(side='left', padx=5)
        
        # Secondary signal visibility
        ttk.Label(frame, text="Secondary Signal:", font=self.FONT_PARAMS['label']).pack(anchor='w', pady=(10,0))
        secondary_frame = ttk.Frame(frame)
        secondary_frame.pack(fill='x', padx=5, pady=2)
        
        self.secondary_dff_var = tk.BooleanVar(value=True)
        self.secondary_raw_var = tk.BooleanVar(value=True)
        self.secondary_control_var = tk.BooleanVar(value=True)
        self.secondary_ttl1_var = tk.BooleanVar(value=True)
        self.secondary_ttl2_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(secondary_frame, text="ΔF/F", variable=self.secondary_dff_var).pack(side='left', padx=5)
        ttk.Checkbutton(secondary_frame, text="Raw", variable=self.secondary_raw_var).pack(side='left', padx=5)
        ttk.Checkbutton(secondary_frame, text="Control", variable=self.secondary_control_var).pack(side='left', padx=5)
        ttk.Checkbutton(secondary_frame, text="TTL1", variable=self.secondary_ttl1_var).pack(side='left', padx=5)
        ttk.Checkbutton(secondary_frame, text="TTL2", variable=self.secondary_ttl2_var).pack(side='left', padx=5)
        
        # Add apply button for signal visibility
        apply_frame = ttk.Frame(frame)
        apply_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(apply_frame, text="Apply Signal Visibility", 
                  command=lambda: self.master.update_plot_visibility()).pack(side='left', padx=5)
        
        return frame

    def create_file_display(self, parent):
        """Create file name display widgets."""
        # Primary file
        primary_frame = ttk.Frame(parent)
        primary_frame.pack(fill='x', pady=2)
        ttk.Label(primary_frame, text="Primary:", font=('TkDefaultFont', self.FONT_PARAMS['label']['size'])).pack(side='left')
        self.primary_file_label = ttk.Label(primary_frame, text="No file loaded", 
                                          font=('TkDefaultFont', self.FONT_PARAMS['label']['size']), 
                                          foreground='gray')
        self.primary_file_label.pack(side='left', padx=(10, 0))
        
        # Primary sample rate
        self.primary_fs_label = ttk.Label(primary_frame, text="", 
                                        font=('TkDefaultFont', self.FONT_PARAMS['label']['size']-1), 
                                        foreground='blue')
        self.primary_fs_label.pack(side='right')
        
        # Secondary file
        secondary_frame = ttk.Frame(parent)
        secondary_frame.pack(fill='x', pady=2)
        ttk.Label(secondary_frame, text="Secondary:", font=('TkDefaultFont', self.FONT_PARAMS['label']['size'])).pack(side='left')
        self.secondary_file_label = ttk.Label(secondary_frame, text="No file loaded", 
                                            font=('TkDefaultFont', self.FONT_PARAMS['label']['size']), 
                                            foreground='gray')
        self.secondary_file_label.pack(side='left', padx=(10, 0))
        
        # Secondary sample rate
        self.secondary_fs_label = ttk.Label(secondary_frame, text="", 
                                          font=('TkDefaultFont', self.FONT_PARAMS['label']['size']-1), 
                                          foreground='blue')
        self.secondary_fs_label.pack(side='right')
        
    def update_file_display(self, primary_file=None, secondary_file=None, primary_fs=None, secondary_fs=None):
        """Update the file display labels."""
        if primary_file:
            filename = os.path.basename(primary_file)
            self.primary_file_label.config(text=filename, foreground='black')
        if secondary_file:
            filename = os.path.basename(secondary_file)
            self.secondary_file_label.config(text=filename, foreground='black')
        if primary_fs:
            self.primary_fs_label.config(text=f"fs: {primary_fs} Hz")
        if secondary_fs:
            self.secondary_fs_label.config(text=f"fs: {secondary_fs} Hz")
            
    def clear_file_display(self, clear_primary=False, clear_secondary=False):
        """Clear file display."""
        if clear_primary:
            self.primary_file_label.config(text="No file loaded", foreground='gray')
            self.primary_fs_label.config(text="")
        if clear_secondary:
            self.secondary_file_label.config(text="No file loaded", foreground='gray')
            self.secondary_fs_label.config(text="")
            
    def create_psth_tab(self, parent):
        """Create the PSTH analysis tab."""
        frame = ttk.Frame(parent, padding=5)
        
        # PSTH parameters frame
        params_frame = ttk.LabelFrame(frame, text='PSTH Parameters', padding=5)
        params_frame.pack(fill='x', padx=5, pady=5)
        
        # Event type selection
        ttk.Label(params_frame, text='Event Type:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.master.psth_event_type = getattr(self.master, 'psth_event_type', tk.StringVar(value='Peaks'))
        ttk.Combobox(params_frame, textvariable=self.master.psth_event_type, 
                    values=['Peaks', 'Valleys'], state='readonly', width=15).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        # Signal source for PSTH
        ttk.Label(params_frame, text='Signal Source:').grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.master.psth_signal_source = getattr(self.master, 'psth_signal_source', tk.StringVar(value='Primary'))
        ttk.Combobox(params_frame, textvariable=self.master.psth_signal_source, 
                    values=['Primary', 'Secondary'], state='readonly', width=15).grid(row=0, column=3, sticky='w', padx=5, pady=2)
        
        # Pre-event window
        ttk.Label(params_frame, text='Pre-event (s):').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.master.psth_pre_time = getattr(self.master, 'psth_pre_time', tk.DoubleVar(value=5.0))
        pre_scale = tk.Scale(params_frame, from_=1.0, to=30.0, resolution=0.5, orient='horizontal', 
                            variable=self.master.psth_pre_time, length=120)
        pre_scale.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # Post-event window
        ttk.Label(params_frame, text='Post-event (s):').grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.master.psth_post_time = getattr(self.master, 'psth_post_time', tk.DoubleVar(value=10.0))
        post_scale = tk.Scale(params_frame, from_=1.0, to=30.0, resolution=0.5, orient='horizontal', 
                             variable=self.master.psth_post_time, length=120)
        post_scale.grid(row=1, column=3, sticky='ew', padx=5, pady=2)
        
        # Bin size
        ttk.Label(params_frame, text='Bin size (s):').grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.master.psth_bin_size = getattr(self.master, 'psth_bin_size', tk.DoubleVar(value=0.1))
        bin_scale = tk.Scale(params_frame, from_=0.01, to=1.0, resolution=0.01, orient='horizontal', 
                            variable=self.master.psth_bin_size, length=120)
        bin_scale.grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        
        # Generate PSTH button
        ttk.Button(params_frame, text='Generate PSTH', 
                  command=self.master.generate_psth).grid(row=2, column=2, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # PSTH results frame
        results_frame = ttk.LabelFrame(frame, text='PSTH Results', padding=5)
        results_frame.pack(fill='x', padx=5, pady=5)
        
        # Create PSTH results text area
        self.psth_results = tk.Text(results_frame, height=6, width=60, font=('Courier', 9))
        psth_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.psth_results.yview)
        self.psth_results.configure(yscrollcommand=psth_scrollbar.set)
        
        self.psth_results.pack(side='left', fill='both', expand=True)
        psth_scrollbar.pack(side='right', fill='y')
        
        # Add initial message
        self.psth_results.insert(tk.END, "PSTH Analysis Results\n")
        self.psth_results.insert(tk.END, "="*30 + "\n")
        self.psth_results.insert(tk.END, "Generate PSTH to see results here.\n\n")
        self.psth_results.config(state='disabled')
        
        # PSTH plot frame
        plot_frame = ttk.LabelFrame(frame, text='PSTH Plot', padding=5)
        plot_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Import matplotlib here to avoid initial import issues
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Create PSTH figure
        self.psth_fig, self.psth_ax = plt.subplots(figsize=(8, 4), dpi=80)
        self.psth_canvas = FigureCanvasTkAgg(self.psth_fig, master=plot_frame)
        self.psth_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Configure PSTH plot
        self.psth_ax.set_xlabel('Time relative to event (s)')
        self.psth_ax.set_ylabel('ΔF/F (%)')
        self.psth_ax.set_title('Peri-Stimulus Time Histogram')
        self.psth_ax.grid(True, alpha=0.3)
        self.psth_fig.tight_layout()
        
        return frame
    
    def create_correlation_tab(self, parent):
        """Create the correlation analysis tab."""
        frame = ttk.Frame(parent, padding=10)
        
        # Correlation parameters
        params_frame = ttk.LabelFrame(frame, text='Correlation Parameters', padding=5)
        params_frame.pack(fill='x', pady=(0, 10))
        
        # Signal selection
        ttk.Label(params_frame, text='Signal 1:').grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.master.corr_signal1 = getattr(self.master, 'corr_signal1', tk.StringVar(value='Primary ΔF/F'))
        signal1_combo = ttk.Combobox(params_frame, textvariable=self.master.corr_signal1, 
                                   values=['Primary ΔF/F', 'Primary Raw', 'Secondary ΔF/F', 'Secondary Raw'], 
                                   state='readonly', width=15)
        signal1_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        
        ttk.Label(params_frame, text='Signal 2:').grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.master.corr_signal2 = getattr(self.master, 'corr_signal2', tk.StringVar(value='Secondary ΔF/F'))
        signal2_combo = ttk.Combobox(params_frame, textvariable=self.master.corr_signal2, 
                                   values=['Primary ΔF/F', 'Primary Raw', 'Secondary ΔF/F', 'Secondary Raw'], 
                                   state='readonly', width=15)
        signal2_combo.grid(row=0, column=3, sticky='ew', padx=5, pady=2)
        
        # Time window parameters
        ttk.Label(params_frame, text='Window size (s):').grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.master.corr_window = getattr(self.master, 'corr_window', tk.DoubleVar(value=10.0))
        window_scale = tk.Scale(params_frame, from_=1.0, to=60.0, resolution=0.5, orient='horizontal', 
                               variable=self.master.corr_window, length=120)
        window_scale.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        
        # Max lag for cross-correlation
        ttk.Label(params_frame, text='Max lag (s):').grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.master.corr_max_lag = getattr(self.master, 'corr_max_lag', tk.DoubleVar(value=5.0))
        lag_scale = tk.Scale(params_frame, from_=0.1, to=20.0, resolution=0.1, orient='horizontal', 
                            variable=self.master.corr_max_lag, length=120)
        lag_scale.grid(row=1, column=3, sticky='ew', padx=5, pady=2)
        
        # Analysis buttons
        button_frame = ttk.Frame(params_frame)
        button_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=5)
        
        ttk.Button(button_frame, text='Pearson Correlation', 
                  command=self.master.calculate_pearson_correlation).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Cross-Correlation', 
                  command=self.master.calculate_cross_correlation).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Granger Causality', 
                  command=self.master.calculate_granger_causality).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Rolling Correlation', 
                  command=self.master.calculate_rolling_correlation).pack(side='left', padx=5)
        
        # Results display
        results_frame = ttk.LabelFrame(frame, text='Correlation Results', padding=5)
        results_frame.pack(fill='both', expand=True, pady=5)
        
        # Create results text area
        self.correlation_results = tk.Text(results_frame, height=8, width=60, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.correlation_results.yview)
        self.correlation_results.configure(yscrollcommand=scrollbar.set)
        
        self.correlation_results.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Correlation plot frame
        plot_frame = ttk.LabelFrame(frame, text='Correlation Plot', padding=5)
        plot_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Import matplotlib here to avoid initial import issues
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Create correlation figure
        self.corr_fig, self.corr_ax = plt.subplots(figsize=(8, 4), dpi=80)
        self.corr_canvas = FigureCanvasTkAgg(self.corr_fig, master=plot_frame)
        self.corr_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Configure correlation plot
        self.corr_ax.set_xlabel('Time/Lag (s)')
        self.corr_ax.set_ylabel('Correlation Coefficient')
        self.corr_ax.set_title('Signal Correlation Analysis')
        self.corr_ax.grid(True, alpha=0.3)
        self.corr_fig.tight_layout()
        
        return frame