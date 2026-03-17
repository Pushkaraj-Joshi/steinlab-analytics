# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 22:28:51 2026

@author: pjoshi11
"""

import mph
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from pathlib import Path

# --- 1. Setup Paths ---
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_08_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)
file_path = os.path.join(folder_path, 'meniscus_data.txt')

client = mph.start()
model = client.load(full_mph_path)

# --- 2. Define Physical Constants (in SI units) ---
eps_0 = 8.85418782e-12   # Vacuum permittivity (F/m)
q = 1.60217663e-19       # Elementary charge (C)
k_B = 1.380649e-23       # Boltzmann constant (J/K)
h = 6.62607015e-34       # Planck constant (J*s)
gamma = 0.072            # Surface tension (N/m)
T = 298.0                # Temperature in Kelvin

G0_eV = 1.5              # Fixed Activation Energy for plotting
r_inner_list = [20e-9, 40e-9, 60e-9, 80e-9]
r_cap_list = [16e-9, 8e-9, 4e-9] 
ext_elec_ri_list = [0] 

# Dictionary structure to track ratios: {ext_elec_ri: {rcap: {r_inner: v_onset}}}
all_results = {ri: {rcap: {} for rcap in r_cap_list} for ri in ext_elec_ri_list}

# --- 3. Main Execution ---
prev_onset = None
prev_r_inner = None

model.java.study('std1').run() # Initialize 'sol1'

for elec_ri in ext_elec_ri_list:
    model.parameter('Ext_elec_R_i', f'{elec_ri} [m]')
    
    for r_inner in r_inner_list:
        model.parameter('R_inner', f'{r_inner} [m]')
        R_base = float(model.evaluate('R_base'))
        alpha = float(model.evaluate('alpha'))
        print(f'alpha: {alpha}')
        
        # --- START NEW PLOT FOR THIS R_INNER ---
        plt.figure(figsize=(9, 6))
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'] # Support up to 4 r_caps
        
        for idx, rcap in enumerate(r_cap_list):
            r_cap = rcap
            z_center = (R_base - r_cap)/np.cos(alpha)
            p_laplace = (2 * gamma) / r_cap
            model.parameter('R_cap', f'{r_cap} [m]')
            
            # --- Bulletproof Bounding Logic ---
            if prev_onset is None:
                v_low = 0
                v_high = 200
            else:
                v_low = 0
                v_high = max(200, 2 * prev_onset) 
            
            tol = 0.5 
            print(f"\n--- Searching with Bounds: [{v_low:.1f}, {v_high:.1f}] V for R_inner: {r_inner*1e9:.1f}nm, R_cap: {r_cap*1e9:.1f}nm ---")
            
            # --- Binary Search for Onset ---
            while (v_high - v_low) > tol:
                v_mid = (v_high + v_low) / 2
                model.parameter('V_ext', f'{v_mid} [V]') 
                model.solve()
                
                e_max = model.evaluate('maxop1(es3.normE)')
                p_maxwell = 0.5 * eps_0 * (e_max**2)
                
                if p_maxwell > p_laplace:
                    v_high = v_mid
                else:
                    v_low = v_mid
            
            # Store results
            v_onset = v_high
            prev_onset = v_onset
            prev_r_inner = r_inner
            all_results[elec_ri][rcap][r_inner] = v_onset
            
            # --- Extract Data at Exact Onset Voltage ---
            print(f"Onset found at {v_onset:.1f} V. Extracting field data...")
            model.parameter('V_ext', f'{v_onset} [V]')
            model.solve() 
            model.java.result().export("data1").run()
            
            df = pd.read_csv(file_path, sep='\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
            df = df.drop(columns=['r_mesh', 'z_mesh'])
            
            z_center = float(model.evaluate('z_cap_center'))
            
            df['theta_deg'] = np.abs(np.degrees(np.arctan2(df['r'], df['z'] - z_center)))
            df = df.sort_values('theta_deg')
            
            E_onset = df['E'].values
            angles = df['theta_deg'].values

            # --- Emission Rate Calculation (1.5 eV only) ---
            pre_factor = eps_0 * E_onset * (k_B * T) / h
            barrier_lowering = np.sqrt((q**3 * E_onset) / (4 * np.pi * eps_0))

            G0_J = G0_eV * q
            exponent = - (G0_J - barrier_lowering) / (k_B * T)
            j_emission = pre_factor * np.exp(exponent)
            
            j_max = np.max(j_emission)
            j_normalized = j_emission / j_max
            
            # Plot the specific R_cap curve on the shared figure
            plt.plot(angles, j_normalized, 'o-', color=colors[idx % len(colors)], 
                     markersize=5, linewidth=2, label=f'R_cap: {r_cap*1e9:.1f} nm (Onset: {v_onset:.1f} V)')

        # --- Formatting Emission Plot (Executes after all R_caps for current R_inner) ---
        plt.title(f'Emission vs Angle (R_inner: {r_inner*1e9:.1f} nm, G0: {G0_eV} eV)')
        plt.xlabel('Angle from symmetry axis (degrees)')
        plt.ylabel(r'Normalized Emission Rate ($j/j_{max}$)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(title='Cap Variations')
        plt.tight_layout()
        
        plot_filename = f"Emission_rate_angular_distribution_Rinner_{r_inner*1e9:.1f}nm_G0_{G0_eV}eV.pdf"
        plot_path = os.path.join(folder_path, plot_filename)
        plt.savefig(plot_path)
        print(f"Combined emission plot saved to: {plot_path}")
        plt.close() # Close figure to prep for next R_inner


# --- 4. Final Plotting: Onset Voltage vs Geometric Variations ---
plt.figure(figsize=(10, 6))
markers = ['o', 's', '^']

for elec_ri, rcap_data in all_results.items():
    for (rcap, r_inner_data), marker in zip(rcap_data.items(), markers):
        
        # Sort the dictionary keys (r_inner) to ensure the line plots smoothly left-to-right
        sorted_r_inner = sorted(r_inner_data.keys())
        x = [r * 1e9 for r in sorted_r_inner] 
        y = [r_inner_data[r] for r in sorted_r_inner]
        
        plt.plot(x, y, linestyle='-', marker=marker, label=f'Elec Ri: {elec_ri*1e3} mm, R_cap: {rcap*1e9:.1f} nm')

plt.xlabel('Tip Radius R_inner (nm)')
plt.ylabel('Onset Voltage (V)')
plt.title('Onset Voltage vs Tip Radius (Geometric Variations)')
plt.legend()
plt.grid(True)

plot_filename = "V_Onset_Plot_cap_radius_inner_radius_variations.pdf"
plot_path = os.path.join(folder_path, plot_filename)
plt.savefig(plot_path)
print(f"\nFinal onset plot saved to: {plot_path}")

plt.show()

# --- 5. Export Results to CSV ---
print("\nExporting raw onset voltage data to CSV...")

# Flatten the nested dictionary into a list of rows
csv_data = []
for elec_ri, rcap_data in all_results.items():
    for rcap, r_inner_data in rcap_data.items():
        for r_inner, v_onset in r_inner_data.items():
            csv_data.append({
                'Electrode_Ri (m)': elec_ri,
                'R_cap (m)': rcap,
                'R_inner (m)': r_inner,
                'V_onset (V)': v_onset
            })

# Convert to a Pandas DataFrame
df_results = pd.DataFrame(csv_data)

# Save to the working folder
csv_filename = "Onset_Voltages_Summary.csv"
csv_path = os.path.join(folder_path, csv_filename)
df_results.to_csv(csv_path, index=False)

print(f"Data successfully saved to: {csv_path}")