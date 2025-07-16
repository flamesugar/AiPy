#!/usr/bin/env python3
"""
Test script to verify the robustness of the enhanced filter implementation.
"""

import numpy as np
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signal_processing import butter_filter, process_data_pipeline

def test_filter_robustness():
    """Test the filter with various edge cases and problematic inputs."""
    
    print("=== Testing Filter Robustness ===")
    
    # Test parameters
    fs = 1000.0
    
    # Test 1: Normal signal
    print("\n1. Testing normal signal...")
    t = np.linspace(0, 1, 1000)
    normal_signal = np.sin(2 * np.pi * 5 * t) + 0.1 * np.random.randn(1000)
    filtered = butter_filter(normal_signal, 10, fs, btype='low')
    print(f"   Normal signal: {len(normal_signal)} -> {len(filtered)} samples")
    
    # Test 2: Signal with NaN values
    print("\n2. Testing signal with NaN values...")
    nan_signal = normal_signal.copy()
    nan_signal[100:110] = np.nan
    filtered_nan = butter_filter(nan_signal, 10, fs, btype='low')
    print(f"   NaN signal: {len(nan_signal)} -> {len(filtered_nan)} samples")
    
    # Test 3: Signal with inf values
    print("\n3. Testing signal with inf values...")
    inf_signal = normal_signal.copy()
    inf_signal[200:210] = np.inf
    filtered_inf = butter_filter(inf_signal, 10, fs, btype='low')
    print(f"   Inf signal: {len(inf_signal)} -> {len(filtered_inf)} samples")
    
    # Test 4: Very short signal
    print("\n4. Testing very short signal...")
    short_signal = np.array([1, 2, 3, 4, 5])
    filtered_short = butter_filter(short_signal, 10, fs, btype='low')
    print(f"   Short signal: {len(short_signal)} -> {len(filtered_short)} samples")
    
    # Test 5: Empty signal
    print("\n5. Testing empty signal...")
    empty_signal = np.array([])
    filtered_empty = butter_filter(empty_signal, 10, fs, btype='low')
    print(f"   Empty signal: {len(empty_signal)} -> {len(filtered_empty)} samples")
    
    # Test 6: Invalid cutoff frequency
    print("\n6. Testing invalid cutoff frequency...")
    filtered_invalid = butter_filter(normal_signal, 600, fs, btype='low')  # 600 Hz > Nyquist
    print(f"   Invalid cutoff: {len(normal_signal)} -> {len(filtered_invalid)} samples")
    
    # Test 7: Bandpass filter
    print("\n7. Testing bandpass filter...")
    filtered_bp = butter_filter(normal_signal, [1, 50], fs, btype='bandpass')
    print(f"   Bandpass filter: {len(normal_signal)} -> {len(filtered_bp)} samples")
    
    # Test 8: Multiple rapid filter applications (stress test)
    print("\n8. Testing multiple rapid filter applications...")
    test_signal = normal_signal.copy()
    for i in range(10):
        test_signal = butter_filter(test_signal, 10 + i, fs, btype='low')
        if i % 3 == 0:
            print(f"   Iteration {i+1}: {len(test_signal)} samples")
    
    print("\n=== Filter Robustness Tests Completed ===")
    
def test_pipeline_robustness():
    """Test the full processing pipeline with edge cases."""
    
    print("\n=== Testing Pipeline Robustness ===")
    
    # Generate test data
    fs = 1000.0
    t = np.linspace(0, 10, 10000)
    signal = np.sin(2 * np.pi * 5 * t) + 0.1 * np.random.randn(10000)
    control = np.sin(2 * np.pi * 3 * t) + 0.05 * np.random.randn(10000)
    
    # Test 1: Normal pipeline
    print("\n1. Testing normal pipeline...")
    result = process_data_pipeline(
        t, signal, control, fs,
        low_cutoff=0.1, high_cutoff=50.0,
        filter_type='Bandpass',
        downsample_factor=10
    )
    if result[0] is not None:
        print(f"   Normal pipeline: {len(result[0])} samples processed")
    else:
        print("   Normal pipeline: Failed")
    
    # Test 2: Pipeline with None control
    print("\n2. Testing pipeline with None control...")
    result = process_data_pipeline(
        t, signal, None, fs,
        low_cutoff=0.1, high_cutoff=50.0,
        filter_type='Bandpass',
        downsample_factor=10
    )
    if result[0] is not None:
        print(f"   None control pipeline: {len(result[0])} samples processed")
    else:
        print("   None control pipeline: Failed")
    
    # Test 3: Pipeline with extreme parameters
    print("\n3. Testing pipeline with extreme parameters...")
    result = process_data_pipeline(
        t, signal, control, fs,
        low_cutoff=0.001, high_cutoff=400.0,  # High cutoff near Nyquist
        filter_type='Bandpass',
        downsample_factor=100
    )
    if result[0] is not None:
        print(f"   Extreme parameters: {len(result[0])} samples processed")
    else:
        print("   Extreme parameters: Failed")
    
    print("\n=== Pipeline Robustness Tests Completed ===")

if __name__ == "__main__":
    test_filter_robustness()
    test_pipeline_robustness()
    print("\n=== All Tests Completed Successfully ===")