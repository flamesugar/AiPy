# file: data_io.py

import json
import numpy as np
import os
import traceback

def read_ppd_file(file_path):
    """
    Reads a .ppd file and returns a dictionary containing the header and data bytes.
    Includes comprehensive error handling.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.lower().endswith('.ppd'):
        raise ValueError("File must have a .ppd extension")

    try:
        with open(file_path, 'rb') as f:
            # First two bytes are the header length in little-endian
            header_len_bytes = f.read(2)
            if not header_len_bytes:
                raise ValueError("File is empty or corrupted (could not read header length).")
            header_len = int.from_bytes(header_len_bytes, byteorder='little')

            # Read the header
            header_bytes = f.read(header_len)
            header_str = header_bytes.decode('utf-8')

            # Parse the header JSON
            header = json.loads(header_str)
            
            # Detailed header inspection for debugging
            print(f"=== HEADER INSPECTION ===")
            print(f"Header keys: {list(header.keys())}")
            for key, value in header.items():
                if 'sample' in key.lower() or 'rate' in key.lower() or 'freq' in key.lower():
                    print(f"  {key}: {value} (type: {type(value)})")
            
            # Try multiple possible sample rate keys with comprehensive search
            sample_rate_keys = ['sampling_rate', 'sample_rate', 'fs', 'frequency', 'rate', 'sampleRate', 'samplingRate', 'freq', 'f_s']
            found_rate = None
            
            # First pass: exact key match
            for key in sample_rate_keys:
                if key in header:
                    found_rate = header[key]
                    print(f"Found sample rate with key '{key}': {found_rate}")
                    break
            
            # Second pass: case-insensitive search
            if found_rate is None:
                for key in header.keys():
                    if any(rate_key.lower() in key.lower() for rate_key in ['sample', 'rate', 'freq', 'fs']):
                        found_rate = header[key]
                        print(f"Found sample rate with case-insensitive key '{key}': {found_rate}")
                        break
            
            # Third pass: nested search in sub-dictionaries
            if found_rate is None:
                for key, value in header.items():
                    if isinstance(value, dict):
                        for sub_key in sample_rate_keys:
                            if sub_key in value:
                                found_rate = value[sub_key]
                                print(f"Found sample rate in nested dict '{key}.{sub_key}': {found_rate}")
                                break
                        if found_rate is not None:
                            break
            
            if found_rate is None:
                print("WARNING: No sample rate found in header! Using default 1000Hz")
                print(f"Available header keys: {list(header.keys())}")
                # Show nested structure for debugging
                for key, value in header.items():
                    if isinstance(value, dict):
                        print(f"  {key}: {list(value.keys())}")
            else:
                # Validate sample rate
                try:
                    found_rate = float(found_rate)
                    if found_rate <= 0 or found_rate > 100000:
                        print(f"WARNING: Suspicious sample rate {found_rate} Hz, using default 1000Hz")
                        found_rate = 1000.0
                    else:
                        print(f"Validated sample rate: {found_rate} Hz")
                except (ValueError, TypeError):
                    print(f"WARNING: Invalid sample rate format '{found_rate}', using default 1000Hz")
                    found_rate = 1000.0
            
            # Read the rest of the file as data
            data_bytes = f.read()
            print(f"Successfully read file with {len(data_bytes)} bytes of data")
            return {'header': header, 'data_bytes': data_bytes}
    except json.JSONDecodeError as e:
        print(f"Error decoding header JSON from file: {file_path}. Error: {e}")
        traceback.print_exc()
        raise ValueError(f"Invalid JSON in header: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while reading PPD file: {file_path}. Error: {e}")
        traceback.print_exc()
        return None

def parse_ppd_data(data_bytes, header, downsample_factor=1):
    """
    Parses the data bytes from a .ppd file and returns a dictionary containing
    all the required fields for the GUI.
    
    Args:
        data_bytes: Raw data bytes from the PPD file
        header: Header dictionary from the PPD file
        downsample_factor: Factor to downsample the data by (default: 1)
    
    Returns:
        Dictionary containing all required fields for the GUI
    """
    if header is None or data_bytes is None or len(data_bytes) == 0:
        print("Error: No valid data found for parsing.")
        return None

    try:
        # Extract sample rate with comprehensive search
        sample_rate_keys = ['sampling_rate', 'sample_rate', 'fs', 'frequency', 'rate', 'sampleRate', 'samplingRate', 'freq', 'f_s']
        sampling_rate = None
        
        # Search for sample rate in header
        for key in sample_rate_keys:
            if key in header:
                sampling_rate = header[key]
                break
        
        # If not found, use default and warn
        if sampling_rate is None:
            print("WARNING: No sample rate found in header during parsing! Using default 1000Hz")
            sampling_rate = 1000.0
        else:
            try:
                sampling_rate = float(sampling_rate)
                if sampling_rate <= 0 or sampling_rate > 100000:
                    print(f"WARNING: Suspicious sample rate {sampling_rate} Hz during parsing, using default 1000Hz")
                    sampling_rate = 1000.0
            except (ValueError, TypeError):
                print(f"WARNING: Invalid sample rate format '{sampling_rate}' during parsing, using default 1000Hz")
                sampling_rate = 1000.0
        
        volts_per_division = header.get('volts_per_division', [1.0, 1.0])

        # Original format is unsigned 16-bit integers in little-endian
        data = np.frombuffer(data_bytes, dtype=np.dtype('<u2'))

        if len(data) == 0:
            print("Warning: No data points found in file after reading bytes.")
            return None

        # The last bit is the digital signal, the rest is the analog value
        analog = data >> 1
        digital = data & 1

        # Separate channels - even indices are channel 1, odd are channel 2
        analog_1 = analog[0::2]
        analog_2 = analog[1::2]
        digital_1 = digital[0::2]
        digital_2 = digital[1::2]

        # Ensure all arrays have the same length to prevent errors
        min_len = min(len(analog_1), len(analog_2), len(digital_1), len(digital_2))
        
        # Handle case where min_len is 0 after slicing
        if min_len == 0:
            print("Warning: No data points found in file after separating channels.")
            return None
             
        analog_1 = analog_1[:min_len]
        analog_2 = analog_2[:min_len]
        digital_1 = digital_1[:min_len]
        digital_2 = digital_2[:min_len]

        # Create the time array
        time_raw = np.arange(min_len) / sampling_rate

        # Apply volts per division scaling (convert to mV)
        if len(volts_per_division) >= 2:
            analog_1 = analog_1.astype(np.float64) * volts_per_division[0]
            analog_2 = analog_2.astype(np.float64) * volts_per_division[1]

        # Downsample if needed
        if downsample_factor > 1:
            original_length = len(time_raw)
            time_raw = time_raw[::downsample_factor]
            analog_1 = analog_1[::downsample_factor]
            analog_2 = analog_2[::downsample_factor]
            digital_1 = digital_1[::downsample_factor]
            digital_2 = digital_2[::downsample_factor]
            print(f"Downsampling: {original_length} -> {len(time_raw)} samples (factor: {downsample_factor})")
        else:
            print(f"No downsampling applied (factor: {downsample_factor})")

        # Calculate dF/F using a more efficient method
        window_size = int(sampling_rate / downsample_factor)  # 1 second window
        # Use a more efficient moving average calculation
        baseline = np.zeros_like(analog_1)
        half_window = window_size // 2
        for i in range(len(analog_1)):
            start = max(0, i - half_window)
            end = min(len(analog_1), i + half_window + 1)
            baseline[i] = np.mean(analog_1[start:end])
        
        dff = (analog_1 - baseline) / baseline * 100  # Convert to percentage

        # Create the return dictionary with all required fields
        result = {
            'time_raw': time_raw,
            'time': time_raw,  # For compatibility
            'analog_1_raw': analog_1,
            'analog_2_raw': analog_2,
            'raw1': analog_1,  # For compatibility
            'raw2': analog_2,  # For compatibility
            'digital1': digital_1,
            'digital2': digital_2,
            'dff': dff,
            'fs': sampling_rate / downsample_factor,
            'fs_original': sampling_rate,  # Store original sample rate
            'downsample_factor': downsample_factor,
            'drift': baseline,  # Store the baseline as drift
            'fit': baseline,    # Store the baseline as fit
            'peaks': {'indices': np.array([]), 'times': np.array([]), 'heights': np.array([])},
            'valleys': {'indices': np.array([]), 'times': np.array([]), 'heights': np.array([])},
            'artifact_mask': np.zeros_like(time_raw, dtype=bool)
        }

        print(f"Parsed data: {len(time_raw)} samples, duration: {time_raw[-1]:.2f} seconds, effective fs: {sampling_rate / downsample_factor:.1f} Hz")
        return result

    except Exception as e:
        print(f"Error parsing PPD data: {e}")
        traceback.print_exc()
        return None