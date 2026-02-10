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
import re


# 1. Setup paths
dataset_path = r"C:\Users\pjoshi11\Documents\COMSOL_working files\Studies\Dataset_E_field.csv"
output_dir = os.path.dirname(os.path.abspath(dataset_path))

# 2. Load data - Skip 8 lines of metadata to get to data rows
# Using float precision to ensure E+09 is not lost
df = pd.read_csv(dataset_path, skiprows=8, sep=None, engine='python', header=None)

# 3. Manually assign headers based on your image
df.columns = ['r', 'z', 'E_80V', 'E_100V', 'E_120V']
df = df.iloc[1:]

# 4. CONVERT THE ENTIRE DATAFRAME TO NUMERIC
# errors='coerce' turns any non-numeric strings into NaN
df = df.apply(pd.to_numeric, errors='coerce')

# 5. Drop any rows that failed to convert (cleanup)
df = df.dropna().reset_index(drop=True)

# --- VERIFICATION ---
# Now scientific formatting will work because the data is numeric
print("New Data Types:\n", df.dtypes)
print(f"\nNumeric Max Field: {df.iloc[:, 2].max():.2e} V/m")


# 2. Geometry Setup (Nanotip Origin)
r0, z0 = 0.0, 0.0
target_angle_deg = 5.0  # Plotting along the symmetry axis
tolerance_nm = 0.5    # How "thick" the slice is

# 3. Calculate actual Angle and Distance for every single mesh node
df['node_dist'] = np.sqrt((df['r'] - r0)**2 + (df['z'] - z0)**2)
df['node_angle'] = np.degrees(np.arctan2(df['r'] - r0, df['z'] - z0))

# 4. Filter: Keep only the real nodes that are near our target angle
raw_points = df[np.abs(df['node_angle'] - target_angle_deg) < (tolerance_nm / 1e9)]

# 5. Plot the raw, uninterpolated data
plt.figure(figsize=(10, 6))
plt.scatter(raw_points['node_dist'] * 1e9, raw_points['E_120V'], 
            s=2, c='red', label='Raw Mesh Nodes')

plt.yscale('log')
plt.xscale('log')
plt.xlabel('Distance from Tip (nm)')
plt.ylabel('Electric Field (V/m)')
plt.title(f'Raw Mesh Data along {target_angle_deg}° Axis')
plt.legend()
plt.show()