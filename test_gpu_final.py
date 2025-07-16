#!/usr/bin/env python3
"""
Final GPU test script
"""
import sys
import numpy as np

print("=== Final GPU Test ===")
print("Testing CuPy directly...")

try:
    import cupy as cp
    device_count = cp.cuda.runtime.getDeviceCount()
    print(f"SUCCESS: CuPy works: {device_count} devices found")
    
    # Test basic GPU operations
    x = cp.array([1, 2, 3, 4, 5])
    y = cp.sum(x)
    print(f"SUCCESS: Basic operations work: sum = {y}")
    
    # Test GPU processing module
    print("\nTesting GPU processing module...")
    
    # Force reload to avoid cached import issues
    if 'gpu_processing' in sys.modules:
        del sys.modules['gpu_processing']
    
    import gpu_processing
    print(f"Initial GPU status: {gpu_processing.gpu_accel.gpu_available}")
    
    # Force CuPy initialization
    print("Forcing CuPy initialization...")
    cp_module, cupy_signal, cupy_ndimage = gpu_processing._get_cupy_modules()
    
    if cp_module is not None:
        print("SUCCESS: CuPy modules loaded successfully")
        # Force GPU accelerator initialization
        gpu_processing.gpu_accel._try_gpu_init()
        print(f"Final GPU status: {gpu_processing.gpu_accel.gpu_available}")
        
        # Test a GPU function
        print("Testing GPU filtering...")
        test_data = np.random.randn(1000).astype(np.float32)
        result = gpu_processing.gpu_butter_filter(test_data, 10.0, 1000.0, 'low', 2)
        print(f"SUCCESS: GPU filtering works: output shape = {result.shape}")
        
    else:
        print("ERROR: CuPy modules failed to load")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")