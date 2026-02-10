# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 11:19:57 2025

@author: Pushkaraj Joshi
"""

import pandas as pd
import matplotlib.pyplot as plt
import datetime
import os
import shutil

# Define the path to your .tsv file
file_path = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Sep_29_2025\pump_down_trend_1.tsv"

# Define the target pressure in Torr
target_pressure = 5e-6

# --- Step 1: Read the data from the .tsv file ---
df = pd.read_csv(file_path, sep='\t', header=None)
df.columns = ['pressure_torr', 'year', 'month', 'day', 'hour', 'minute', 'second']

# --- Step 2: Process time data using pandas.to_datetime (Corrected Section) ---
# This is a robust way to handle the date/time columns, including float seconds.
df['timestamp'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])

# Calculate elapsed time in minutes from the first timestamp
start_time = df['timestamp'].iloc[0]
df['elapsed_minutes'] = (df['timestamp'] - start_time).dt.total_seconds() / 60

# --- Step 3: Find the time to reach the target pressure ---
# Find the last row where pressure is less than or equal to the target
try:
    # Reverse the DataFrame and then find the first row that meets the condition
    # This is equivalent to finding the last row in the original DataFrame
    pump_down_row = df[df['pressure_torr'] >= target_pressure].iloc[-1]
    pump_down_time_minutes = pump_down_row['elapsed_minutes']
except IndexError:
    pump_down_time_minutes = None
    print(f"The pressure of {target_pressure} Torr was never reached or sustained in the data.")

# --- Step 4: Create the plot ---
plt.figure(figsize=(10, 6))

# Plot the pressure data on a log scale for better visualization
plt.plot(df['elapsed_minutes'], df['pressure_torr'], label='Pressure')

# Set labels and title
plt.xlabel('Time (minutes)')
plt.ylabel('Pressure (Torr)')
plt.title('Pump Down Trend')
plt.grid(True, which="both", ls="--")
plt.yscale('log')

# --- Step 5: Add a horizontal line and text to the plot (if successful) ---
if pump_down_time_minutes is not None:
    # Add a horizontal line at the target pressure
    plt.axhline(y=target_pressure, color='r', linestyle='--', 
                label=f'{target_pressure:.1e} Torr')
    
    # Add a vertical line at the calculated pump-down time
    plt.axvline(x=pump_down_time_minutes, color='r', linestyle='--')
    
    # Add the text to the plot
    text_string = f"Pump down time: {pump_down_time_minutes:.2f} min"
    plt.text(pump_down_time_minutes, target_pressure, text_string, 
             fontsize=12, color='red', ha='left', va='top')
    
plt.legend()

# --- Step 6: Create the output folder if it doesn't exist ---

base_dir, filename = os.path.split(file_path)
# Define the analysis subfolder path
analysis_folder = os.path.join(base_dir, 'Analysis')

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder) # Use makedirs to create intermediate directories if needed

# --- Step 7: Save the plot as a PDF in the new folder ---
output_file_name = f"{filename[:-4]}.pdf"
output_path = os.path.join(analysis_folder, output_file_name)
plt.savefig(output_path, format="pdf")
print(f"\nPlot saved to: {output_path}")

# --- Optional: Display the plot on the screen as well ---
plt.show()

# --- Print the final calculated value ---
if pump_down_time_minutes is not None:
    print(f"The time to reach {target_pressure} Torr was {pump_down_time_minutes:.2f} minutes.")
    
    
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


