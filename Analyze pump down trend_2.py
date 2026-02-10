# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 11:19:57 2025

@author: Pushkaraj Joshi
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import os
import shutil

# Define the paths to your input files
file_path = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Nov_11_2025\2\pump_down\pump_down_timeline.txt"
valve_open_file_path = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Nov_11_2025\2\pump_down\valve_open_time_and_pressure.txt"

# Define the target pressure in Torr
target_pressure = 5e-6

# --- Step 1: Read the pump-down data ---
try:
    df = pd.read_csv(file_path, sep='\t', header=None)
    if df.empty:
        print("Error: Pump-down data file is empty.")
        exit()
    df.columns = ['pressure_torr', 'year', 'month', 'day', 'hour', 'minute', 'second']
except FileNotFoundError:
    print(f"Error: Pump-down data file not found at {file_path}")
    exit()
except Exception as e:
    print(f"Error reading pump-down data file: {e}")
    exit()

# --- Step 2: Read the valve open time ---
valve_open_time = None
try:
    # Use pandas to read the file, correctly handling the header and columns
    valve_df = pd.read_csv(valve_open_file_path, sep='\t', header=0)
    
    # Corrected: Get the timestamp from the first row and first column
    valve_open_time_str = valve_df.iloc[0, 0]
    
    # Use pandas.to_datetime with format='mixed' to handle the fractional seconds
    valve_open_time = pd.to_datetime(valve_open_time_str, format='mixed')
    print(f"Valve open time read: {valve_open_time}")
    
except FileNotFoundError:
    print(f"Error: Valve open time file not found at {valve_open_file_path}")
except Exception as e:
    print(f"Error processing valve open time file: {e}")
    
# --- Step 3: Process time data and calculate elapsed time ---
df['timestamp'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])
start_time_for_calc = valve_open_time if valve_open_time is not None else df['timestamp'].iloc[0]
df['elapsed_minutes'] = (df['timestamp'] - start_time_for_calc).dt.total_seconds() / 60

# --- Step 4: Find the time to reach the target pressure ---
pump_down_time_minutes = None
pump_down_timestamp = None
if valve_open_time is not None:
    df_after_valve = df[df['timestamp'] >= valve_open_time]
    if not df_after_valve.empty:
        try:
            pump_down_row = df_after_valve[df_after_valve['pressure_torr'] <= target_pressure].iloc[0]
            pump_down_time_minutes = pump_down_row['elapsed_minutes']
            pump_down_timestamp = pump_down_row['timestamp']
        except IndexError:
            print(f"The pressure of {target_pressure} Torr was never reached or sustained in the data after the valve opened.")
    else:
        print("No data recorded after the valve opened.")
else:
    print("Valve open time is not available, cannot calculate pump down time relative to valve open.")

# --- Step 5: Create the plot ---
fig, ax = plt.subplots(figsize=(12, 8))
ax.plot(df['timestamp'], df['pressure_torr'], label='Pressure')

ax.set_xlabel('Time')
ax.set_ylabel('Pressure (Torr)')
ax.set_title('Full Pressure History')
ax.grid(True, which="both", ls="--")
ax.set_yscale('log')

# Format the x-axis for better readability of datetimes
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
fig.autofmt_xdate(rotation=45)

# --- Step 6: Add vertical line for valve open and text ---
if valve_open_time is not None:
    ax.axvline(x=valve_open_time, color='g', linestyle='-', label='Valve Open Time')
    # A more robust text placement using relative y-position and the Axes transform
    ax.text(valve_open_time, ax.get_ylim()[1], "Valve Opened", color='g', 
            ha='left', va='top', rotation=90)

# --- Step 7: Add horizontal and vertical lines and text for pump down time (if successful) ---
if pump_down_time_minutes is not None:
    ax.axhline(y=target_pressure, color='r', linestyle='--', 
                label=f'Target Pressure: {target_pressure:.1e} Torr')
    ax.axvline(x=pump_down_timestamp, color='r', linestyle='--')
    ax.text(pump_down_timestamp, target_pressure, 
             f"Pump down time: {pump_down_time_minutes:.2f} min", 
             fontsize=12, color='red', ha='left', va='top')
    
ax.legend()
plt.tight_layout()

# --- Step 8: Create the output folder and save the plot ---
base_dir, filename = os.path.split(file_path)
analysis_folder = os.path.join(base_dir, 'Analysis')

if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)

output_file_name = f"{os.path.splitext(filename)[0]}_full_history_analysis.pdf"
output_path = os.path.join(analysis_folder, output_file_name)
plt.savefig(output_path, format="pdf")
print(f"\nPlot saved to: {output_path}")

# --- Optional: Display the plot ---
plt.show()

# --- Print the final calculated value ---
if pump_down_time_minutes is not None:
    print(f"The time to reach {target_pressure} Torr was {pump_down_time_minutes:.2f} minutes.")
    
# --- Store a copy of the analysis script in the base folder ---
current_script_path = os.path.abspath(__file__)
script_copy_path = os.path.join(analysis_folder, os.path.basename(current_script_path))

try:
    shutil.copyfile(current_script_path, script_copy_path)
    print(f"Copied current script to: {script_copy_path}")
except shutil.SameFileError:
    print("The script is already in the target directory, skipping copy.")
except Exception as e:
    print(f"Error copying script: {e}")