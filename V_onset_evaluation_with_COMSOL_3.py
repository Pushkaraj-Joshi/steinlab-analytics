# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 22:28:51 2026

@author: pjoshi11
"""

import mph
import matplotlib.pyplot as plt
import os
from datetime import datetime
from pathlib import Path

# 1. Setup Paths
# Replace this with your actual folder path
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_08_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)

client = mph.start()
model = client.load(full_mph_path)

# 2. Constants & Parameters
gamma = 0.072 
eps0 = 8.854e-12
r_inner_list = [20e-9, 40e-9, 60e-9, 80e-9, 100e-9, 125e-9]
r_ratios = [1.0] 
ext_elec_ri_list = [0, 4e-3, 8e-3, 12e-3] # Converting mm to m

# Dictionary structure: {ext_elec_ri: {r_inner: v_onset}}
all_results = {ri: {} for ri in ext_elec_ri_list}

# 3. Triple Nested Loops
for elec_ri in ext_elec_ri_list:
    # Set the annular electrode inner radius
    model.parameter('Ext_elec_R_i', f'{elec_ri} [m]')
    
    for r_inner in r_inner_list:
        model.parameter('R_inner', f'{r_inner} [m]')
        
        for ratio in r_ratios:
            r_cap = r_inner * ratio
            p_laplace = (2 * gamma) / r_cap
            model.parameter('R_cap', f'{r_cap} [m]')
            
            v_low, v_high = 0, 1000 # Increased high bound for annular gaps
            tol = 0.5 
            
            print(f"\n--- Elec_Ri: {elec_ri*1e3}mm | R_inner: {r_inner*1e9}nm ---")
            
            while (v_high - v_low) > tol:
                v_mid = (v_high + v_low) / 2
                model.parameter('V_ext', f'{v_mid} [V]') 
                model.solve()
                
                # Use es3 and maxop1 from your model definitions
                e_max = model.evaluate('maxop1(es3.normE)')
                p_maxwell = 0.5 * eps0 * (e_max**2)
                
                if p_maxwell > p_laplace:
                    v_high = v_mid
                else:
                    v_low = v_mid
            
            print(f"   Onset: {v_high:.2f} V")
            all_results[elec_ri][r_inner] = v_high

# 4. Plotting & Archiving
plt.figure(figsize=(10, 6))
for elec_ri, data in all_results.items():
    x = [r * 1e9 for r in data.keys()] 
    y = list(data.values())
    plt.plot(x, y, '-o', label=f'Electrode Ri: {elec_ri*1e3} mm')

plt.xlabel('Tip Radius R_inner (nm)')
plt.ylabel('Onset Voltage (V)')
plt.title('Onset Voltage vs Tip Radius (Annular Electrode Study)')
plt.legend()
plt.grid(True)

plot_filename = f"V_Onset_Plot_annular_electrode_{mph_filename}.pdf"
plot_path = os.path.join(folder_path, plot_filename)

plt.savefig(plot_path)
print(f"Plot saved to: {plot_path}")


plt.show()