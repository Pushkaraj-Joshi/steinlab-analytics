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
import numpy as np

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
r_inner_list = [20e-9] #, 80e-9, 100e-9, 125e-9]
r_ratios = [0.1] 
ext_elec_ri_list = [0] # Converting mm to m

# Dictionary structure: {ext_elec_ri: {r_inner: v_onset}}
all_results = {ri: {} for ri in ext_elec_ri_list}

# 3. Triple Nested Loops
# Initialize a variable to store the previous onset outside the loops
prev_onset = None
prev_r_inner = None

# model.java.study('std1').run() # Runs the study once to initialize 'sol1'

for elec_ri in ext_elec_ri_list:
    model.parameter('Ext_elec_R_i', f'{elec_ri} [m]')
    
    for r_inner in r_inner_list:
        model.parameter('R_inner', f'{r_inner} [m]')
        
        for ratio in r_ratios:
            r_cap = r_inner * ratio
            taylor_Emax = np.sqrt((2*gamma*np.cos(49.3))/(eps0*r_cap))
            model.parameter('R_cap', f'{r_cap} [m]')
            
            # --- START MODIFIED BOUNDING LOGIC ---
            if prev_onset is None:
                # First run ever: Use standard wide bounds
                v_low = 0
                v_high = 200
            elif r_inner != prev_r_inner:
                # Case: r_inner changed. Use ratio-based scaling
                # High bound = 2 * (r_inner_current / r_inner_previous) * prev_onset
                v_low = prev_onset
                v_high = 2 * (r_inner / prev_r_inner) * prev_onset
            else:
                # Case: r_inner stayed same, but r_cap (ratio) changed
                # High bound = 2 * prev_onset
                v_low = prev_onset
                v_high = 2 * prev_onset
           
            tol = 0.5 
            print(f"\n--- Searching with Bounds: [{v_low:.1f}, {v_high:.1f}] V ---")
            
            while (v_high - v_low) > tol:
                v_mid = (v_high + v_low) / 2
                model.parameter('V_ext', f'{v_mid} [V]') 
                model.solve()
                
                e_max = model.evaluate('maxop1(es3.normE)')
                print(f'Emax: {e_max}')
        
                
                if e_max > taylor_Emax:
                    v_high = v_mid
                else:
                    v_low = v_mid
            
            # Store results and update tracking variables for the next iteration
            prev_onset = v_high
            prev_r_inner = r_inner
            all_results[elec_ri][r_inner] = v_high
            
            # --- Data Extraction and Profile Plotting ---
            try:
                # 1. Extract the data (Coordinate in col 0, Field Value in col 1)
                # Ensure cln1 dataset is linked to Solution 1 in COMSOL
                model.java.result().dataset('cln1').set('data', 'sol1')
                
                profile_data = model.evaluate('comp3.es3.normE', dataset='Cut Line 2D 1')
                          
                # 2. Setup the Profile Plot
                plt.figure(figsize=(8, 4))
                
                # Assuming profile_data is a numpy array where:
                # Row 0 or Col 0 is the distance along the line
                # Row 1 or Col 1 is the electric field magnitude (es3.normE)
                dist = profile_data[0] 
                field = profile_data[1]
                
                plt.plot(dist, field, 'r-', linewidth=2)
                plt.title(f'Field Profile at Onset: Ri={r_inner*1e9:.1f}nm, Elec_Ri={elec_ri*1e3:.1f}mm')
                plt.xlabel('Distance along Cut Line (m)')
                plt.ylabel('Electric Field (V/m)')
                plt.grid(True)
                
                # 3. Save the specific profile plot
                profile_plot_name = f"Profile_Ri_{r_inner*1e9:.0f}_Elec_{elec_ri*1e3:.0f}.pdf"
                plt.savefig(os.path.join(folder_path, profile_plot_name))
                plt.close() # Close to save memory during long sweeps
                
                print(f"   Field profile plot saved: {profile_plot_name}")
            
            except Exception as e:
                print(f"   Skipping profile plot: {e}")

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

plot_filename = f"V_Onset_Plot_annular_electrode_{mph_filename}_2.pdf"
plot_path = os.path.join(folder_path, plot_filename)

plt.savefig(plot_path)
print(f"Plot saved to: {plot_path}")


plt.show()