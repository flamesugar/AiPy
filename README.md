# Photometry Viewer

A Python-based GUI application for viewing and analyzing photometry data.

## Features

- Load and view .ppd files
- Signal processing capabilities (filtering, denoising)
- support GPU acceleration 
- Peak detection and analysis
- PSTH (Peri-Stimulus Time Histogram) analysis
- Interactive plotting with PyQtGraph
<img width="954" height="478" alt="image" src="https://github.com/user-attachments/assets/d483ef6e-a93f-46a8-ad83-19fa506f0da2" />

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/PyGUI.git
cd PyGUI
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

### Basic Usage

1. Click "Load PPD File" to open a .ppd file
2. Use the toolbar to access various analysis functions
3. Interact with the plot using mouse controls:
   - Left click and drag to pan
   - Right click and drag to zoom
   - Mouse wheel to zoom in/out

## Project Structure

```
PyGUI/
├── main.py                     # Main entry point
├── data_io.py                  # File I/O operations
├── signal_processing.py        # Signal processing functions
├── gui/                        # GUI-related modules
│   ├── main_window.py         # Main window implementation
│   ├── plot_manager.py        # Plot management
│   └── dialogs.py             # Dialog windows
└── analysis/                   # Analysis modules
    ├── peak_analysis.py       # Peak detection
    └── psth_analysis.py       # PSTH calculations
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
