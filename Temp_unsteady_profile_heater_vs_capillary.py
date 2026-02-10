# -*- coding: utf-8 -*-
"""
Created on Wed Nov 12 16:55:53 2025

@author: pjoshi11
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil

# --- 1. Define the Local File Path ---
# NOTE: Use 'r' before the string (Raw string) to handle backslashes in Windows paths
file_path = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Nov_17_2025\Step_wise_temp_evolution_with_conductive_grease_trial_1 - Form Responses 1.csv"
# If on macOS/Linux: local_file_path = '/Users/YourName/Google Drive/Project_Data/Form_Responses_Sheet1.csv'

try:
    # 2. Read the CSV directly into a pandas DataFrame
    # Note: Use the actual column names from your form (e.g., 'Timestamp', 'Temp - Object 1')
    df = pd.read_csv(file_path)
    
except FileNotFoundError:
    print(f"Error: CSV file not found at the specified path: {file_path}")
    exit()


# Split the full file path to get the directory and the base file name
base_dir, filename = os.path.split(file_path) 
# Define the analysis subfolder path
analysis_folder = os.path.join(base_dir, 'Analysis')

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)
# --- 3. Prepare Data for Plotting ---
# Ensure the Timestamp column is a proper datetime object
# (The column name must match exactly what your form/sheet created)
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Calculate Elapsed Time (in minutes)
start_time = df['Timestamp'].min()
df['Time_min'] = (df['Timestamp'] - start_time).dt.total_seconds() / 60

# --- 4. Create the Plot ---
plt.figure(figsize=(10, 6))

# Use the exact column names for your temperature data
plt.plot(df['Time_min'], df['Heater Temperature (C)'], label='Heater Temperature', marker='o', linestyle='-')
plt.plot(df['Time_min'], df['Capillary tip Temperature (C)'], label='Capillary tip Temperature', marker='x', linestyle='--')

# --- 5. Customization ---
plt.title('Temperature Evolution between heater plate and capillary')
plt.xlabel('Time Elapsed (minutes)')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True)
# Save the plot as pdf in the analysis subfolder
# Uses f-string to dynamically name the file based on the original data file name
plt.savefig(os.path.join(analysis_folder, f'{filename[:-4]}.pdf'))

plt.show()

# --- Store a copy of the analysis script in the base folder ---

# Get the path of the current Python script
# NOTE: '__file__' must be used inside a script run from a file to work correctly.
current_script_path = os.path.abspath(__file__)

# Construct the destination path for the copied script
script_copy_path = os.path.join(base_dir, os.path.basename(current_script_path))

# Copy the current Python script to the base directory
try:
    shutil.copyfile(current_script_path, script_copy_path)
    # print(f"Copied current script to: {script_copy_path}") # Optional: add a print statement
except shutil.SameFileError:
    pass # Script is already there, skip
except Exception as e:
    print(f"Error copying script: {e}")