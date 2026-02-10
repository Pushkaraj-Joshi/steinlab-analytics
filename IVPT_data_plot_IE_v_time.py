# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 14:09:54 2025

@author: pjoshi11
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime as dt
import shutil

# --- Configuration ---
# Define the base directory and the three file names
base_dir = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Nov_18_2025\4"
file_names = ['ivpt5.tsv']
file_paths = [os.path.join(base_dir, fn) for fn in file_names]
trial_labels = ['Trial 1']

# Specify column names for tab-separated files
column_names = ['Tip current', 'Lens L1 Voltage', 'Lens L2 Voltage', 'Pressure',
                'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Tip_voltage']

def load_and_process_data(file_path):
    """
    Loads data from a TSV file, processes time and converts units.
    Returns a DataFrame with calculated time and converted Tip current, 
    and the Tip_voltage and L1 Voltage from the first data point.
    """
    try:
        # Use pandas.read_csv with sep='\t' for tab-separated files
        df = pd.read_csv(file_path, sep='\t', names=column_names)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None, None, None

    # --- Process the time data ---
    # Combine time components into a single datetime object
    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])

    # Calculate time elapsed in minutes from the start of the recording
    start_time = df['datetime'].iloc[0]
    df['time_minutes'] = (df['datetime'] - start_time).dt.total_seconds() / 60

    # --- Convert the data into appropriate units ---
    # Convert Tip current from A to nA
    df['Tip current (nA)'] = df['Tip current'] * 1e9

    # Extract V_tip and L1 voltage from the first data point for the plot title
    # Tip_voltage is already in Volts in the raw data (assuming standard ivpt file format)
    # L1 Voltage is in kV and should be converted to Volts
    v_tip = df['Tip_voltage'].iloc[0]
    l1_voltage = df['Lens L1 Voltage'].iloc[0] * 1000 # Convert from kV to V

    return df, v_tip, l1_voltage

# --- Create the plot ---
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# Variables to store metadata from the first file for the title
v_tip_val = None
l1_voltage_val = None

# Iterate over the files, load data, and plot
for i, path in enumerate(file_paths):
    df_data, v_tip, l1_voltage = load_and_process_data(path)
    
    if df_data is not None:
        # Plot Emission Current (Tip current) vs. Time
        ax.plot(df_data['time_minutes'], df_data['Tip current (nA)'], 
                linestyle='-', 
                label=trial_labels[i])
        
        # Capture V_tip and L1_voltage from the first file for the title
        if i == 0:
            v_tip_val = v_tip
            l1_voltage_val = l1_voltage

# --- Final Plot Customization ---

if v_tip_val is not None:
    # Set the plot title with extracted metadata
    title = (f"Emission Current vs. Time with Conical tip holder\n"
             f"$V_{{\\text{{tip}}}}$: {v_tip_val:.2f} V, $V_{{\\text{{L1}}}}$: {l1_voltage_val:.0f} V")
    ax.set_title(title, fontsize=14)

# Set labels and add grid
ax.set_xlabel('Time (minutes)', fontsize=12)
ax.set_ylabel('Emission Current (nA)', fontsize=12)
ax.grid(True, linestyle='--', alpha=0.6)

# Add the vertical line at 2 minutes to indicate heater circuit ON
heater_on_time = 3.0
ax.axvline(x=heater_on_time, 
           color='blue', 
           linestyle=':', 
           linewidth=2, 
           label=f'Heater ON ({heater_on_time:.0f} min)')

# Add legend
ax.legend(loc='best', fontsize=10)

# Adjust tick label size and direction
ax.tick_params(axis='both', labelsize=10, direction='in')

# --- Save the plot ---
# Define the analysis subfolder path
analysis_folder = os.path.join(base_dir, 'Analysis')
output_filename = 'Emission_current_vs_time_3_trials.pdf'

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)
    
plt.tight_layout() # Adjust plot to prevent labels from overlapping
plt.savefig(os.path.join(analysis_folder, output_filename))
print(f"Plot saved to: {os.path.join(analysis_folder, output_filename)}")
plt.show()

# plt.show() # Uncomment this line to display the plot immediately
plt.close(fig)

#---- Store a copy of the analysis script in the base folder
# Get the path of the current Python script
current_script_path = os.path.abspath(__file__)

# Construct the destination path for the copied script
script_copy_path = os.path.join(base_dir, os.path.basename(current_script_path))

# Copy the current Python script to the base directory
try:
    shutil.copyfile(current_script_path, script_copy_path)
    print(f"Copied current script to: {script_copy_path}")
except shutil.SameFileError:
    print("The script is already in the target directory, skipping copy.")
except Exception as e:
    print(f"Error copying script: {e}")

plt.close(fig)




