# file: main.py

import os
import sys
import logging
import tkinter as tk
from tkinter import ttk
import matplotlib

# Configure logging
matplotlib.set_loglevel('WARNING')
logging.basicConfig(level=logging.WARNING)

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from gui.main_window import PhotometryViewer

def main():
    """Main function to initialize and run the application."""
    try:
        logging.info("Starting application initialization...")
        root = tk.Tk()
        # Set a reasonable initial size
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.8)
        root.geometry(f"{width}x{height}")
        
        logging.info("Creating PhotometryViewer instance...")
        app = PhotometryViewer(root)
        
        logging.info("Starting main event loop...")
        root.mainloop()
    except Exception as e:
        logging.error(f"An error occurred during application startup: {e}")
        import traceback
        logging.error(traceback.format_exc())
        # Fallback to console input if GUI fails to start
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()