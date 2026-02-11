# -*- coding: utf-8 -*-
"""
Created on Tue Jul 29 11:02:17 2025

@author: pjoshi11
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import matplotlib.ticker as ticker
from si_prefix import si_format
import shutil
import math

def calculate_pore_diameter(pore_resistance, solution_conductivity, half_cone_angle):
    """
    Calculates the pore diameter based on equation in "Characterization of Nanopipette, Anal.Chem(2016), Perry et.al."
    Returns None if conductivity is missing or invalid.
    """
    # Check for None, zero, or NaN conductivity
    if solution_conductivity is None or solution_conductivity <= 0 or np.isnan(solution_conductivity):
        return None

    if pore_resistance == 0:
        raise ValueError("Resistance cannot be zero.")

    # Convert the angle to radians
    angle_in_radians = math.radians(half_cone_angle)

    # Implement the given formula
    pore_dia = (1 / pore_resistance) * (1 / solution_conductivity) * (1 / (math.pi * math.tan(angle_in_radians)) + 0.25)

    return pore_dia


# ~~~ Provide the base folder where data files are stored
base_dir = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance\Jul_16_2025\Tip_15'

# ~~ Enter solution conductivity in S/m. Set to None if unknown.
# Example: 10.53e-3/1e-2 or None
solution_conductivity = 3.31e-3/1e-2

# -- Enter the half cone angle in degree
half_cone_angle = 2

# --- Read and process data from multiple CSV files ---
csv_files = glob.glob(os.path.join(base_dir, "*.csv"))
all_voltages = []
all_currents = []

output_csv_filename = "averaged_IV_data.csv" 

if csv_files:
    first_csv_filename_base = os.path.basename(csv_files[0])
    filename_without_ext = os.path.splitext(first_csv_filename_base)
    last_underscore_index = filename_without_ext[0].rfind('_')
    
    if last_underscore_index != -1:
        main_part_of_filename = filename_without_ext[0][:last_underscore_index]
    else:
        main_part_of_filename = filename_without_ext[0]

    output_csv_filename = f"averaged_{main_part_of_filename}.csv"
else:
    print("Warning: No CSV files found.")
    main_part_of_filename = "no_data"

analysis_folder = os.path.join(base_dir, 'Analysis')
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder)
    
output_csv_path = os.path.join(analysis_folder, output_csv_filename) 

for file_path in csv_files:
    df = pd.read_csv(file_path, skiprows=3, usecols=[0,1], names=['Voltage', 'Current'])
    all_voltages.append(df['Voltage'].values)
    all_currents.append(df['Current'].values)

if len(set(len(v) for v in all_voltages)) != 1:
    print("Warning: IV curves have different lengths.")

average_voltage = np.mean(all_voltages, axis=0)
average_current = np.mean(all_currents, axis=0)
std_current = np.std(all_currents, axis=0)

averaged_data_df = pd.DataFrame({
    'Average Voltage (V)': average_voltage,
    'Average Current (A)': average_current,
    'Current Std Dev (A)': std_current
})
averaged_data_df.to_csv(output_csv_path, index=False)

# --- Calculate Resistance centered around 0V ---
voltage_min = -0.2
voltage_max = 0.2

indices_in_range = np.where((average_voltage >= voltage_min) & (average_voltage <= voltage_max))
voltage_for_fit_range = average_voltage[indices_in_range]
current_for_fit_range = average_current[indices_in_range]*1e9 

m_range, b_range = np.polyfit(voltage_for_fit_range, current_for_fit_range, 1)
resistance_from_slope_range = (1 / m_range)*1e9 
formatted_resistance = si_format(resistance_from_slope_range, precision=2)

# ---- Predict the pore diameter (Handles None case) ----
pore_dia = calculate_pore_diameter(resistance_from_slope_range, solution_conductivity, half_cone_angle)

if pore_dia is not None:
    formatted_pore_dia = si_format(pore_dia, precision=0) + "m"
else:
    formatted_pore_dia = "N/A"

# --- Plotting ---
fig, ax = plt.subplots(figsize=(8, 6))

ax.errorbar(average_voltage, average_current*1e9, yerr=std_current*1e9, fmt='o',
            markerfacecolor='none', markeredgecolor='red', capsize=3, label='Averaged IV Data')

ax.plot(average_voltage, m_range * average_voltage + b_range, 'k--',
         label=f' Linear Fit,\n Pore Resistance = {formatted_resistance} $\Omega$ \n Predicted pore diameter = {formatted_pore_dia} ')

ax.set_title('Averaged I-V Curve with Linear Fit (-0.2V to 0.2V)', fontsize=16)
ax.set_xlabel('Voltage (V)', fontsize=14)
ax.set_ylabel('Current (nA)', fontsize=14)
ax.tick_params(axis='both', labelsize=12, direction='in')
ax.legend()
ax.grid(True)

output_pdf_path = os.path.join(analysis_folder, f"averaged_{main_part_of_filename}.pdf")
plt.savefig(output_pdf_path, bbox_inches="tight")
plt.show()

# ---- Copy script ----
try:
    current_script_path = os.path.abspath(__file__)
    script_copy_path = os.path.join(base_dir, os.path.basename(current_script_path))
    shutil.copyfile(current_script_path, script_copy_path)
except Exception as e:
    print(f"Script copy skipped or error: {e}")

plt.close(fig)
print(f"Analysis complete. Plot saved to: {output_pdf_path}")