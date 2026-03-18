# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 16:41:50 2026

@author: pjoshi11
"""

import mph
import os
import sys
import shutil
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

# --- 1. Setup Paths & Dynamic Folder Creation ---
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_14_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)
file_path = os.path.join(folder_path, 'meniscus_data.txt')

base_name = os.path.splitext(mph_filename)[0] 
plots_base_dir = os.path.join(folder_path, f"Plots - {base_name} - CapRadius_Sweep")

timestamp_str = datetime.now().strftime("%b-%d-%Y - %H-%M-%S")
target_dir = os.path.join(plots_base_dir, timestamp_str)
os.makedirs(target_dir, exist_ok=True)
print(f"Created main output directory: {target_dir}")

shutil.copy2(full_mph_path, target_dir)
print(f"Copied {mph_filename} to output directory.")

try:
    script_path = os.path.abspath(__file__)
    shutil.copy2(script_path, target_dir)
    print("Copied Python script to output directory.")
except NameError:
    print("Note: Running in interactive environment. Automatic script copying skipped.")

# --- 2. Initialize COMSOL & Constants ---
client = mph.start()
model = client.load(full_mph_path)

eps_0 = 8.85418782e-12   
gamma = 0.072            

# --- Sweep Parameter List & Fixed Parameters ---
r_cap_list = [35e-9] #, 20e-9, 10e-9, 5e-9, 2e-9, 1.5e-9, 1e-9, 0.75e-9 in meters

r_inner_fixed = 40e-9
cap_depth_fixed = 100e-6
ife_spacing_fixed = 0.5e-6 

# Apply Fixed Parameters to COMSOL BEFORE the loop
model.parameter('R_inner', f'{r_inner_fixed} [m]')
model.parameter('IFE_spacing', f'{ife_spacing_fixed} [m]') 
model.parameter('Ext_elec_R_i', '0.0 [m]')
model.parameter('capillary_depth', f'{cap_depth_fixed} [m]') 

# --- Data Trackers ---
detailed_summary_data = [] # Tracks all requested variables for the Excel sheet

rayleigh_meniscus_data = {}  # Add this
taylor_meniscus_data = {}    # Add this

# --- Helper Function for Parameter Extraction ---
def get_param(name):
    """Safely fetch a parameter from COMSOL, return 'N/A' if it doesn't exist."""
    try:
        return model.parameter(name)
    except:
        return "N/A"

# --- 3. Main Execution (Sweep of R_cap) ---
model.java.study('std1').run()

prev_onset_ray = None 

