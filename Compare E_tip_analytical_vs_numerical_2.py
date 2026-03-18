# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 20:06:12 2026

@author: pjoshi11
"""

import mph
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import shutil  # <-- Imported for file copying

# --- 1. Setup Paths ---
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_14_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)

plots_base_dir = os.path.join(folder_path, "Plots_Distance_Sweep")
timestamp_str = datetime.now().strftime("%b-%d-%Y_%H-%M-%S")
target_dir = os.path.join(plots_base_dir, timestamp_str)
os.makedirs(target_dir, exist_ok=True)

# --- 1.5 Copy Script and COMSOL File ---
# Copy the COMSOL file
try:
    shutil.copy2(full_mph_path, target_dir)
    print(f"Success: Copied COMSOL file to {target_dir}")
except Exception as e:
    print(f"Warning: Could not copy COMSOL file. Error: {e}")

# Copy this Python script
try:
    script_path = os.path.abspath(__file__)
    shutil.copy2(script_path, target_dir)
    print(f"Success: Copied Python script to {target_dir}")
except NameError:
    print("Note: Running in an interactive environment (like Jupyter). Automatic script copying skipped.")
except Exception as e:
    print(f"Warning: Could not copy script. Error: {e}")

# --- 2. Initialize COMSOL & Constants ---
client = mph.start()
model = client.load(full_mph_path)

# Fixed Parameters
r_inner_fixed = 40e-9 # 40nm
r_cap_fixed = 4e-9 # 10 nm
e_target = 1e9      # Target Electric Field: 1 V/nm (10^9 V/m)
v_test = 100.0      # Arbitrary test voltage for linear scaling

# Apply fixed parameters
model.parameter('R_cap', f'{r_cap_fixed} [m]')
model.parameter('V_ext', f'{v_test} [V]')
model.parameter('R_inner', f'{r_inner_fixed} [m]')

# Define sweep for z0 (tip-extractor separation 'd' in meters)
# Sweeping from 10 um to 10 mm using a logarithmic progression
z0_list = np.logspace(np.log10(10e-6), np.log10(7e-3), num=16) 

results_data = []

# --- 3. Main Execution (Sweep of z0) ---
print(f"\nTarget Electric Field: {e_target/1e9:g} V/nm")
print(f"Capillary Radius: {r_cap_fixed*1e9:g} nm")
print("-" * 50)

for z0 in z0_list:
    print(f"Solving for Separation (z0): {z0*1e6:.1f} um...")
    
    # Assuming the separation parameter in COMSOL is named 'd'
    model.parameter('d', f'{z0} [m]')
    model.solve()
    
    # --- EVALUATE MAXIMUM FIELD FROM EXPORTED TEXT FILE ---
    
    try:
        # 1. Run the Export node in COMSOL to generate the .txt file
        # Replace 'data1' with the actual tag of your Export node in the COMSOL tree
        # (Look under Results > Export in your COMSOL model)
        model.java.result().export("data1").run()
        
        # 2. Define the path where COMSOL is saving that text file
        # IMPORTANT: Make sure this matches the filename/path set inside your COMSOL Export node
        txt_export_path = os.path.join(folder_path, 'meniscus_data.txt')
        
        # 3. Read the text file using Pandas
        # COMSOL .txt files are usually space/tab-delimited and use '%' for comments/headers
        df_meniscus = pd.read_csv(txt_export_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
        
        # 4. Extract the absolute maximum Electric Field
        # This assumes the E-field (normE) is the last column in your text file. 
        # If it's a different column (like the 3rd column), change `iloc[:, -1]` to `iloc[:, 2]`.
        e_sim_test = float(df_meniscus.iloc[:, -1].max())
        
        print(f"     Max E-field found in txt: {e_sim_test:g} V/m")
        
    except Exception as e:
        print(f"  -> Error reading/processing meniscus text file: {e}")
        e_sim_test = np.nan
        
    # ------------------------------------------------------
        
    # LINEAR SCALING: Calculate required V to reach E_target
    if not np.isnan(e_sim_test):
        v_required_sim = v_test * (e_target / e_sim_test)
    else:
        v_required_sim = np.nan
        
    # Calculate Analytical V required
    v_required_analytical = (e_target * r_cap_fixed / np.sqrt(2)) * np.log((4 * z0) / r_cap_fixed)
    
    results_data.append({
        'Separation_z0 (m)': z0,
        'Separation_z0 (um)': z0 * 1e6,
        'V_Required_Sim (V)': v_required_sim,
        'V_Required_Analytical (V)': v_required_analytical
    })

# --- 4. Export & Plotting ---
df_results = pd.DataFrame(results_data)

excel_path = os.path.join(target_dir, "Distance_Sweep_V_Required.xlsx")
df_results.to_excel(excel_path, index=False)
print(f"\nData saved to: {excel_path}")

# Plotting
plt.figure(figsize=(9, 6))

# Plotting on a semilog-x axis to easily see the logarithmic dependency
plt.semilogx(df_results['Separation_z0 (um)'], df_results['V_Required_Sim (V)'], 
             marker='o', linestyle='-', color='#1f77b4', linewidth=2, label='COMSOL Simulated')

plt.semilogx(df_results['Separation_z0 (um)'], df_results['V_Required_Analytical (V)'], 
             marker='s', linestyle='--', color='#d62728', linewidth=2, label='Analytical Model')

plt.xlabel('Tip-Extractor Separation $z_0$ ($\mu$m) [Log Scale]', fontsize=12)
plt.ylabel(f'Required Voltage (V) to reach {e_target/1e9:g} V/nm', fontsize=12)
plt.title('Required Voltage vs. Tip-Extractor Separation\n$V \propto \ln(4z_0/r_c)$ Verification, R-cap = {r_cap_fixed*1e9}nm ', fontsize=14)
plt.grid(True, which="both", linestyle='--', alpha=0.7)
plt.legend(fontsize=11)

plt.tight_layout()

plot_path = os.path.join(target_dir, "Required_Voltage_vs_Separation.pdf")
plt.savefig(plot_path, format='pdf')
print(f"Saved plot to: {plot_path}")

plt.show()