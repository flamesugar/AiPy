import numpy as np

def calculate_psth(spike_times, event_times, time_window=(-1, 1), bin_size=0.01):
    """
    Calculate Peri-Stimulus Time Histogram (PSTH)
    
    Args:
        spike_times (np.ndarray): Array of spike times
        event_times (np.ndarray): Array of event times
        time_window (tuple): Time window around events (pre, post) in seconds
        bin_size (float): Size of time bins in seconds
        
    Returns:
        tuple: (time_bins, psth_values)
    """
    # Create time bins
    time_bins = np.arange(time_window[0], time_window[1] + bin_size, bin_size)
    
    # Initialize PSTH array
    psth = np.zeros(len(time_bins) - 1)
    
    # For each event
    for event_time in event_times:
        # Get spikes within window
        window_spikes = spike_times[
            (spike_times >= event_time + time_window[0]) &
            (spike_times <= event_time + time_window[1])
        ]
        
        # Convert to relative times
        relative_times = window_spikes - event_time
        
        # Bin the spikes
        hist, _ = np.histogram(relative_times, bins=time_bins)
        psth += hist
    
    # Normalize by number of events
    psth = psth / len(event_times)
    
    return time_bins[:-1], psth

def calculate_mean_psth(spike_times, event_times, time_window=(-1, 1), 
                       bin_size=0.01, trials=None):
    """
    Calculate mean PSTH across trials
    
    Args:
        spike_times (np.ndarray): Array of spike times
        event_times (np.ndarray): Array of event times
        time_window (tuple): Time window around events (pre, post) in seconds
        bin_size (float): Size of time bins in seconds
        trials (np.ndarray): Trial numbers for each spike (optional)
        
    Returns:
        tuple: (time_bins, mean_psth, std_psth)
    """
    if trials is None:
        # If no trial information, treat all spikes as one trial
        time_bins, psth = calculate_psth(spike_times, event_times, 
                                       time_window, bin_size)
        return time_bins, psth, np.zeros_like(psth)
    
    # Calculate PSTH for each trial
    trial_psths = []
    unique_trials = np.unique(trials)
    
    for trial in unique_trials:
        trial_spikes = spike_times[trials == trial]
        _, psth = calculate_psth(trial_spikes, event_times, 
                               time_window, bin_size)
        trial_psths.append(psth)
    
    # Calculate mean and std across trials
    mean_psth = np.mean(trial_psths, axis=0)
    std_psth = np.std(trial_psths, axis=0)
    
    time_bins = np.arange(time_window[0], time_window[1] + bin_size, bin_size)
    return time_bins[:-1], mean_psth, std_psth 