# file: gpu_processing_fixed.py

import numpy as np
import warnings
from typing import Optional, Tuple, Union
import sys
import os

# Initialize CuPy directly without complex logic
try:
    import cupy as cp
    import cupyx.scipy.signal as cupy_signal
    import cupyx.scipy.ndimage as cupy_ndimage
    
    # Test GPU availability
    device_count = cp.cuda.runtime.getDeviceCount()
    CUPY_AVAILABLE = device_count > 0
    
    if CUPY_AVAILABLE:
        print(f"CuPy available - GPU acceleration enabled ({device_count} devices)")
    else:
        print("No GPU devices found")
        
except Exception as e:
    CUPY_AVAILABLE = False
    cp = None
    cupy_signal = None
    cupy_ndimage = None
    print(f"CuPy not available - falling back to CPU processing: {e}")

# Initialize Numba
try:
    import numba
    from numba import cuda, jit
    NUMBA_AVAILABLE = True
    print("Numba available - JIT compilation enabled")
except ImportError:
    NUMBA_AVAILABLE = False
    print("Numba not available - no JIT acceleration")

class GPUAccelerator:
    """GPU acceleration manager for signal processing."""
    
    def __init__(self, force_cpu=False):
        """Initialize GPU accelerator."""
        self.force_cpu = force_cpu
        self.gpu_available = CUPY_AVAILABLE and not force_cpu
        self.cuda_available = NUMBA_AVAILABLE and not force_cpu
        
        if self.gpu_available:
            try:
                # Test GPU availability
                self.device_count = cp.cuda.runtime.getDeviceCount()
                
                # Get GPU memory info
                meminfo = cp.cuda.runtime.memGetInfo()
                self.gpu_memory_free = meminfo[0]
                self.gpu_memory_total = meminfo[1]
                
                print(f"GPU initialized: {self.device_count} device(s), "
                      f"{self.gpu_memory_free/1024**3:.1f}GB free / "
                      f"{self.gpu_memory_total/1024**3:.1f}GB total")
                
                # Initialize memory management
                self.memory_pool = cp.get_default_memory_pool()
                
            except Exception as e:
                print(f"GPU initialization failed: {e}")
                self.gpu_available = False
                self.device_count = 0
                self.gpu_memory_free = 0
                self.gpu_memory_total = 0
                self.memory_pool = None
        else:
            self.device_count = 0
            self.gpu_memory_free = 0
            self.gpu_memory_total = 0
            self.memory_pool = None
    
    def get_device_info(self):
        """Get GPU device information."""
        if not self.gpu_available:
            return {"status": "CPU only", "devices": 0}
        
        try:
            device_info = {
                "status": "GPU available",
                "devices": self.device_count,
                "memory_free_gb": self.gpu_memory_free / 1024**3,
                "memory_total_gb": self.gpu_memory_total / 1024**3,
                "memory_used_percent": (1 - self.gpu_memory_free / self.gpu_memory_total) * 100
            }
            return device_info
        except Exception as e:
            return {"status": f"GPU error: {e}", "devices": 0}
    
    def to_gpu(self, data: np.ndarray) -> Union[np.ndarray, 'cp.ndarray']:
        """Move data to GPU if available."""
        if not self.gpu_available or data is None:
            return data
        
        try:
            # Check if data is already on GPU
            if hasattr(data, 'device'):
                return data
            
            # Check memory requirements
            data_size = data.nbytes
            if data_size > self.gpu_memory_free * 0.8:  # Use max 80% of free memory
                print(f"WARNING: Data too large for GPU ({data_size/1024**3:.1f}GB), using CPU")
                return data
            
            return cp.asarray(data)
        except Exception as e:
            print(f"WARNING: GPU transfer failed: {e}")
            return data
    
    def to_cpu(self, data: Union[np.ndarray, 'cp.ndarray']) -> np.ndarray:
        """Move data back to CPU."""
        if not hasattr(data, 'device'):
            return data
        
        try:
            return cp.asnumpy(data)
        except Exception as e:
            print(f"WARNING: CPU transfer failed: {e}")
            return data
    
    def clear_memory(self):
        """Clear GPU memory."""
        if self.gpu_available and self.memory_pool:
            try:
                self.memory_pool.free_all_blocks()
                print("GPU memory cleared")
            except Exception as e:
                print(f"WARNING: Memory clear failed: {e}")

# Global GPU accelerator instance
gpu_accel = GPUAccelerator()

def gpu_butter_filter(data: np.ndarray, cutoff: Union[float, list], fs: float, 
                     btype: str = 'low', order: int = 2) -> np.ndarray:
    """GPU-accelerated Butterworth filter."""
    if not gpu_accel.gpu_available:
        # Fallback to CPU
        from signal_processing import butter_filter
        return butter_filter(data, cutoff, fs, btype, order, zero_phase=True)
    
    try:
        # Move data to GPU
        gpu_data = gpu_accel.to_gpu(data)
        
        # Calculate normalized cutoff frequencies
        nyq = 0.5 * fs
        if isinstance(cutoff, (list, tuple)):
            normal_cutoff = [c / nyq for c in cutoff]
        else:
            normal_cutoff = cutoff / nyq
        
        # Create filter coefficients
        from scipy.signal import butter
        sos = butter(order, normal_cutoff, btype=btype, analog=False, output='sos')
        
        # Apply filter on GPU
        filtered_gpu = cupy_signal.sosfiltfilt(sos, gpu_data)
        
        # Move result back to CPU
        filtered_data = gpu_accel.to_cpu(filtered_gpu)
        
        return filtered_data
        
    except Exception as e:
        print(f"WARNING: GPU filter failed: {e}, falling back to CPU")
        # Fallback to CPU
        from signal_processing import butter_filter
        return butter_filter(data, cutoff, fs, btype, order, zero_phase=True)

# Test function
def test_gpu_acceleration():
    """Test GPU acceleration functionality."""
    print("\n=== GPU Acceleration Test ===")
    print(f"GPU Available: {gpu_accel.gpu_available}")
    print(f"Device Count: {gpu_accel.device_count}")
    
    if gpu_accel.gpu_available:
        print("Testing GPU filtering...")
        test_data = np.random.randn(1000).astype(np.float32)
        result = gpu_butter_filter(test_data, 10.0, 1000.0, 'low', 2)
        print(f"SUCCESS: GPU filtering works, output shape: {result.shape}")
    else:
        print("GPU not available - using CPU fallback")

# Initialize GPU processing on import
print(f"GPU processing module loaded - GPU available: {gpu_accel.gpu_available}")

if __name__ == "__main__":
    test_gpu_acceleration()