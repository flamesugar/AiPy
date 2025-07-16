# file: analysis/peak_analysis.py

import numpy as np
from scipy.signal import find_peaks
from scipy.integrate import trapezoid

def find_peaks_valleys(signal, time, fs, prominence=1.0, width_s=None, distance_s=None):
    """
    Finds peaks and valleys in a signal. Returns separate dictionaries for peaks and valleys.
    """
    if signal is None or len(signal) == 0:
        return {}, {}
    width_samples = int(width_s * fs) if width_s is not None and width_s > 0 else None
    distance_samples = int(distance_s * fs) if distance_s is not None and distance_s > 0 else None

    peak_indices, _ = find_peaks(signal, prominence=prominence, width=width_samples, distance=distance_samples)
    valley_indices, _ = find_peaks(-signal, prominence=prominence, width=width_samples, distance=distance_samples)
    
    return {
        'indices': peak_indices, 'times': time[peak_indices], 'heights': signal[peak_indices]
    }, {
        'indices': valley_indices, 'times': time[valley_indices], 'depths': signal[valley_indices]
    }

def calculate_peak_metrics(peak_data, valley_data, signal, time):
    """Calculates detailed metrics for each peak based on surrounding valleys."""
    if not peak_data or not peak_data.get('indices').any(): return None
    
    metrics = {'area': [], 'fwhm': [], 'rise_time': [], 'decay_time': []}
    peak_indices = peak_data['indices']
    valley_indices = valley_data['indices'] if valley_data and valley_data.get('indices').any() else np.array([0, len(signal)-1])

    for peak_idx in peak_indices:
        try:
            preceding_valleys = valley_indices[valley_indices < peak_idx]
            following_valleys = valley_indices[valley_indices > peak_idx]
            if not preceding_valleys.any() or not following_valleys.any(): raise ValueError("Peak not enclosed.")
            
            pre_v_idx, post_v_idx = preceding_valleys[-1], following_valleys[0]
            base_level = min(signal[pre_v_idx], signal[post_v_idx])
            peak_height = signal[peak_idx]
            half_height = base_level + (peak_height - base_level) / 2.0
            
            # Find indices for FWHM
            rise_indices = np.where(signal[pre_v_idx:peak_idx+1] >= half_height)[0] + pre_v_idx
            decay_indices = np.where(signal[peak_idx:post_v_idx+1] >= half_height)[0] + peak_idx
            if not rise_indices.any() or not decay_indices.any(): raise ValueError("FWHM not found.")
            
            rise_t_idx, decay_t_idx = rise_indices[0], decay_indices[-1]
            
            metrics['fwhm'].append(time[decay_t_idx] - time[rise_t_idx])
            metrics['rise_time'].append(time[peak_idx] - time[rise_t_idx])
            metrics['decay_time'].append(time[decay_t_idx] - time[peak_idx])
            
            # Area calculation
            time_segment = time[pre_v_idx:post_v_idx+1]
            signal_segment = signal[pre_v_idx:post_v_idx+1]
            metrics['area'].append(trapezoid(signal_segment - base_level, time_segment))
        except (ValueError, IndexError):
            for k in metrics: metrics[k].append(np.nan)
            
    return metrics

def calculate_valley_metrics(peak_data, valley_data, signal, time):
    """Calculates metrics for each valley, focusing on width and area above."""
    if not valley_data or not valley_data.get('indices').any(): return None
    
    metrics = {'area_above': [], 'fwhm': []}
    valley_indices = valley_data['indices']
    peak_indices = peak_data['indices'] if peak_data and peak_data.get('indices').any() else np.array([0, len(signal)-1])

    for valley_idx in valley_indices:
        try:
            preceding_peaks = peak_indices[peak_indices < valley_idx]
            following_peaks = peak_indices[peak_indices > valley_idx]
            if not preceding_peaks.any() or not following_peaks.any(): raise ValueError("Valley not enclosed.")
            
            pre_p_idx, post_p_idx = preceding_peaks[-1], following_peaks[0]
            peak_level = max(signal[pre_p_idx], signal[post_p_idx])
            valley_depth = signal[valley_idx]
            half_depth = peak_level - (peak_level - valley_depth) / 2.0
            
            # Find indices for FWHM
            rise_indices = np.where(signal[pre_p_idx:valley_idx+1] <= half_depth)[0] + pre_p_idx
            decay_indices = np.where(signal[valley_idx:post_p_idx+1] <= half_depth)[0] + valley_idx
            if not rise_indices.any() or not decay_indices.any(): raise ValueError("FWHM not found.")

            metrics['fwhm'].append(time[decay_indices[-1]] - time[rise_indices[0]])
            
            # Area calculation
            time_segment = time[pre_p_idx:post_p_idx+1]
            signal_segment = signal[pre_p_idx:post_p_idx+1]
            metrics['area_above'].append(trapezoid(peak_level - signal_segment, time_segment))
        except (ValueError, IndexError):
            for k in metrics: metrics[k].append(np.nan)
            
    return metrics

def calculate_intervals(times):
    """Calculates intervals between a sorted list of event times."""
    if times is None or len(times) < 2:
        return None
    intervals = np.diff(np.sort(times))
    return {
        'intervals': intervals,
        'count': len(intervals),
        'mean': np.mean(intervals),
        'median': np.median(intervals),
        'std': np.std(intervals),
        'min': np.min(intervals),
        'max': np.max(intervals)
    }