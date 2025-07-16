# file: gpu_processing.py

import numpy as np
import warnings
from typing import Optional, Tuple, Union
import sys
import os

# GPU acceleration libraries - simple approach
try:
    import cupy as cp
    device_count = cp.cuda.runtime.getDeviceCount()
    CUPY_AVAILABLE = device_count > 0
    if CUPY_AVAILABLE:
        print(f"CuPy available - GPU acceleration enabled ({device_count} devices)")
    else:
        print("No GPU devices found")
except Exception as e:
    CUPY_AVAILABLE = False
    cp = None
    print(f"CuPy not available - falling back to CPU processing: {e}")

# Note: cupyx.scipy.signal has DLL issues, so we'll use basic CuPy operations
# and implement our own signal processing functions

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
        self.cuda_available = NUMBA_AVAILABLE and not force_cpu
        self.gpu_available = False
        self.device_count = 0
        self.gpu_memory_free = 0
        self.gpu_memory_total = 0
        self.memory_pool = None
        
        # Try to initialize GPU on first access
        if not force_cpu:
            self._try_gpu_init()
    
    def _try_gpu_init(self):
        """Try to initialize GPU."""
        try:
            if CUPY_AVAILABLE and cp is not None:
                self.device_count = cp.cuda.runtime.getDeviceCount()
                
                # Get GPU memory info
                meminfo = cp.cuda.runtime.memGetInfo()
                self.gpu_memory_free = meminfo[0]
                self.gpu_memory_total = meminfo[1]
                
                self.gpu_available = True
                self.memory_pool = cp.get_default_memory_pool()
                
                print(f"GPU initialized: {self.device_count} device(s), "
                      f"{self.gpu_memory_free/1024**3:.1f}GB free / "
                      f"{self.gpu_memory_total/1024**3:.1f}GB total")
                
        except Exception as e:
            print(f"GPU initialization failed: {e}")
            self.gpu_available = False
    
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
        if not self.gpu_available or data is None or cp is None:
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
            if cp is None:
                return data
            
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
        
        # Create filter coefficients on CPU
        from scipy.signal import butter, sosfiltfilt
        sos = butter(order, normal_cutoff, btype=btype, analog=False, output='sos')
        
        # Apply filter on CPU (since cupyx.scipy.signal has DLL issues)
        # Move data back to CPU for filtering
        cpu_data = gpu_accel.to_cpu(gpu_data)
        filtered_data = sosfiltfilt(sos, cpu_data)
        
        return filtered_data
        
    except Exception as e:
        print(f"WARNING: GPU filter failed: {e}, falling back to CPU")
        # Fallback to CPU
        from signal_processing import butter_filter
        return butter_filter(data, cutoff, fs, btype, order, zero_phase=True)

