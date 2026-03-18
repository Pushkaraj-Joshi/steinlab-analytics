# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 21:56:39 2026

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
# Add time delay library in case file IO is slow
import time

# --- 1. Setup Paths & Dynamic Folder Creation ---
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_14_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)
# The file name COMSOL will export the meniscus data to
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
r_cap_list = [1.5e-9, 1e-9,0.75e-9] # in meters

r_inner_fixed = 40e-9
cap_depth_fixed = 100e-6
ife_spacing_fixed = 0.5e-6 # Fixed to 0.5 um as requested

# Apply Fixed Parameters to COMSOL BEFORE the loop
model.parameter('R_inner', f'{r_inner_fixed} [m]')
model.parameter('IFE_spacing', f'{ife_spacing_fixed} [m]') 
model.parameter('Ext_elec_R_i', '0.0 [m]')
model.parameter('capillary_depth', f'{cap_depth_fixed} [m]') 

# --- Data Trackers ---
onset_rayleigh_data = {}  # Tracks {r_cap: v_onset_rayleigh}
onset_taylor_data = {}    # Tracks {r_cap: v_onset_taylor}

# Remove unused data tracker from original script: emission_profiles = {}

# --- 3. Main Execution (Sweep of R_cap) ---
# Run initial study step
model.java.study('std1').run()

prev_onset_ray = None 

