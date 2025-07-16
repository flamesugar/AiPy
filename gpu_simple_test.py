#!/usr/bin/env python3
"""
Simple GPU test to isolate the issue
"""

print("=== GPU Import Test ===")

# Test 1: Import CuPy first, before any other imports
print("Test 1: Direct CuPy import")
try:
    import cupy as cp
    print(f"SUCCESS: CuPy imported, devices: {cp.cuda.runtime.getDeviceCount()}")
    cupy_works = True
except Exception as e:
    print(f"FAILED: {e}")
    cupy_works = False

# Test 2: Import after numpy and warnings
print("\nTest 2: After numpy/warnings import")
try:
    import numpy as np
    import warnings
    import cupy as cp2
    print(f"SUCCESS: CuPy after numpy, devices: {cp2.cuda.runtime.getDeviceCount()}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 3: Import after sys and os
print("\nTest 3: After sys/os import")
try:
    import sys
    import os
    import cupy as cp3
    print(f"SUCCESS: CuPy after sys/os, devices: {cp3.cuda.runtime.getDeviceCount()}")
except Exception as e:
    print(f"FAILED: {e}")

# Test 4: Import after numba
print("\nTest 4: After numba import")
try:
    import numba
    from numba import cuda, jit
    import cupy as cp4
    print(f"SUCCESS: CuPy after numba, devices: {cp4.cuda.runtime.getDeviceCount()}")
except Exception as e:
    print(f"FAILED: {e}")

print("\n=== Test Complete ===")