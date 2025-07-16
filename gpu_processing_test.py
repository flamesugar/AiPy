# Import CuPy first, before anything else
import cupy as cp
import cupyx.scipy.signal as cupy_signal
import cupyx.scipy.ndimage as cupy_ndimage

# Now import other modules
import numpy as np
import warnings
from typing import Optional, Tuple, Union
import sys
import os

print(f"CuPy imported successfully: {cp.cuda.runtime.getDeviceCount()} devices")
print("Success! GPU acceleration is working.")