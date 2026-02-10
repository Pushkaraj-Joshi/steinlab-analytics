# -*- coding: utf-8 -*-
"""
Created on Wed Jul 30 14:09:54 2025

@author: pjoshi11
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import os
import shutil


file_path = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Dec_09_2025\5\ivpt5.tsv"


# Use pandas.read_csv with sep='\t' for tab-separated files
# Specify column names for clarity
column_names = ['Tip current', 'Lens L1 Voltage', 'Lens L2 Voltage', 'Pressure',
                'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Tip_voltage']
df = pd.read_csv(file_path, sep='\t', names=column_names)

# --- Process the time data ---
# Combine year, month, day, hour, minute, second into a single datetime object
df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])

# Calculate time elapsed in minutes from the start of the recording
start_time = df['datetime'].iloc[0]
df['time_minutes'] = (df['datetime'] - start_time).dt.total_seconds() / 60

# Convert the date into appropriate units
df['Tip current'] = df['Tip current']*1e9 # convert current from A into nA
df['Lens L1 Voltage'] = df['Lens L1 Voltage']*1000 # convert the voltage from kV into Volts 
df['Lens L1=2 Voltage'] = df['Lens L1 Voltage']*1000 # convert the voltage from kV into Volts 
df['Pressure'] = df['Pressure']*1e6 # convert the Pressure to display in terms of 10^-6 mTorr 

# --- Create the plot ---

# Create two subplots arranged vertically, sharing the x-axis (time)
fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.subplots_adjust(hspace=0.3) # Adjust vertical space between subplots

# --- Top Subplot: Lens L1 Voltage and Tip Current vs Time ---
ax0.set_title('Lens L1 Voltage & Tip Current vs. Time', fontsize = 16)
ax0.set_xlabel('Time (minutes)', fontsize = 14) # Shared x-label will be on the bottom subplot

# Primary y-axis for Lens L1 Voltage
ax0.plot(df['time_minutes'], df['Lens L1 Voltage'], linestyle='-', color='blue', label='Lens L1 Voltage (V)')
ax0.set_ylabel('Lens L1 Voltage (V)', fontsize = 14, color='blue')
ax0.tick_params(axis='y', labelcolor='blue')
ax0.tick_params(axis = 'both', labelsize = 12, direction = 'in')

ax0.grid(True)

# Secondary y-axis for Tip Current
ax0_twin = ax0.twinx() # Create a twin Axes sharing the x-axis
ax0_twin.plot(df['time_minutes'], df['Tip current'], linestyle='-', color='red', label='Tip Current (A)')
ax0_twin.set_ylabel('Tip Current (nA)', fontsize = 14, color='red')
ax0_twin.tick_params(axis='y', labelcolor='red')
ax0_twin.tick_params(axis = 'both', labelsize = 12, direction = 'in')
ax0_twin.axhline(0.0, color='gray', linestyle='--', linewidth=1.5) # Adds a horizontal dashed line at y=0

# Combine legends from both axes
# lines0, labels0 = ax0.get_legend_handles_labels()
# lines0_twin, labels0_twin = ax0_twin.get_legend_handles_labels()
# ax0_twin.legend(lines0 + lines0_twin, labels0 + labels0_twin, loc='upper left')

# --- Bottom Subplot: Tip Current and Pressure vs Time ---
ax1.set_title('Pressure vs. Time', fontsize = 16)
ax1.set_xlabel('Time (minutes)', fontsize = 14)

# Primary y-axis for Tip Current
ax1.plot(df['time_minutes'], df['Pressure'], linestyle='-', color='green', label=r'Pressure ($\times 10^{-6}$ mTorr)')
ax1.set_ylabel(r'Pressure ($\times 10^{-6}$ mTorr)', fontsize = 14, color='green')
ax1.tick_params(axis='y', labelcolor='green')
ax1.tick_params(axis = 'both', labelsize = 12, direction = 'in')
ax1.grid(True)

# # Secondary y-axis for Pressure
# ax1_twin = ax1.twinx() # Create a twin Axes sharing the x-axis
# ax1_twin.plot(df['time_minutes'], df['Pressure'], linestyle='-', color='green', label=r'Pressure ($\times 10^{-6}$ mTorr)')
# ax1_twin.set_ylabel(r'Pressure ($\times 10^{-6}$ mTorr)', fontsize = 14, color='green')
# ax1_twin.tick_params(axis='y', labelcolor='green')
# ax1_twin.tick_params(axis = 'both', labelsize = 12, direction = 'in')

# Combine legends from both axes
# lines1, labels1 = ax1.get_legend_handles_labels()
# lines1_twin, labels1_twin = ax1_twin.get_legend_handles_labels()
# ax1_twin.legend(lines1 + lines1_twin, labels1 + labels1_twin, loc='upper left')


#Save the plot as pdf by creating a folder named analysis

base_dir, filename = os.path.split(file_path)
# Define the analysis subfolder path
analysis_folder = os.path.join(base_dir, 'Analysis')

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder) # Use makedirs to create intermediate directories if needed
    
plt.savefig(os.path.join(analysis_folder, f'{filename[:-4]}_plot.pdf'))    
plt.show()


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




