# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 22:28:51 2026

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

# --- 1. Setup Paths & Dynamic Folder Creation ---
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_14_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)
file_path = os.path.join(folder_path, 'meniscus_data.txt')

base_name = os.path.splitext(mph_filename)[0] 
plots_base_dir = os.path.join(folder_path, f"Plots - {base_name} - IFE_Sweep")

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
q = 1.60217663e-19       
k_B = 1.380649e-23       
h = 6.62607015e-34       
gamma = 0.072            
T = 298.0                
G0_eV = 1.5              

# --- Fixed Parameters & Study Lists ---
r_inner_fixed = 40e-9
r_cap_fixed = 10e-9
cap_depth_fixed = 100e-6

ife_spacing_list = [0.5e-6, 10e-6, 50e-6, 100e-6] # in meters

# Apply Fixed Parameters to COMSOL
model.parameter('R_inner', f'{r_inner_fixed} [m]')
model.parameter('R_cap', f'{r_cap_fixed} [m]')
model.parameter('Ext_elec_R_i', '0.0 [m]')
# Apply fixed capillary depth
model.parameter('capillary_depth', f'{cap_depth_fixed} [m]') 

# Fixed Laplace pressure 
p_laplace = (2 * gamma) / r_cap_fixed

# --- Data Trackers ---
onset_data = {}         # Tracks {ife_spacing: v_onset}
emission_profiles = {}  # Tracks {ife_spacing: dataframe_of_emission_data}

# --- 3. Main Execution ---
model.java.study('std1').run()

prev_onset = None 

for ife_spacing in ife_spacing_list:
    
    ife_um = ife_spacing * 1e6
    model.parameter('IFE_spacing', f'{ife_spacing} [m]')
    
    print(f"\n{'='*50}")
    print(f"Starting iteration for IFE Spacing: {ife_um:g} um")
    print(f"{'='*50}")
    
    # --- Bounding Logic ---
    if prev_onset is None:
        v_low = 50
        v_high = 700
    else:
        v_low = 50
        # Start the next bound using the previous onset to save time
        v_high = max(700, 2 * prev_onset) 
    
    tol = 1.0
    print(f"--- Searching bounds [{v_low:.1f}, {v_high:.1f}] V ---")
    
    solve_counter = 0
    # --- Binary Search ---
    while (v_high - v_low) > tol:
        v_mid = (v_high + v_low) / 2
        model.parameter('V_ext', f'{v_mid} [V]') 
        model.solve()
        solve_counter += 1
        
        e_max = model.evaluate('maxop1(es3.normE)')
        p_maxwell = 0.5 * eps_0 * (e_max**2)
        
        if p_maxwell > p_laplace:
            v_high = v_mid
        else:
            v_low = v_mid
    
    v_onset = v_high
    prev_onset = v_onset
    onset_data[ife_spacing] = v_onset
    
    # --- Extract Data for Emission Plot ---
    print(f"Onset found at {v_onset:.1f} V after {solve_counter} iterations. Extracting data...")
    model.parameter('V_ext', f'{v_onset} [V]')
    model.solve() 
    model.java.result().export("data1").run()
    
    df = pd.read_csv(file_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
    df = df.drop(columns=['r_mesh', 'z_mesh'])
    
    z_center_eval = float(model.evaluate('z_cap_center'))
    df['theta_deg'] = np.abs(np.degrees(np.arctan2(df['r'], df['z'] - z_center_eval)))
    df = df.sort_values('theta_deg')
    
    E_onset = df['E'].values
    angles = df['theta_deg'].values

    # --- Emission Rate Calculation ---
    pre_factor = eps_0 * E_onset * (k_B * T) / h
    barrier_lowering = np.sqrt((q**3 * E_onset) / (4 * np.pi * eps_0))
    G0_J = G0_eV * q
    exponent = - (G0_J - barrier_lowering) / (k_B * T)
    j_emission = pre_factor * np.exp(exponent)
    
    j_normalized = j_emission / np.max(j_emission)
    
    # Store data for this specific IFE spacing
    s_angle = pd.Series(angles, name=f'Angle_deg_{ife_um:g}um')
    s_jnorm = pd.Series(j_normalized, name=f'j_norm_{ife_um:g}um')
    s_efield = pd.Series(E_onset, name=f'E_field_{ife_um:g}um')
    
    emission_profiles[ife_spacing] = pd.concat([s_angle, s_jnorm, s_efield], axis=1)


# --- 4. MASTER PLOTTING & EXPORT ---
print("\nGenerating Master Plots and Data Files...")

# Plot 1: Combined Normalized Emission vs Angle
plt.figure(figsize=(10, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

for idx, ife_spacing in enumerate(ife_spacing_list):
    ife_um = ife_spacing * 1e6
    df_plot = emission_profiles[ife_spacing]
    plt.plot(df_plot[f'Angle_deg_{ife_um:g}um'], 
             df_plot[f'j_norm_{ife_um:g}um'], 
             'o-', color=colors[idx % len(colors)], markersize=4, linewidth=2, 
             label=f'IFE: {ife_um:g} $\mu$m ($V_{{onset}}$: {onset_data[ife_spacing]:.1f} V)')

plt.title(f'Normalized Emission vs Angle for Various IFE Spacings\n($R_{{in}}$=40nm, $R_{{cap}}$=10nm, Depth=100$\mu$m)')
plt.xlabel('Angle from symmetry axis (degrees)')
plt.ylabel(r'Normalized Emission Rate ($j/j_{max}$)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(target_dir, "Master_Emission_vs_Angle.pdf"))
plt.close()

# Plot 2: Onset Voltage vs IFE Spacing
plt.figure(figsize=(9, 6))
x_spacings = [spacing * 1e6 for spacing in ife_spacing_list]
y_vonsets = [onset_data[spacing] for spacing in ife_spacing_list]

plt.plot(x_spacings, y_vonsets, linestyle='-', marker='D', color='#d62728', markersize=8, linewidth=2)
plt.title(f'Onset Voltage vs IFE Spacing\n($R_{{in}}$=40nm, $R_{{cap}}$=10nm, Depth=100$\mu$m)')
plt.xlabel('IFE Spacing ($\mu$m)')
plt.ylabel('Onset Voltage (V)')
# Using a logarithmic x-scale can be helpful when sweeping values from 0.5 to 100
plt.xscale('log') 
plt.grid(True, which="both", ls="--", alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(target_dir, "Master_V_Onset_vs_IFESpacing.pdf"))
plt.close()

# Export Data to Excel
csv_summary = [{'IFE_Spacing (um)': k*1e6, 'V_onset (V)': v} for k, v in onset_data.items()]
df_summary = pd.DataFrame(csv_summary)

excel_path = os.path.join(target_dir, "Master_IFE_Spacing_Data.xlsx")
with pd.ExcelWriter(excel_path) as writer:
    # Sheet 1: Onset summary
    df_summary.to_excel(writer, sheet_name='V_Onset_Summary', index=False)
    
    # Put all emission profiles into a single combined sheet side-by-side
    df_combined_emission = pd.concat(emission_profiles.values(), axis=1)
    df_combined_emission.to_excel(writer, sheet_name='Emission_Profiles', index=False)

print(f"Data correctly saved in: {target_dir}")
print("\nAll simulations completed successfully!")