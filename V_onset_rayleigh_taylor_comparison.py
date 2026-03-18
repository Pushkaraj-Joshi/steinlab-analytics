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
base_folder = r'C:\Users\pjoshi11\Documents\COMSOL_working files\Plots - Onset-field-study- Mar_14_2026 - CapRadius_Sweep'
excel_name = 'Onset_voltage_summary.xlsx'
excel_path = os.path.join(base_folder, excel_name)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plot_output = os.path.join(base_folder, f"Consolidated_Onset_Plot_{timestamp}.pdf")

# --- 2. Load Data ---
if not os.path.exists(excel_path):
    print(f"Error: {excel_name} not found in {base_folder}")
else:
    df = pd.read_excel(excel_path)
    df = df.sort_values('R_cap (nm)')

    # --- 3. Synchronize Axis Bounds ---
    v_min = df[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].min().min()
    v_max = df[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].max().max()
    
    padding = (v_max - v_min) * 0.1
    y_limits = (v_min - padding, v_max + padding)

    # --- 4. Plotting (Single Y-Axis) ---
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Rayleigh Data (Blue)
    color_ray = '#1f77b4'
    ax1.plot(df['R_cap (nm)'], df['V_onset_Rayleigh (V)'], 
             marker='o', color=color_ray, linewidth=2, label='V_onset (2γ/R_cap vs Max E-field)')

    # Taylor Data (Red) - Plotted on the same ax1
    color_tay = '#d62728'
    ax1.plot(df['R_cap (nm)'], df['V_onset_Taylor (V)'], 
             marker='D', color=color_tay, linewidth=2, label='V_onset (γ/R_cap vs E-field at cone surface)')

    # Vertical line for Na+ Ion Size
    ax1.axvline(x=0.5, color='gray', linestyle='--', linewidth=1.5, label='Solvated Na$^+$ Ion Size')
    ax1.text(0.55, y_limits[0] + (padding * 0.5), 'Solvated Na$^+$ Ion Size', 
             rotation=90, verticalalignment='bottom', color='gray', fontsize=9)

    # Axis Formatting (Black Labels/Ticks)
    ax1.set_xlabel('Cap Radius ($R_{cap}$) [nm]', color='black')
    ax1.set_ylabel('Onset Voltage (V)', color='black')
    ax1.tick_params(axis='both', labelcolor='black')
    
    ax1.set_xscale('log')
    ax1.set_ylim(y_limits)
    ax1.grid(True, which="both", ls="--", alpha=0.5)

    # Title and Legend
    plt.title(f'Comparison of Onset Voltage Conditions vs Capillary Radius\n($R_{{in}}$=40nm, Depth=100$\mu$m, IFE=0.5$\mu$m)')
    
    # Legend shows both Rayleigh (blue) and Taylor (red)
    ax1.legend(loc='best', frameon=True)

    plt.tight_layout()
    plt.savefig(plot_output)
    print(f"Plot saved to: {plot_output}")
    plt.show()

# --- 5. Save a copy of this script ---
script_backup = os.path.join(base_folder, f"Archive_Plotting_Script_{timestamp}.py")
# Note: In some environments __file__ may not be defined; 
# if so, replace __file__ with the string of this script's name.
try:
    shutil.copy2(__file__, script_backup)
    print(f"Script archived to: {script_backup}")
except NameError:
    print("Script archiving skipped (running in interactive mode).")