# Start loop for R_cap
for r_cap in r_cap_list:
    
    r_cap_nm = r_cap * 1e9
    model.parameter('R_cap', f'{r_cap} [m]')
    
    print(f"\n{'='*60}")
    print(f"Starting iteration for Capillary Radius (R_cap): {r_cap_nm:g} nm")
    print(f"{'='*60}")
    
    # Calculate Fixed pressures for THIS specific R_cap
    p_laplace_rayleigh = (2 * gamma) / r_cap
    p_laplace_taylor = gamma / r_cap
    
    # -------------------------------------------------------------------------
    # --- PART 1: Calculate Rayleigh Onset (Evaluates Maximum Field) ---
    # -------------------------------------------------------------------------
    print(f"\n--- Searching for Rayleigh Onset (V_onset_rayleigh) ---")
    
    # Bounding logic (uses floor/ceiling logic from previous successful sweep)
    if prev_onset_ray is None:
        v_low = 50 # Using user's floor of 50
        v_high = 250
    else:
        v_low = 50
        # Ceiling of 700 or 2 times previous onset
        v_high = max(250, 2 * prev_onset_ray) 
    
    tol = 1.0
    print(f"--- Bounding brackets: [{v_low:.1f}, {v_high:.1f}] V ---")
    
    solve_counter_ray = 0
    # Rayleigh Binary Search
    while (v_high - v_low) > tol:
        v_mid = (v_high + v_low) / 2
        model.parameter('V_ext', f'{v_mid} [V]') 
        model.solve()
        solve_counter_ray += 1
        
        # Original logic: Evaluate maximum field everywhere on meniscus
        e_max = model.evaluate('maxop1(es3.normE)')
        p_maxwell_ray = 0.5 * eps_0 * (e_max**2)
        
        # Compare with 2gamma/R_cap
        if p_maxwell_ray > p_laplace_rayleigh:
            v_high = v_mid
        else:
            v_low = v_mid
    
    v_onset_rayleigh = v_high
    prev_onset_ray = v_onset_rayleigh
    onset_rayleigh_data[r_cap] = v_onset_rayleigh
    
    print(f"** Found V_onset_rayleigh = {v_onset_rayleigh:.1f} V (after {solve_counter_ray} steps) **")
    
    # -------------------------------------------------------------------------
    # --- PART 2: Transition to Taylor Condition Onset (Nested Data Evaluation) ---
    # -------------------------------------------------------------------------
    print(f"\n--- Transitioning to Taylor Condition evaluation ---")
    print(f"Evaluating junction point at V = {v_onset_rayleigh:.1f} V...")
    
    # Solve at found Rayleigh voltage to export data and decide on the bracket
    model.parameter('V_ext', f'{v_onset_rayleigh} [V]')
    model.solve()
    model.java.result().export("data1").run()
    # Tiny delay to ensure file write completes
    time.sleep(0.5) 

    # Load and process the exported data
    # Standard output columns: r_mesh, z_mesh, r, z, es3.normE
    df_ray = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
    df_ray = df_ray.drop(columns=['r_mesh', 'z_mesh'])
    
    # Calculate angle from symmetry axis to sort data
    # (Using user's provided logic based on z_cap_center evaluation)
    z_center_eval = float(model.evaluate('z_cap_center'))
    df_ray['theta_deg'] = np.abs(np.degrees(np.arctan2(df_ray['r'], df_ray['z'] - z_center_eval)))
    
    # Sort data by angle ascending
    df_ray = df_ray.sort_values('theta_deg')
    
    # Find the field AT the very last data point (evaluated node) on the meniscus
    e_taylor_evaluation = df_ray['E'].iloc[-1]
    p_maxwell_taylor_evaluation = 0.5 * eps_0 * (e_taylor_evaluation**2)
    
    # Decide on Taylor bracket initialization
    if p_maxwell_taylor_evaluation > p_laplace_taylor:
        # If maxwell pressure is higher, assign v_high as the onset obtained for rayleigh
        v_high_tay = v_onset_rayleigh
        # And use v_low as 100V below this
        v_low_tay = v_onset_rayleigh - 100
        # In case previous was really low, enforce reasonable bounds
        if v_low_tay < 50: v_low_tay = 50 
    else:
        # And vice versa: v_low is rayleigh
        v_low_tay = v_onset_rayleigh
        # (New bracket ceiling) use v_high as 100V above this
        v_high_tay = v_onset_rayleigh + 100
    
    # Ensure a valid search bracket
    if v_high_tay <= v_low_tay: v_high_tay = v_low_tay + 100

    print(f"--- Bounding brackets for Taylor onset: [{v_low_tay:.1f}, {v_high_tay:.1f}] V ---")
    print(f"Searching for Taylor Onset (V_onset_taylor)...")
    
    solve_counter_tay = 0
    # -------------------------------------------------------------------------
    # --- PART 3: Taylor Condition Binary Search (Nested Data Extraction) ---
    # -------------------------------------------------------------------------
    while (v_high_tay - v_low_tay) > tol:
        v_mid_tay = (v_high_tay + v_low_tay) / 2
        model.parameter('V_ext', f'{v_mid_tay} [V]') 
        # Inside Taylor BS, perform NESTED solve and export step
        model.solve()
        # Overwrite the same meniscus_data.txt file
        model.java.result().export("data1").run()
        # Tiny delay to ensure file write completes
        time.sleep(0.5) 
        solve_counter_tay += 1
        
        # Load and process data at current v_mid step
        df_tay = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
        df_tay = df_tay.drop(columns=['r_mesh', 'z_mesh'])
        df_tay['theta_deg'] = np.abs(np.degrees(np.arctan2(df_tay['r'], df_tay['z'] - z_center_eval)))
        df_tay = df_tay.sort_values('theta_deg')
        
        # Get field AT node at the last data point
        e_tay_junction = df_tay['E'].iloc[-1]
        
        # Calculate P_maxwell with evaluated E field
        p_maxwell_tay = 0.5 * eps_0 * (e_tay_junction**2)
        
        # Compare P_maxwell (evaluated at junction) with P_laplace (fixed at gamma/R_cap)
        if p_maxwell_tay > p_laplace_taylor:
            v_high_tay = v_mid_tay
        else:
            v_low_tay = v_mid_tay
    
    v_onset_taylor = v_high_tay
    onset_taylor_data[r_cap] = v_onset_taylor
    print(f"** Found V_onset_taylor = {v_onset_taylor:.1f} V (after {solve_counter_tay} steps) **")

# --- 4. MASTER PLOTTING & EXPORT ---
print("\nGenerating Master Plot and Data Files...")

