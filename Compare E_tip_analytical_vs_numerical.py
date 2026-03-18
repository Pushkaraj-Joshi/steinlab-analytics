# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 19:07:47 2026

@author: pjoshi11
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil

# --- 1. Load the Data & Setup Paths ---
# Replace this with the actual path to your Excel file
file_path = r"C:\Users\pjoshi11\Documents\COMSOL_working files\Plots - Onset-field-study- Mar_14_2026 - CapRadius_Sweep\Onset_voltage_summary.xlsx"
sheet_name = 'Sheet1' # Adjust if your data is on a different sheet

# Get the absolute directory path of the Excel file
target_dir = os.path.dirname(os.path.abspath(file_path))

# Copy this Python script to the target directory
try:
    script_path = os.path.abspath(__file__)
    shutil.copy2(script_path, target_dir)
    print(f"Success: Copied Python script to {target_dir}")
except NameError:
    print("Note: Running in an interactive environment (like Jupyter). Automatic script copying skipped.")
except Exception as e:
    print(f"Warning: Could not copy script. Error: {e}")

# Read the Excel file
df = pd.read_excel(file_path, sheet_name=sheet_name)

# --- 2. Define Constants ---
# z0 is 'd' (tip-electrode separation). 
# Using 0.5 um based on your previous code (IFE_spacing = 0.5e-6). 
# UPDATE THIS VALUE if 'd' is different in this specific dataset.
d = 1e-3 # 1mm 

# --- 3. Extract and Calculate ---
# Convert R_cap from nm to meters
r_cap_m = df['R_cap (nm)'] * 1e-9
v_rayleigh = df['V_onset_Rayleigh (V)']
e_simulated = df['E_max(derived)']

# Calculate Analytical E-field
# E0 = (sqrt(2) * V) / (rc * ln(4 * z0 / rc))
e_analytical = (np.sqrt(2) * v_rayleigh) / (r_cap_m * np.log((4 * d) / r_cap_m))

# Add the calculated values back to the dataframe
df['E_analytical'] = e_analytical

# Sort by Voltage so the plot lines connect sequentially from left to right
df_sorted = df.sort_values(by='V_onset_Rayleigh (V)')

# --- 4. Plotting ---
plt.figure(figsize=(10, 6))

# Plot Simulated E_max (converted to V/nm)
plt.plot(df_sorted['V_onset_Rayleigh (V)'], df_sorted['E_max(derived)'] / 1e9, 
         marker='o', linestyle='-', color='#1f77b4', linewidth=2, label='Simulated $E_{max}$')

# Plot Analytical E0 (converted to V/nm)
plt.plot(df_sorted['V_onset_Rayleigh (V)'], df_sorted['E_analytical'] / 1e9, 
         marker='s', linestyle='--', color='#d62728', linewidth=2, label='Analytical $E_0$')

# Formatting
plt.xlabel('Rayleigh Onset Voltage (V)', fontsize=12)
plt.ylabel('Electric Field Magnitude (V/nm)', fontsize=12)
plt.title('Electric Field vs. Onset Voltage\n(Annotated with Cap radius)', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11)

# Annotate R_cap values onto the Simulated points for context
for i, row in df_sorted.iterrows():
    plt.annotate(f"{row['R_cap (nm)']:g} nm", 
                 (row['V_onset_Rayleigh (V)'], row['E_max(derived)'] / 1e9), # <-- Added / 1e9 here
                 textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)

plt.tight_layout()

# --- ADD THESE LINES TO SAVE PLOT 1 ---
plot1_path = os.path.join(target_dir, "E_Field_vs_Voltage_2.pdf")
plt.savefig(plot1_path, format='pdf')
print(f"Saved Plot 1 to: {plot1_path}")
# --------------------------------------
plt.show()

# --- 5. Plotting Plot 2: E_sim / E_analytical vs R_cap ---

# Calculate the ratio
df['E_ratio'] = df['E_max(derived)'] / df['E_analytical']

# Sort by R_cap so the line connects sequentially from left to right
df_sorted_rcap = df.sort_values(by='R_cap (nm)')

plt.figure(figsize=(10, 6))

# Plot the ratio
plt.plot(df_sorted_rcap['R_cap (nm)'], df_sorted_rcap['E_max(derived)']/1e9, 
         marker='o', linestyle='-', color='#1f77b4', linewidth=2, label='$E_{simulated}$')
plt.plot(df_sorted_rcap['R_cap (nm)'], df_sorted_rcap['E_analytical']/1e9, 
         marker='^', linestyle='-', color='#2ca02c', linewidth=2, label='$E_{analytical}$')


# Formatting
plt.xscale('log')
plt.xlabel('Cap Radius (nm)', fontsize=12)
plt.ylabel('Electric Field (V/nm)', fontsize=12)
plt.title('Comparison Ratio vs. Cap Radius at onset condition', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11)

plt.tight_layout()

# --- ADD THESE LINES TO SAVE PLOT 2 ---
plot2_path = os.path.join(target_dir, "E_Ratio_vs_Rcap_2.pdf")
plt.savefig(plot2_path, format='pdf')
print(f"Saved Plot 2 to: {plot2_path}")
# --------------------------------------

plt.show()

# Optional: Print the comparison table to the console
print("\n--- Data Comparison ---")
print(df[['R_cap (nm)', 'V_onset_Rayleigh (V)', 'E_max(derived)', 'E_analytical']])