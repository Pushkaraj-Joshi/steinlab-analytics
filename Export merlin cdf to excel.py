# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.

Created by Pushkaraj Joshi
"""

import netCDF4
import pandas as pd
import os
import glob
import shutil

def cdf_to_xlsx(input_cdf_path, output_xlsx_path):
    """
    Reads a .cdf file and exports its variables to an XLSX file,
    handling variables of different lengths by padding with NaN.
    
    Args:
        input_cdf_path (str): The full path to the input .cdf file.
        output_xlsx_path (str): The full path for the output XLSX file.
    """
    try:
        with netCDF4.Dataset(input_cdf_path, 'r') as nc_file:
            data = {}
            # Get all variables and their lengths
            var_lengths = {var_name: len(var_data) for var_name, var_data in nc_file.variables.items()}
            
            if not var_lengths:
                print(f"Warning: No variables found in '{input_cdf_path}'. Skipping.")
                return

            # Find the maximum length to pad shorter variables
            max_len = max(var_lengths.values())

            for var_name, var_data in nc_file.variables.items():
                current_data = var_data[:].tolist()
                
                # Pad shorter lists with NaN to match the max_len
                if len(current_data) < max_len:
                    current_data += [pd.NA] * (max_len - len(current_data))
                
                data[var_name] = current_data
            
            # Create a pandas DataFrame from the processed dictionary
            df = pd.DataFrame(data)
            
            # Save the DataFrame to an XLSX file
            df.to_excel(output_xlsx_path, index=False)
            
        print(f"Successfully converted '{input_cdf_path}' to '{output_xlsx_path}'")
        
    except FileNotFoundError:
        print(f"Error: The file '{input_cdf_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# --- Automated file processing ---

# Define the base directory containing the .cdf files
base_dir = r'H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Sep_22_2025\trial_2\L2-100V'

# Use glob to find all files with the .cdf extension in the base directory
cdf_files = glob.glob(os.path.join(base_dir, '*.cdf'))

# Check if any .cdf files were found
if not cdf_files:
    print(f"No .cdf files found in the directory: {base_dir}")
else:
    # Loop through each found .cdf file
    for input_cdf_filepath in cdf_files:
        # Extract the base filename without the extension
        base_name, _ = os.path.splitext(os.path.basename(input_cdf_filepath))
        
        # Construct the output .xlsx filename
        output_file_name = f"{base_name}.xlsx"
        
        # Construct the full output path
        output_xlsx_filepath = os.path.join(base_dir, output_file_name)
        
        # Call the conversion function with the determined file paths
        cdf_to_xlsx(input_cdf_filepath, output_xlsx_filepath)


# --- Store a copy of the analysis script ---
# Get the path of the current Python script using __file__
try:
    current_script_path = os.path.abspath(__file__)
    
    # Construct the destination path for the copied script
    script_copy_path = os.path.join(base_dir, os.path.basename(current_script_path))
    
    # Copy the current Python script to the base directory
    shutil.copyfile(current_script_path, script_copy_path)
    print(f"\nCopied current script to: {script_copy_path}")
except NameError:
    # This block handles cases where __file__ is not defined (e.g., in an interactive shell)
    print("\nSkipping script copy. `__file__` is not defined.")
except shutil.SameFileError:
    print("\nThe script is already in the target directory, skipping copy.")
except Exception as e:
    print(f"\nError copying script: {e}")