# file: signal_processing.py

import numpy as np
import numpy.polynomial.polynomial as poly
from scipy.signal import butter, sosfiltfilt, savgol_filter
from scipy.stats import linregress
from scipy.interpolate import interp1d
from scipy.ndimage import median_filter

# GPU acceleration support
try:
    from gpu_processing import (
        gpu_butter_filter, gpu_correlation_matrix, gpu_fft_analysis,
        gpu_moving_average, gpu_peak_detection, gpu_downsample,
        optimize_gpu_processing, gpu_accel
    )
    GPU_AVAILABLE = True
    print("GPU acceleration available for signal processing")
except ImportError as e:
    GPU_AVAILABLE = False
    print(f"WARNING: GPU acceleration not available: {e}")

def butter_filter(data, cutoff, fs, btype='low', order=2, zero_phase=True):
    """Applies a Butterworth filter with robust error handling and GPU acceleration."""
    try:
        # Input validation - fast early returns
        if data is None or len(data) == 0:
            return data
        
        # Convert to numpy array and ensure it's contiguous (optimized)
        if not isinstance(data, np.ndarray):
            data = np.asarray(data, dtype=np.float64)
        elif data.dtype != np.float64:
            data = data.astype(np.float64)
        
        if not data.flags.c_contiguous:
            data = np.ascontiguousarray(data)
        
        # Fast finite check using numpy's built-in optimized functions
        if not np.all(np.isfinite(data)):
            print("Warning: NaN or inf values detected in data, replacing with zeros")
            data = np.where(np.isfinite(data), data, 0.0)
        
        # Validate cutoff frequencies (optimized)
        if isinstance(cutoff, (list, tuple, np.ndarray)):
            cutoff = np.asarray(cutoff)
            if np.any(cutoff <= 0) or np.any(cutoff >= fs/2):
                print(f"Warning: Invalid cutoff frequencies {cutoff} for fs={fs}")
                return data
        else:
            if cutoff <= 0 or cutoff >= fs/2:
                print(f"Warning: Invalid cutoff frequency {cutoff} for fs={fs}")
                return data
        
        # Validate minimum data length for filtering
        min_length = max(order * 6, 9)
        if len(data) < min_length:
            print(f"Warning: Data too short for filtering ({len(data)} < {min_length}), returning original")
            return data
        
        # GPU acceleration decision based on data size
        data_size_mb = data.nbytes / (1024 * 1024)
        use_gpu = GPU_AVAILABLE and data_size_mb > 10  # Use GPU for data > 10MB
        
        if use_gpu:
            try:
                print(f"Using GPU acceleration for filtering ({data_size_mb:.1f}MB)")
                return gpu_butter_filter(data, cutoff, fs, btype, order)
            except Exception as e:
                print(f"WARNING: GPU filtering failed: {e}, falling back to CPU")
        
        # CPU implementation (fallback or for small data)
        # Calculate normalized cutoff frequencies (optimized)
        nyq = 0.5 * fs
        if isinstance(cutoff, (list, tuple, np.ndarray)):
            normal_cutoff = cutoff / nyq
        else:
            normal_cutoff = cutoff / nyq
        
        # Create filter with error handling
        try:
            sos = butter(order, normal_cutoff, btype=btype, analog=False, output='sos')
        except Exception as e:
            print(f"Error creating filter: {e}")
            return data
        
        # Calculate appropriate padlen (optimized)
        if isinstance(cutoff, (list, tuple, np.ndarray)):
            min_cutoff = np.min(cutoff)
        else:
            min_cutoff = cutoff
        
        # Optimized padlen calculation
        padlen = min(len(data) - 1, max(1, int(3 * fs / min_cutoff))) if min_cutoff > 0 else 0
        
        # Apply filter with error handling (optimized)
        try:
            filtered_data = sosfiltfilt(sos, data, padlen=padlen)
        except Exception as e:
            print(f"Error applying filter: {e}")
            return data
        
        # Fast finite check on output
        if not np.all(np.isfinite(filtered_data)):
            print("Warning: Filter produced NaN or inf values, returning original data")
            return data
        
        return filtered_data
        
    except Exception as e:
        print(f"Unexpected error in butter_filter: {e}")
        return data  # Return original data on any error

