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
r_ratios = [1.0] # Multiple cap ratios to plot

# Dictionary to store: {ratio: {r_inner: v_onset}}
all_results = {ratio: {} for ratio in r_ratios}

# 3. Nested Loops
for r_inner in r_inner_list:
    # Set the inner radius parameter in COMSOL
    model.parameter('R_inner', f'{r_inner} [m]')
    
    for ratio in r_ratios:
        r_cap = r_inner * ratio
        p_laplace = (2 * gamma) / r_cap
        
        # Set the cap radius parameter
        model.parameter('R_cap', f'{r_cap} [m]')
        
        v_low, v_high = 0, 200
        tol = 0.5 
        
        print(f"\n--- Solving R_inner: {r_inner*1e9}nm | Ratio: {ratio} ---")
        
        while (v_high - v_low) > tol:
            v_mid = (v_high + v_low) / 2
            # Use the exact parameter name from your Global Definitions
            model.parameter('V_ext', f'{v_mid} [V]') 
            model.solve()
            
            # Use es3 to match your physics tag
            e_max = model.evaluate('maxop1(es3.normE)')
            p_maxwell = 0.5 * eps0 * (e_max**2)
            
            if p_maxwell > p_laplace:
                v_high = v_mid
            else:
                v_low = v_mid
        
        print(f"  Onset found: {v_high:.2f} V")
        all_results[ratio][r_inner] = v_high

# 4. Plotting
plt.figure(figsize=(10, 6))
for ratio, data in all_results.items():
    x = [r * 1e9 for r in data.keys()] # Convert to nm
    y = list(data.values())
    plt.plot(x, y, '-o', label=f'R_cap: {r_cap} nm')

plt.xlabel('R_inner (nm)')
plt.ylabel('Onset Voltage (V)')
plt.title('Onset Voltage vs Inner Radius for Different Cap Ratios')
plt.legend()
plt.grid(True)
plt.show()

plot_filename = f"V_Onset_Plot_{mph_filename}.pdf"
plot_path = os.path.join(folder_path, plot_filename)

plt.savefig(plot_path)
print(f"Plot saved to: {plot_path}")


plt.show()