# Prepare summary dataframe for plotting and export
# Store the data in pairs for side-by-side visualization
summary_list = []
for k in r_cap_list:
    r_nm_disp = k * 1e9
    summary_list.append({
        'R_cap (nm)': r_nm_disp,
        'V_onset_Rayleigh (V)': onset_rayleigh_data[k],
        'V_onset_Taylor (V)': onset_taylor_data[k]
    })
df_summary = pd.DataFrame(summary_list)
# Sort final table by radius decreasing (original sweep order)
df_summary = df_summary.sort_values('R_cap (nm)', ascending=False)

# Extract the global min and max to define common bounds
# We look at both columns to find the overall spread
v_min = df_summary[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].min().min()
v_max = df_summary[['V_onset_Rayleigh (V)', 'V_onset_Taylor (V)']].max().max()

# Add a 5-10% padding so points aren't touching the very top/bottom of the chart
padding = (v_max - v_min) * 0.1
y_limits = (v_min - padding, v_max + padding)

# Master Plot: Two y-axis (Rayleigh vs Taylor) against R_cap
fig, ax1 = plt.figure(figsize=(10, 6)), plt.gca()

# X-axis data (radius in nm)
x_radii = df_summary['R_cap (nm)'].values

# Plot 1 (Ax1): Rayleigh condition on left axis (Blue)
color1 = '#1f77b4' # Original script blue
y_vonsets_ray = df_summary['V_onset_Rayleigh (V)'].values
line1 = ax1.plot(x_radii, y_vonsets_ray, linestyle='-', marker='o', 
                 color=color1, markersize=8, linewidth=2, label='V_onset (Rayleigh Condition: 2γ/R_cap vs Max E-field)')

# Set x-axis labels (for the shared axis)
ax1.set_xlabel('Capillary Radius ($R_{cap}$) (nm)')
# (Required logic) Set log scale for x-axis as values span 40 to 2 nm
ax1.set_xscale('log') 

# Axis 1 configuration (Blue label, title)
ax1.set_ylabel('Onset Voltage (Rayleigh) (V)', color=color1)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_ylim(y_limits) # Apply synchronized limits
ax1.grid(True, which="both", linestyle='--', alpha=0.7)

# Create Plot 2 (Ax2): Taylor condition on right axis (Red), sharing x-axis
ax2 = ax1.twinx() 
color2 = '#d62728' # Original script red
y_vonsets_tay = df_summary['V_onset_Taylor (V)'].values
line2 = ax2.plot(x_radii, y_vonsets_tay, linestyle='-', marker='D', 
                 color=color2, markersize=8, linewidth=2, label='V_onset (Taylor Condition: γ/R_cap vs Evaluation Point E-field)')

# Axis 2 configuration (Red label, different range)
ax2.set_ylabel('Onset Voltage (Taylor) (V)', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylim(y_limits) # Apply synchronized limits (same as ax1)

# Master title and configuration
plt.title(f'Comparison of Onset Voltage Conditions vs Capillary Radius\n($R_{{in}}$=40nm, Depth=100$\mu$m, IFE=0.5$\mu$m)')

# Combine legends from both axes
lines = line1 + line2
labels = [l.get_label() for l in lines]
# Place legend outside or inside clearly
ax1.legend(lines, labels, loc='lower left', bbox_to_anchor=(0.0, -0.28), frameon=True)

fig.tight_layout()
# Adjust layout to make room for legend below
plt.subplots_adjust(bottom=0.25)
plt.savefig(os.path.join(target_dir, "Master_V_Onset_Comparison_vs_R_cap.pdf"))
plt.close()

# Export Summary Data to Excel
excel_path = os.path.join(target_dir, "Master_CapRadius_Sweep_Summary.xlsx")
# Convert to simplified summary sheet
df_summary.to_excel(excel_path, sheet_name='Summary_Data', index=False)

# Clean up exported data files from folder_path if needed, or leave for debug
# if os.path.exists(file_path): os.remove(file_path)

print(f"Data correctly saved in: {target_dir}")
print("\nAll capillary radius sweep simulations completed successfully!")