def fit_bleaching_correction(signal, control):
    """Fits the control signal to the data signal using linear regression."""
    if control is None or len(control) == 0 or signal is None or len(signal) == 0:
        return np.zeros_like(signal)
    if np.std(control) < 1e-9 or np.std(signal) < 1e-9:
        scale_factor = np.mean(signal) / (np.mean(control) if np.mean(control) > 1e-9 else 1.0)
        return control * scale_factor
    slope, intercept, _, _, _ = linregress(control, signal)
    return slope * control + intercept

def detect_artifacts(control_signal, threshold=3.0):
    """Detects artifacts based on deviation from the median in the control signal."""
    if control_signal is None or len(control_signal) < 2:
        return np.zeros_like(control_signal, dtype=bool)
    
    median_val = np.median(control_signal)
    # Median Absolute Deviation (MAD) is more robust to outliers than standard deviation
    mad = np.median(np.abs(control_signal - median_val))
    # Constant to convert MAD to an equivalent standard deviation
    mad_to_std = 1.4826
    
    # Identify points that are more than `threshold` standard deviations from the median
    artifact_mask = np.abs(control_signal - median_val) > threshold * mad * mad_to_std
    return artifact_mask

def advanced_denoise_signal(signal, time, artifact_mask, control_signal=None, aggressive_mode=False):
    """
    Enhanced denoising using interpolation and optional control signal correction.
    """
    if not np.any(artifact_mask):
        return signal.copy()
        
    denoised_signal = signal.copy()
    valid_indices = np.where(~artifact_mask)[0]

    if len(valid_indices) < 2: # Not enough good data to interpolate from
        return signal.copy()

    # Create an interpolation function based on the "good" data points
    interp_func = interp1d(
        time[valid_indices], signal[valid_indices],
        kind='linear', bounds_error=False, fill_value='extrapolate'
    )
    
    artifact_indices = np.where(artifact_mask)[0]
    
    # Use control signal for a more sophisticated correction if available and desired
    if aggressive_mode and control_signal is not None and len(valid_indices) > 10:
        try:
            # Fit control to signal on the clean parts
            slope, intercept, _, _, _ = linregress(control_signal[valid_indices], signal[valid_indices])
            # Predict what the signal should have been based on the control
            predicted_signal = slope * control_signal[artifact_indices] + intercept
            # Blend the prediction with the simple interpolation for smoother results
            interp_values = interp_func(time[artifact_indices])
            denoised_signal[artifact_indices] = 0.7 * predicted_signal + 0.3 * interp_values
        except Exception:
            # Fallback to simple interpolation if regression fails
            denoised_signal[artifact_indices] = interp_func(time[artifact_indices])
    else:
        # Default to simple interpolation over the artifact regions
        denoised_signal[artifact_indices] = interp_func(time[artifact_indices])
        
    return denoised_signal

