# -*- coding: utf-8 -*-
"""
Created on Mon Feb  9 13:12:45 2026

@author: pjoshi11
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import os
import shutil

# 1. Setup paths based on your file location
dataset_path = r"C:\Users\pjoshi11\Documents\COMSOL_working files\Studies\Dataset_E_field_003.csv"
output_dir = os.path.dirname(os.path.abspath(dataset_path))

# 1. Define the exact columns as they appear in your long-format file
# This matches the order: r, z, R_inner, R_cap, d, V_ext, es3.normE
column_names = ['r', 'z', 'R_inner', 'R_cap', 'd', 'V_ext', 'E_field']

# 2. Define the data types (float64) to ensure E+09 is handled correctly
data_types = {col: 'float64' for col in column_names}

# 3. Use the high-speed loader
# We skip 9 lines to bypass ALL text/header rows entirely
df = pd.read_csv(
    dataset_path, 
    skiprows=9, 
    sep=None, 
    engine='python', 
    names=column_names, 
    dtype=data_types
)

# Round geometry to 9 decimal places to fix floating point noise
df['R_inner'] = df['R_inner'].round(9)
df['V_ext'] = df['V_ext'].round(2)

R_inner = df['R_inner'].unique()
V_ext = df['V_ext'].unique()
d = df['d'].unique()

# 4. Immediate Verification
print(f"Dataset loaded with {len(df)} rows.")
print(f"Maximum Field Value: {df['E_field'].max():.2e} V/m") # Now safe to format as .2e

# 3. Define Extraction Geometry (Using your nm coordinates)
r0, z0 = 0.0, 0.0  # Nanotip apex location
distances = np.linspace(0, 5e-7, 5000)  # Extract up to 500nm from tip
angles_deg = [0]


# --- TEST SECTION: Single Parameter Set ---
# Choose specific values from your parametric sweep
test_v_ext = 80.0

for test_r_in in R_inner:
    # Filter the 3M+ row dataframe for just this combination
    group = df[(df['V_ext'] == test_v_ext) & (df['R_inner'] == test_r_in)].copy()
    
    if group.empty:
        print(f"Warning: No data found for V={test_v_ext}, R_in={test_r_in}")
    else:
        plt.figure(figsize=(10, 6))
        
        for angle in angles_deg:
            theta = np.radians(angle)
            r_query = r0 + distances * np.sin(theta)
            z_query = z0 + distances * np.cos(theta)
            
            # Interpolate using the 'E_field' column defined in your Pro-Tip loader
            e_values = griddata((group['r'], group['z']), group['E_field'], 
                                (r_query, z_query), method='linear')
            
            plt.plot(distances, e_values, label=f'R_inner {test_r_in*1e9} nm', marker = 'o')
    
# Formatting for the test plot
plt.yscale('log')
plt.xscale('log')
plt.xlabel('Distance from Tip (m)')
plt.ylabel('Electric Field Norm (V/m)')
plt.title('Plot E field vs distance')
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.3)

# Save the test PDF to your dataset location
test_filename = os.path.join(output_dir, f"TEST_Rin{test_r_in:.0e}_V{test_v_ext}.pdf")
plt.savefig(test_filename, format='pdf', bbox_inches='tight')
print(f"Test plot successfully saved to: {test_filename}")
plt.show()


# # 4. Process every unique combination of parameters
# # This creates a loop for each geometry and voltage study
# for (r_in, v_ext), group in df.groupby(['R_inner', 'V_ext']):
#     plt.figure(figsize=(10, 6))
    
#     for angle in angles_deg:
#         theta = np.radians(angle)
#         r_query = r0 + distances * np.sin(theta)
#         z_query = z0 + distances * np.cos(theta)
        
#         # Interpolate field from the current parameter group
#         e_values = griddata((group['r'], group['z']), group['E_field'], 
#                             (r_query, z_query), method='linear')
        
#         plt.plot(distances, e_values, label=f'Angle {angle}°')

#     # Formatting and Scientific Display
#     plt.yscale('log')
#     plt.xlabel('Distance from Tip (m)')
#     plt.ylabel('Electric Field Norm (V/m)')
#     plt.title(f'Decay: R_inner={r_in:.2e}m, V_ext={v_ext}V')
#     plt.legend()
#     plt.grid(True, which="both", ls="-", alpha=0.3)
    
#     # 5. Export Plot as PDF to the same location
#     filename = f"Decay_Rin{r_in:.0e}_V{v_ext}.pdf"
#     plt.savefig(os.path.join(output_dir, filename), format='pdf', bbox_inches='tight')
#     plt.close()

# 6. Save a copy of this script to the same location
try:
    script_dest = os.path.join(output_dir, "automated_plotter.py")
    shutil.copy2(__file__, script_dest)
    print(f"Success! Plots and script backup saved to: {output_dir}")
except NameError:
    print(f"Plots saved to {output_dir}. (Script backup skipped - running in interactive mode).")