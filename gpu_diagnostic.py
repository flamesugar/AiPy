#!/usr/bin/env python3
"""
GPU Diagnostic Script for CuPy and CUDA Setup
"""
import sys
import platform
import subprocess
import importlib.util

def check_python_version():
    """Check Python version compatibility."""
    print("=== Python Version ===")
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print()

def check_cuda_installation():
    """Check CUDA installation."""
    print("=== CUDA Installation ===")
    try:
        # Try to run nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ NVIDIA driver found")
            print("NVIDIA-SMI output:")
            print(result.stdout)
        else:
            print("✗ NVIDIA driver not found or not working")
            print("Error:", result.stderr)
    except FileNotFoundError:
        print("✗ nvidia-smi command not found")
        print("CUDA/NVIDIA drivers may not be installed")
    except subprocess.TimeoutExpired:
        print("✗ nvidia-smi command timed out")
    except Exception as e:
        print(f"✗ Error running nvidia-smi: {e}")
    
    print()
    
    # Check CUDA version
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ CUDA compiler found")
            print("NVCC output:")
            print(result.stdout)
        else:
            print("✗ CUDA compiler (nvcc) not found")
    except FileNotFoundError:
        print("✗ nvcc command not found")
        print("CUDA toolkit may not be installed")
    except Exception as e:
        print(f"✗ Error running nvcc: {e}")
    
    print()

def check_cupy_installation():
    """Check CuPy installation and compatibility."""
    print("=== CuPy Installation ===")
    
    # Check if CuPy is installed
    try:
        import cupy
        print(f"✓ CuPy found: version {cupy.__version__}")
        
        # Check CuPy CUDA version
        try:
            cuda_version = cupy.cuda.runtime.runtimeGetVersion()
            print(f"✓ CuPy CUDA runtime version: {cuda_version}")
        except Exception as e:
            print(f"✗ Error getting CuPy CUDA version: {e}")
        
        # Test basic CuPy functionality
        try:
            # Test GPU availability
            device_count = cupy.cuda.runtime.getDeviceCount()
            print(f"✓ GPU devices found: {device_count}")
            
            if device_count > 0:
                # Test basic operations
                x = cupy.array([1, 2, 3, 4, 5])
                y = cupy.sum(x)
                print(f"✓ Basic CuPy operations work: sum([1,2,3,4,5]) = {y}")
                
                # Test memory info
                meminfo = cupy.cuda.runtime.memGetInfo()
                free_mem = meminfo[0] / 1024**3
                total_mem = meminfo[1] / 1024**3
                print(f"✓ GPU memory: {free_mem:.1f}GB free / {total_mem:.1f}GB total")
                
                # Test device properties
                for i in range(device_count):
                    props = cupy.cuda.runtime.getDeviceProperties(i)
                    print(f"✓ GPU {i}: {props['name'].decode()}")
                    
        except Exception as e:
            print(f"✗ CuPy GPU operations failed: {e}")
            print("This suggests a CUDA/CuPy compatibility issue")
            
    except ImportError as e:
        print(f"✗ CuPy not found: {e}")
        print("Try installing CuPy with: pip install cupy-cuda12x")
    except Exception as e:
        print(f"✗ Error importing CuPy: {e}")
    
    print()

def check_cupy_variants():
    """Check which CuPy variants are available."""
    print("=== CuPy Variants Check ===")
    
    cupy_variants = [
        'cupy-cuda12x',
        'cupy-cuda11x', 
        'cupy-cuda10x',
        'cupy'
    ]
    
    for variant in cupy_variants:
        try:
            result = subprocess.run([sys.executable, '-c', f'import {variant.replace("-", "_")}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✓ {variant} is available")
            else:
                print(f"✗ {variant} not available")
        except Exception as e:
            print(f"✗ Error checking {variant}: {e}")
    
    print()

def check_cuda_path():
    """Check CUDA environment variables."""
    print("=== CUDA Environment ===")
    
    import os
    cuda_path = os.environ.get('CUDA_PATH')
    cuda_home = os.environ.get('CUDA_HOME')
    
    if cuda_path:
        print(f"✓ CUDA_PATH: {cuda_path}")
    else:
        print("✗ CUDA_PATH not set")
    
    if cuda_home:
        print(f"✓ CUDA_HOME: {cuda_home}")
    else:
        print("✗ CUDA_HOME not set")
    
    # Check PATH for CUDA
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    cuda_in_path = any('cuda' in dir.lower() for dir in path_dirs)
    
    if cuda_in_path:
        print("✓ CUDA directories found in PATH")
    else:
        print("✗ No CUDA directories in PATH")
    
    print()

def suggest_solutions():
    """Suggest solutions based on the diagnostic results."""
    print("=== Suggested Solutions ===")
    
    print("1. Install the correct CuPy version for your CUDA:")
    print("   - For CUDA 12.x: pip install cupy-cuda12x")
    print("   - For CUDA 11.x: pip install cupy-cuda11x")
    print("   - For CUDA 10.x: pip install cupy-cuda10x")
    print()
    
    print("2. If you don't have CUDA installed:")
    print("   - Download and install CUDA from https://developer.nvidia.com/cuda-downloads")
    print("   - Make sure to install the version that matches your GPU")
    print()
    
    print("3. If you have multiple CUDA versions:")
    print("   - Uninstall conflicting CuPy versions: pip uninstall cupy")
    print("   - Install the correct version for your CUDA")
    print()
    
    print("4. Alternative: Use CPU-only mode:")
    print("   - The application will work fine with CPU processing")
    print("   - GPU acceleration is optional for performance")
    print()

def main():
    """Run complete GPU diagnostic."""
    print("GPU Acceleration Diagnostic Tool")
    print("=" * 50)
    print()
    
    check_python_version()
    check_cuda_installation()
    check_cupy_installation()
    check_cupy_variants()
    check_cuda_path()
    suggest_solutions()
    
    print("Diagnostic complete!")
    print("Share this output to get help with GPU setup.")

if __name__ == "__main__":
    main()