def process_data_pipeline(
    time_raw, signal_raw, control_raw, fs,
    low_cutoff=0.001, high_cutoff=5.0, drift_correction=True, drift_degree=2,
    downsample_factor=1, edge_protection=True,
    filter_type='Bandpass', filter_order=2, zero_phase=True, filter_raw_signals=True
):
    """
    Full data processing pipeline with robust error handling and memory management.
    """
    try:
        # Input validation
        if signal_raw is None or len(signal_raw) == 0:
            print("Error: Empty signal_raw passed to processing pipeline")
            return None, None, None, None, None, None
        
        # Validate parameters
        if fs <= 0:
            print(f"Error: Invalid sampling rate {fs}")
            return None, None, None, None, None, None
        
        if low_cutoff >= high_cutoff:
            print(f"Error: Invalid cutoff frequencies: low={low_cutoff}, high={high_cutoff}")
            return None, None, None, None, None, None
        
        # Memory management - force garbage collection
        import gc
        gc.collect()

        # Convert to numpy arrays with error handling
        try:
            processed_signal = np.asarray(signal_raw, dtype=np.float64)
            if not np.all(np.isfinite(processed_signal)):
                print("Warning: Invalid values in signal_raw, cleaning")
                processed_signal = np.where(np.isfinite(processed_signal), processed_signal, 0.0)
        except Exception as e:
            print(f"Error converting signal_raw: {e}")
            return None, None, None, None, None, None
        
        try:
            processed_control = np.asarray(control_raw, dtype=np.float64) if control_raw is not None else None
            if processed_control is not None and not np.all(np.isfinite(processed_control)):
                print("Warning: Invalid values in control_raw, cleaning")
                processed_control = np.where(np.isfinite(processed_control), processed_control, 0.0)
        except Exception as e:
            print(f"Error converting control_raw: {e}")
            processed_control = None
        
        # Artifact detection with error handling
        try:
            artifact_mask = detect_artifacts(processed_control) if processed_control is not None else np.zeros_like(processed_signal, dtype=bool)
        except Exception as e:
            print(f"Error in artifact detection: {e}")
            artifact_mask = np.zeros_like(processed_signal, dtype=bool)

        # Keep original raw signals for comparison
        original_signal = processed_signal.copy()
        original_control = processed_control.copy() if processed_control is not None else None
    
        # --- Filtering ---
        try:
            if filter_type == 'Lowpass':
                processed_signal = butter_filter(processed_signal, high_cutoff, fs, btype='low', order=filter_order, zero_phase=zero_phase)
                if processed_control is not None:
                    processed_control = butter_filter(processed_control, high_cutoff, fs, btype='low', order=filter_order, zero_phase=zero_phase)
            elif filter_type == 'Highpass':
                processed_signal = butter_filter(processed_signal, low_cutoff, fs, btype='high', order=filter_order, zero_phase=zero_phase)
                if processed_control is not None:
                    processed_control = butter_filter(processed_control, low_cutoff, fs, btype='high', order=filter_order, zero_phase=zero_phase)
            elif filter_type == 'Bandpass':
                processed_signal = butter_filter(processed_signal, [low_cutoff, high_cutoff], fs, btype='bandpass', order=filter_order, zero_phase=zero_phase)
                if processed_control is not None:
                    processed_control = butter_filter(processed_control, [low_cutoff, high_cutoff], fs, btype='bandpass', order=filter_order, zero_phase=zero_phase)
            elif filter_type == 'Bandstop':
                processed_signal = butter_filter(processed_signal, [low_cutoff, high_cutoff], fs, btype='bandstop', order=filter_order, zero_phase=zero_phase)
                if processed_control is not None:
                    processed_control = butter_filter(processed_control, [low_cutoff, high_cutoff], fs, btype='bandstop', order=filter_order, zero_phase=zero_phase)
        except Exception as e:
            print(f"Error in filtering stage: {e}")
            # Keep original signals if filtering fails
            processed_signal = original_signal.copy()
            processed_control = original_control.copy() if original_control is not None else None

        # --- Motion Correction ---
        try:
            if processed_control is not None:
                motion_corrected = processed_signal - fit_bleaching_correction(processed_signal, processed_control)
            else:
                motion_corrected = processed_signal
        except Exception as e:
            print(f"Error in motion correction: {e}")
            motion_corrected = processed_signal
        
        # --- Drift Correction ---
        try:
            if drift_correction:
                time_norm = np.linspace(0, 1, len(motion_corrected))
                coeffs = poly.polyfit(time_norm, motion_corrected, drift_degree)
                drift_curve = poly.polyval(time_norm, coeffs)
                detrended_signal = motion_corrected - drift_curve
            else:
                detrended_signal = motion_corrected
                drift_curve = None
        except Exception as e:
            print(f"Error in drift correction: {e}")
            detrended_signal = motion_corrected
            drift_curve = None
        
        # --- dF/F ---
        try:
            f0 = np.percentile(detrended_signal, 10)
            f0 = max(abs(f0), 1e-9)
            dff_signal = (detrended_signal - f0) / f0 * 100
        except Exception as e:
            print(f"Error in dF/F calculation: {e}")
            dff_signal = np.zeros_like(detrended_signal)
        
        # --- Downsampling ---
        try:
            factor = int(max(1, downsample_factor))
            time_ds = time_raw[::factor]
            dff_ds = dff_signal[::factor]
            
            # Return filtered or original raw signals based on user choice
            if filter_raw_signals:
                raw1_ds = processed_signal[::factor]
                raw2_ds = processed_control[::factor] if processed_control is not None else None
                print(f"Filter applied to raw signals: {filter_type} ({low_cutoff}-{high_cutoff} Hz)")
            else:
                raw1_ds = original_signal[::factor]
                raw2_ds = original_control[::factor] if original_control is not None else None
                print(f"Filter NOT applied to raw signals (using original raw signals)")
            
            drift_ds = drift_curve[::factor] if drift_curve is not None else None
            artifact_mask_ds = artifact_mask[::factor]
            
            # Force garbage collection
            gc.collect()
            
            return time_ds, dff_ds, raw1_ds, raw2_ds, drift_ds, artifact_mask_ds
        except Exception as e:
            print(f"Error in downsampling: {e}")
            return None, None, None, None, None, None
        
    except Exception as e:
        print(f"Critical error in process_data_pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None, None, None