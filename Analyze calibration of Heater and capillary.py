# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 14:35:12 2025

@author: steinlab
"""


import pandas as pd
import matplotlib.pyplot as plt
import io
import os


# Use io.StringIO to simulate reading a file

output_base_dir = r'H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Nov_17_2025'
file = 'Step_wise_heating_ungreased_equilibrium_data - Sheet1.csv'
equilibrium_data_file_path = os.path.join(output_base_dir, file)
# To read a real file, use: df = pd.read_csv('your_filename.csv')
df = pd.read_csv(equilibrium_data_file_path)

# --- 2. Calculate Statistics ---
# Select the trial columns to calculate mean and std dev
trial_columns = ['Trial 1', 'Trial 2', 'Trial 3']

# Calculate row-wise mean and standard deviation
df['Mean Capillary'] = df[trial_columns].mean(axis=1)
df['Std Dev Capillary'] = df[trial_columns].std(axis=1)

# --- 3. Plotting ---
# Use plt.subplots to correctly define fig and ax
fig, ax = plt.subplots(figsize=(10, 6))

# 1. Plot the Mean Line (Line with a distinct marker)
ax.plot(
    df['Heater Temperature (C)'], 
    df['Mean Capillary'], 
    linestyle='-', 
    marker='o', 
    color='black', 
    linewidth=2, 
    label='Mean Capillary Temp'
)

# 2. Scatter plot for individual trials
# Each trial is plotted with a unique marker and color
ax.scatter(
    df['Heater Temperature (C)'], 
    df['Trial 1'], 
    marker='x', 
    s=100, 
    color='red', 
    label='Trial 1'
)
ax.scatter(
    df['Heater Temperature (C)'], 
    df['Trial 2'], 
    marker='s', 
    s=100, 
    color='green', 
    label='Trial 2'
)
ax.scatter(
    df['Heater Temperature (C)'], 
    df['Trial 3'], 
    marker='^', 
    s=100, 
    color='blue', 
    label='Trial 3'
)

# Labels and Title
ax.set_title('Capillary Temperature Response: Individual Trials vs. Mean', fontsize=14)
ax.set_xlabel('Heater Temperature (°C)', fontsize=12)
ax.set_ylabel('Capillary Temperature (°C)', fontsize=12)

# Grid and Legend
ax.grid(True, linestyle='--', alpha=0.7)
ax.legend(loc='upper left') # Adjust legend position
ax.tick_params(axis='both', labelsize=10, direction='in')
plt.show()

# Define the analysis subfolder path (using the first file's directory)
analysis_folder = os.path.join(output_base_dir, 'Analysis')

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)

output_filename = 'Equilibrium_Temp_Mean_Scatter_Plot.pdf' # Changed filename
plt.savefig(os.path.join(analysis_folder, output_filename))
plt.close(fig)

print(f"Plot saved to: {os.path.join(analysis_folder, output_filename)}")