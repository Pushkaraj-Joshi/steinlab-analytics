# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 13:08:26 2026

@author: pjoshi11
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil
from datetime import datetime

# --- 1. Setup Paths ---
# The base folder is where this script is located
base_folder = r'C:\Users\pjoshi11\Documents\COMSOL_working files\Plots - Onset-field-study- Mar_14_2026 - CapRadius_Sweep'
excel_name = 'Onset_voltage_summary.xlsx'
excel_path = os.path.join(base_folder, excel_name)

# Define output naming
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plot_output = os.path.join(base_folder, f"Consolidated_Onset_Plot_{timestamp}.pdf")

# --- 2. Load Data ---
if not os.path.exists(excel_path):
    print(f"Error: {excel_name} not found in {base_folder}")
else:
    # Read the summary sheet (assuming columns: 'R_cap (nm)', 'V_onset_Rayleigh (V)', 'V_onset_Taylor (V)')
    df = pd.read_excel(excel_path)
    
    # Sort by Radius for a clean line plot
    df = df.sort_values('R_cap (nm)')

    # --- 3. Synchronize Axis Bounds ---
    v_min = df[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].min().min()
    v_max = df[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].max().max()
    
    # Add 10% padding
    padding = (v_max - v_min) * 0.1
    y_limits = (v_min - padding, v_max + padding)

    # --- 4. Plotting ---
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Rayleigh Axis (Left - Blue)
    color_ray = '#1f77b4'
    line1 = ax1.plot(df['R_cap (nm)'], df['V_onset_Rayleigh (V)'], 
                     marker='o', color=color_ray, linewidth=2, label='Rayleigh Condition')
    ax1.set_xlabel('Capillary Radius ($R_{cap}$) [nm]')
    ax1.set_ylabel('Onset Voltage (V)', color=color_ray)
    ax1.tick_params(axis='y', labelcolor=color_ray)
    ax1.set_xscale('log')
    ax1.set_ylim(y_limits)
    ax1.grid(True, which="both", ls="--", alpha=0.5)
    ax1.axvline(x=0.5, color='gray', linestyle='--', linewidth=1.5, label='Solvated Na+ Ion Size')
    ax1.text(0.55, y_limits[0] + padding, 'Solvated Na$^+$ Ion Size', rotation=90, verticalalignment='bottom', color='gray', fontsize=9)

    # Taylor Axis (Right - Red)
    ax2 = ax1.twinx()
    color_tay = '#d62728'
    line2 = ax2.plot(df['R_cap (nm)'], df['V_onset_Taylor (V)'], 
                     marker='D', color=color_tay, linewidth=2, label='Taylor Condition')
    ax2.set_ylabel('Onset Voltage (V)', color=color_tay)
    ax2.tick_params(axis='y', labelcolor=color_tay)
    ax2.set_ylim(y_limits)

    # Title and Legend
    plt.title(f'Comparison of Onset Voltage Conditions vs Capillary Radius\n($R_{{in}}$=40nm, Depth=100$\mu$m, IFE=0.5$\mu$m)')
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best')

    plt.tight_layout()
    plt.savefig(plot_output)
    print(f"Plot saved to: {plot_output}")
    plt.show()

# --- 5. Save a copy of this script in the base folder ---
script_backup = os.path.join(base_folder, f"Archive_Plotting_Script_{timestamp}.py")
shutil.copy2(__file__, script_backup)
print(f"Script archived to: {script_backup}")