for r_cap in r_cap_list:
    
    r_cap_nm = r_cap * 1e9
    model.parameter('R_cap', f'{r_cap} [m]')
    
    print(f"\n{'='*60}")
    print(f"Starting iteration for Capillary Radius (R_cap): {r_cap_nm:g} nm")
    print(f"{'='*60}")
    
    p_laplace_rayleigh = (2 * gamma) / r_cap
    p_laplace_taylor = gamma / r_cap
    
    # -------------------------------------------------------------------------
    # --- PART 1: Calculate Rayleigh Onset (Nested Data Evaluation) ---
    # -------------------------------------------------------------------------
    print(f"\n--- Searching for Rayleigh Onset (V_onset_rayleigh) ---")
    
    if prev_onset_ray is None:
        v_low = 50 
        v_high = 250
    else:
        v_low = 50
        v_high = max(250, 2 * prev_onset_ray) 
    
    tol = 1.0
    print(f"--- Bounding brackets: [{v_low:.1f}, {v_high:.1f}] V ---")
    
    solve_counter_ray = 0
    # Rayleigh Binary Search
    while (v_high - v_low) > tol:
        v_mid = (v_high + v_low) / 2
        model.parameter('V_ext', f'{v_mid} [V]') 
        model.solve()
        
        # EXPORT DATA to evaluate E max from the file
        model.java.result().export("data1").run()
        time.sleep(0.5) 
        solve_counter_ray += 1
        
        # Read the exported data
        df_ray_eval = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
        
        # Find the maximum Electric Field directly from the exported data
        e_max_data = df_ray_eval['E'].max()
        p_maxwell_ray = 0.5 * eps_0 * (e_max_data**2)
        
        # Compare with 2gamma/R_cap
        if p_maxwell_ray > p_laplace_rayleigh:
            v_high = v_mid
        else:
            v_low = v_mid
    
    v_onset_rayleigh = v_high
    prev_onset_ray = v_onset_rayleigh
    
    print(f"** Found V_onset_rayleigh = {v_onset_rayleigh:.1f} V (after {solve_counter_ray} steps) **")
    
    # -------------------------------------------------------------------------
    # --- PART 2: Transition to Taylor Condition Onset ---
    # -------------------------------------------------------------------------
    print(f"\n--- Transitioning to Taylor Condition evaluation ---")
    
    model.parameter('V_ext', f'{v_onset_rayleigh} [V]')
    model.solve()
    model.java.result().export("data1").run()
    time.sleep(0.5) 

    df_ray = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
    df_ray = df_ray.drop(columns=['r_mesh', 'z_mesh'])
    
    z_center_eval = float(model.evaluate('z_cap_center'))
    df_ray['theta_deg'] = np.abs(np.degrees(np.arctan2(df_ray['r'], df_ray['z'] - z_center_eval)))
    df_ray = df_ray.sort_values('theta_deg')
    
    # --- ADD THESE LINES TO CAPTURE RAYLEIGH DATA ---
    rayleigh_meniscus_data[f'{r_cap_nm:g}nm_Angle'] = df_ray['theta_deg'].values
    rayleigh_meniscus_data[f'{r_cap_nm:g}nm_E'] = df_ray['E'].values
    # ------------------------------------------------
    
    e_taylor_evaluation = df_ray['E'].iloc[-1]
    p_maxwell_taylor_evaluation = 0.5 * eps_0 * (e_taylor_evaluation**2)
    
    if p_maxwell_taylor_evaluation > p_laplace_taylor:
        v_high_tay = v_onset_rayleigh
        v_low_tay = max(50, v_onset_rayleigh - 50) 
    else:
        v_low_tay = v_onset_rayleigh
        v_high_tay = v_onset_rayleigh + 50
    
    if v_high_tay <= v_low_tay: v_high_tay = v_low_tay + 50

    print(f"--- Bounding brackets for Taylor onset: [{v_low_tay:.1f}, {v_high_tay:.1f}] V ---")
    
    solve_counter_tay = 0
    # -------------------------------------------------------------------------
    # --- PART 3: Taylor Condition Binary Search ---
    # -------------------------------------------------------------------------
    while (v_high_tay - v_low_tay) > tol:
        v_mid_tay = (v_high_tay + v_low_tay) / 2
        model.parameter('V_ext', f'{v_mid_tay} [V]') 
        model.solve()
        
        model.java.result().export("data1").run()
        time.sleep(0.5) 
        solve_counter_tay += 1
        
        df_tay = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
        df_tay['theta_deg'] = np.abs(np.degrees(np.arctan2(df_tay['r'], df_tay['z'] - z_center_eval)))
        df_tay = df_tay.sort_values('theta_deg')
        
        e_tay_junction = df_tay['E'].iloc[-1]
        p_maxwell_tay = 0.5 * eps_0 * (e_tay_junction**2)
        
        if p_maxwell_tay > p_laplace_taylor:
            v_high_tay = v_mid_tay
        else:
            v_low_tay = v_mid_tay
    

    v_onset_taylor = v_high_tay
    print(f"** Found V_onset_taylor = {v_onset_taylor:.1f} V (after {solve_counter_tay} steps) **")

    # --- ADD THESE LINES TO CAPTURE FINAL TAYLOR DATA ---
    model.parameter('V_ext', f'{v_onset_taylor} [V]') 
    model.solve()
    model.java.result().export("data1").run()
    time.sleep(0.5) 
    
    df_tay_final = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
    df_tay_final['theta_deg'] = np.abs(np.degrees(np.arctan2(df_tay_final['r'], df_tay_final['z'] - z_center_eval)))
    df_tay_final = df_tay_final.sort_values('theta_deg')
    
    taylor_meniscus_data[f'{r_cap_nm:g}nm_Angle'] = df_tay_final['theta_deg'].values
    taylor_meniscus_data[f'{r_cap_nm:g}nm_E'] = df_tay_final['E'].values
    # ----------------------------------------------------

    # --- Append to Results Tracker ---
    # Note: Adjust the parameter string names inside get_param() if they differ slightly in your .mph file
    detailed_summary_data.append({
        'R_cap (nm)': r_cap * 1e9,
        'V_onset_Rayleigh (V)': v_onset_rayleigh,
        'V_onset_Taylor (V)': v_onset_taylor,
        'd (tip-electrode separation)': get_param('d'),
        'R_in (capillary_inner_radius)': get_param('R_inner'),
        'electrode_inner_radius': get_param('Ext_elec_R_i'),
        'capillary_depth': get_param('capillary_depth'),
        'IFE_spacing': get_param('IFE_spacing'),
        'meniscus_overflow_depth': get_param('meniscus_overflow_depth'), # Adjust name if needed
        'meniscus_overflow_thickness': get_param('meniscus_overflow_thickness') # Adjust name if needed
    })

# --- 4. EXCEL EXPORT (Results Summary & Final Parameters) ---
print("\nGenerating Summary Excel File...")

# DataFrame 1: The Results Summary
df_results = pd.DataFrame(detailed_summary_data)
df_results = df_results.sort_values('R_cap (nm)', ascending=False)

# DataFrame 2: All Final Parameters
all_params = model.parameters() # Returns a dict of all parameters
parsed_params = []

for p_name, p_expr in all_params.items():
    p_str = str(p_expr).strip()
    # Extract value and unit from standard COMSOL format like '40 [nm]'
    if '[' in p_str and ']' in p_str:
        val = p_str.split('[')[0].strip()
        unit = p_str.split('[')[1].split(']')[0].strip()
    else:
        val = p_str
        unit = ""
    
    parsed_params.append({
        "Parameter Name": p_name,
        "Value": val,
        "Units": unit
    })

df_final_params = pd.DataFrame(parsed_params)

# --- ADD THESE LINES TO FORMAT MENISCUS DATAFRAMES ---
df_rayleigh_meniscus = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in rayleigh_meniscus_data.items()]))
df_taylor_meniscus = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in taylor_meniscus_data.items()]))
# -----------------------------------------------------

# Write to a multi-sheet Excel file
excel_path = os.path.join(target_dir, "Detailed_Simulation_Summary.xlsx")
with pd.ExcelWriter(excel_path) as writer:
    df_results.to_excel(writer, sheet_name='Results_Summary', index=False)
    df_final_params.to_excel(writer, sheet_name='Final_Parameters', index=False)
    
    # --- ADD THESE LINES TO EXPORT THE NEW SHEETS ---
    df_rayleigh_meniscus.to_excel(writer, sheet_name='Rayleigh_Onset_Data', index=False)
    df_taylor_meniscus.to_excel(writer, sheet_name='Taylor_Onset_Data', index=False)
    # ------------------------------------------------


print(f"Data correctly saved to: {excel_path}")
print("\nAll capillary radius sweep simulations completed successfully!")