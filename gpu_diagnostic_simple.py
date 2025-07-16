#!/usr/bin/env python3
"""
Simple GPU Diagnostic Script for CuPy and CUDA Setup
"""
import sys
import platform
import subprocess

def check_cuda_installation():
    """Check CUDA installation."""
    print("=== CUDA Installation ===")
    try:
        # Try to run nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("SUCCESS: NVIDIA driver found")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'CUDA Version' in line:
                    print(f"CUDA Version: {line.strip()}")
        else:
            print("ERROR: NVIDIA driver not found or not working")
    except FileNotFoundError:
        print("ERROR: nvidia-smi command not found")
        print("CUDA/NVIDIA drivers may not be installed")
    except Exception as e:
        print(f"ERROR: Error running nvidia-smi: {e}")
    
    print()

def check_cupy_installation():
    """Check CuPy installation and compatibility."""
    print("=== CuPy Installation ===")
    
    # Check if CuPy is installed
    try:
        import cupy
        print(f"SUCCESS: CuPy found: version {cupy.__version__}")
        
        # Check CuPy CUDA version
        try:
            cuda_version = cupy.cuda.runtime.runtimeGetVersion()
            print(f"SUCCESS: CuPy CUDA runtime version: {cuda_version}")
        except Exception as e:
            print(f"ERROR: Error getting CuPy CUDA version: {e}")
        
        # Test basic CuPy functionality
        try:
            # Test GPU availability
            device_count = cupy.cuda.runtime.getDeviceCount()
            print(f"SUCCESS: GPU devices found: {device_count}")
            
            if device_count > 0:
                # Test basic operations
                x = cupy.array([1, 2, 3, 4, 5])
                y = cupy.sum(x)
                print(f"SUCCESS: Basic CuPy operations work: sum([1,2,3,4,5]) = {y}")
                
                # Test memory info
                meminfo = cupy.cuda.runtime.memGetInfo()
                free_mem = meminfo[0] / 1024**3
                total_mem = meminfo[1] / 1024**3
                print(f"SUCCESS: GPU memory: {free_mem:.1f}GB free / {total_mem:.1f}GB total")
                
            else:
                print("ERROR: No GPU devices found")
                
        except Exception as e:
            print(f"ERROR: CuPy GPU operations failed: {e}")
            print("This suggests a CUDA/CuPy compatibility issue")
            
    except ImportError as e:
        print(f"ERROR: CuPy not found: {e}")
        print("Try installing CuPy with: pip install cupy-cuda12x")
    except Exception as e:
        print(f"ERROR: Error importing CuPy: {e}")
    
    print()

def check_installed_packages():
    """Check what CuPy packages are installed."""
    print("=== Installed CuPy Packages ===")
    
    import pkg_resources
    
    cupy_packages = []
    for package in pkg_resources.working_set:
        if 'cupy' in package.project_name.lower():
            cupy_packages.append(f"{package.project_name} {package.version}")
    
    if cupy_packages:
        print("Found CuPy packages:")
        for pkg in cupy_packages:
            print(f"  {pkg}")
    else:
        print("No CuPy packages found")
    
    print()

def suggest_solutions():
    """Suggest solutions based on the diagnostic results."""
    print("=== Suggested Solutions ===")
    
    print("1. Check your CUDA version and install matching CuPy:")
    print("   - For CUDA 12.x: pip uninstall cupy && pip install cupy-cuda12x")
    print("   - For CUDA 11.x: pip uninstall cupy && pip install cupy-cuda11x")
    print("   - For CUDA 10.x: pip uninstall cupy && pip install cupy-cuda10x")
    print()
    
    print("2. If you don't have CUDA installed:")
    print("   - Download CUDA from https://developer.nvidia.com/cuda-downloads")
    print("   - Install CUDA toolkit that matches your GPU")
    print()
    
    print("3. If you have NVIDIA GPU but no CUDA:")
    print("   - Install CUDA toolkit")
    print("   - Restart your computer")
    print("   - Install matching CuPy version")
    print()
    
    print("4. Quick fix commands to try:")
    print("   pip uninstall cupy cupy-cuda12x cupy-cuda11x cupy-cuda10x")
    print("   pip install cupy-cuda12x  # For most recent systems")
    print()

def main():
    """Run complete GPU diagnostic."""
    print("GPU Acceleration Diagnostic Tool")
    print("=" * 50)
    print()
    
    print(f"Python: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print()
    
    check_cuda_installation()
    check_installed_packages()
    check_cupy_installation()
    suggest_solutions()
    
    print("Diagnostic complete!")

if __name__ == "__main__":
    main()