@jit(nopython=True, parallel=True) if NUMBA_AVAILABLE else lambda x: x
def numba_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Numba-accelerated correlation calculation."""
    if len(x) != len(y):
        return 0.0
    
    # Calculate means
    mean_x = np.mean(x)
    mean_y = np.mean(y)
    
    # Calculate correlation coefficient
    numerator = np.sum((x - mean_x) * (y - mean_y))
    denominator = np.sqrt(np.sum((x - mean_x)**2) * np.sum((y - mean_y)**2))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def gpu_correlation_matrix(signals: list) -> np.ndarray:
    """GPU-accelerated correlation matrix calculation."""
    n_signals = len(signals)
    corr_matrix = np.zeros((n_signals, n_signals))
    
    if gpu_accel.gpu_available:
        try:
            # Move all signals to GPU
            gpu_signals = [gpu_accel.to_gpu(signal) for signal in signals]
            
            # Calculate correlation matrix on GPU
            for i in range(n_signals):
                for j in range(i, n_signals):
                    # Use CuPy's correlation function
                    corr = cp.corrcoef(gpu_signals[i], gpu_signals[j])[0, 1]
                    corr_matrix[i, j] = corr_matrix[j, i] = float(corr)
            
            return corr_matrix
            
        except Exception as e:
            print(f"WARNING: GPU correlation failed: {e}, using CPU")
    
    # CPU fallback
    for i in range(n_signals):
        for j in range(i, n_signals):
            if NUMBA_AVAILABLE:
                corr = numba_correlation(signals[i], signals[j])
            else:
                corr = np.corrcoef(signals[i], signals[j])[0, 1]
            corr_matrix[i, j] = corr_matrix[j, i] = corr
    
    return corr_matrix

def gpu_fft_analysis(signal: np.ndarray, fs: float) -> Tuple[np.ndarray, np.ndarray]:
    """GPU-accelerated FFT analysis."""
    if gpu_accel.gpu_available:
        try:
            # Move signal to GPU
            gpu_signal = gpu_accel.to_gpu(signal)
            
            # Compute FFT on GPU
            fft_result = cp.fft.fft(gpu_signal)
            freqs = cp.fft.fftfreq(len(signal), 1/fs)
            
            # Calculate power spectral density
            psd = cp.abs(fft_result)**2
            
            # Move results back to CPU
            freqs_cpu = gpu_accel.to_cpu(freqs)
            psd_cpu = gpu_accel.to_cpu(psd)
            
            # Return positive frequencies only
            positive_freqs = freqs_cpu[:len(freqs_cpu)//2]
            positive_psd = psd_cpu[:len(psd_cpu)//2]
            
            return positive_freqs, positive_psd
            
        except Exception as e:
            print(f"WARNING: GPU FFT failed: {e}, using CPU")
    
    # CPU fallback
    fft_result = np.fft.fft(signal)
    freqs = np.fft.fftfreq(len(signal), 1/fs)
    psd = np.abs(fft_result)**2
    
    # Return positive frequencies only
    positive_freqs = freqs[:len(freqs)//2]
    positive_psd = psd[:len(psd)//2]
    
    return positive_freqs, positive_psd

def gpu_moving_average(signal: np.ndarray, window_size: int) -> np.ndarray:
    """GPU-accelerated moving average."""
    if gpu_accel.gpu_available:
        try:
            # Move signal to GPU
            gpu_signal = gpu_accel.to_gpu(signal)
            
            # Create convolution kernel for moving average
            kernel = cp.ones(window_size) / window_size
            
            # Apply convolution
            result = cp.convolve(gpu_signal, kernel, mode='same')
            
            # Move result back to CPU
            return gpu_accel.to_cpu(result)
            
        except Exception as e:
            print(f"WARNING: GPU moving average failed: {e}, using CPU")
    
    # CPU fallback
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal, kernel, mode='same')

def gpu_peak_detection(signal: np.ndarray, height: float = None, 
                      distance: int = None, prominence: float = None) -> np.ndarray:
    """GPU-accelerated peak detection."""
    if gpu_accel.gpu_available:
        try:
            # Move signal to GPU
            gpu_signal = gpu_accel.to_gpu(signal)
            
            # Use CuPy's signal processing for peak detection
            # Note: cupyx.scipy.signal.find_peaks might not be available in all versions
            # So we'll implement a basic peak detection algorithm
            
            # Calculate first derivative
            diff = cp.diff(gpu_signal)
            
            # Find zero crossings (peaks)
            peaks = cp.where((diff[:-1] > 0) & (diff[1:] < 0))[0] + 1
            
            # Apply height filter if specified
            if height is not None:
                peaks = peaks[gpu_signal[peaks] > height]
            
            # Apply distance filter if specified
            if distance is not None:
                filtered_peaks = []
                last_peak = -distance
                for peak in peaks:
                    if peak - last_peak >= distance:
                        filtered_peaks.append(peak)
                        last_peak = peak
                peaks = cp.array(filtered_peaks)
            
            # Move result back to CPU
            return gpu_accel.to_cpu(peaks)
            
        except Exception as e:
            print(f"WARNING: GPU peak detection failed: {e}, using CPU")
    
    # CPU fallback
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(signal, height=height, distance=distance, prominence=prominence)
    return peaks

def gpu_downsample(signal: np.ndarray, factor: int) -> np.ndarray:
    """GPU-accelerated downsampling."""
    if factor <= 1:
        return signal
    
    if gpu_accel.gpu_available:
        try:
            # Move signal to GPU
            gpu_signal = gpu_accel.to_gpu(signal)
            
            # Simple downsampling by taking every nth sample
            downsampled = gpu_signal[::factor]
            
            # Move result back to CPU
            return gpu_accel.to_cpu(downsampled)
            
        except Exception as e:
            print(f"WARNING: GPU downsampling failed: {e}, using CPU")
    
    # CPU fallback
    return signal[::factor]

def optimize_gpu_processing(data_size_mb: float) -> dict:
    """Optimize GPU processing parameters based on data size."""
    recommendations = {
        "use_gpu": False,
        "batch_size": 1,
        "memory_strategy": "conservative",
        "downsample_factor": 1
    }
    
    if not gpu_accel.gpu_available:
        recommendations["memory_strategy"] = "cpu_only"
        return recommendations
    
    # Get current GPU memory status
    device_info = gpu_accel.get_device_info()
    free_memory_gb = device_info.get("memory_free_gb", 0)
    
    # GPU memory usage recommendations
    if data_size_mb < 100:  # Small data
        recommendations["use_gpu"] = True
        recommendations["batch_size"] = 1
        recommendations["memory_strategy"] = "aggressive"
    elif data_size_mb < 500:  # Medium data
        recommendations["use_gpu"] = True
        recommendations["batch_size"] = 2
        recommendations["memory_strategy"] = "balanced"
    elif data_size_mb < free_memory_gb * 800:  # Large data but fits in GPU
        recommendations["use_gpu"] = True
        recommendations["batch_size"] = 4
        recommendations["memory_strategy"] = "conservative"
        recommendations["downsample_factor"] = 2
    else:  # Very large data
        recommendations["use_gpu"] = False
        recommendations["memory_strategy"] = "cpu_fallback"
        recommendations["downsample_factor"] = 4
    
    return recommendations

def benchmark_gpu_performance():
    """Benchmark GPU vs CPU performance."""
    results = {
        "gpu_available": gpu_accel.gpu_available,
        "tests": {}
    }
    
    # Test data
    test_sizes = [1000, 10000, 100000]
    
    for size in test_sizes:
        test_data = np.random.randn(size).astype(np.float32)
        
        # Test filtering
        import time
        
        # CPU timing
        start = time.time()
        from signal_processing import butter_filter
        cpu_result = butter_filter(test_data, 10.0, 1000.0, 'low', 2)
        cpu_time = time.time() - start
        
        # GPU timing
        if gpu_accel.gpu_available:
            start = time.time()
            gpu_result = gpu_butter_filter(test_data, 10.0, 1000.0, 'low', 2)
            gpu_time = time.time() - start
            
            speedup = cpu_time / gpu_time if gpu_time > 0 else 0
        else:
            gpu_time = 0
            speedup = 0
        
        results["tests"][f"filter_{size}"] = {
            "cpu_time": cpu_time,
            "gpu_time": gpu_time,
            "speedup": speedup
        }
    
    return results

# Initialize GPU processing on import
if __name__ == "__main__":
    # Run benchmark if called directly
    print("=== GPU Processing Benchmark ===")
    benchmark_results = benchmark_gpu_performance()
    
    for test_name, result in benchmark_results["tests"].items():
        print(f"{test_name}: CPU={result['cpu_time']:.4f}s, GPU={result['gpu_time']:.4f}s, "
              f"Speedup={result['speedup']:.2f}x")
else:
    print(f"GPU processing module loaded - GPU available: {gpu_accel.gpu_available}")