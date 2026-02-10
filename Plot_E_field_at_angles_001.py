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


# 6. Geometry and Interpolation
r0, z0 = 0.0, 0.0 # Adjusted z0 based on your sample data
distances = np.linspace(0, 5e-5, 1000) # μm scale
angles_deg = [5]

plt.figure(figsize=(10, 6))

# Interpolate for the 120V case
for angle in angles_deg:
    theta = np.radians(angle)
    r_q = r0 + distances * np.sin(theta)
    z_q = z0 + distances * np.cos(theta)
    
    # Use 'linear' or 'cubic'. If the data is sparse, cubic can over-oscillate.
    e_interp = griddata((df['r'], df['z']), df['E_120V'], (r_q, z_q), method='linear')
    
    plt.plot(distances, e_interp, label=f'{angle}°', marker = 'o')

# 7. Formatting
plt.yscale('log') 
plt.xscale('log') 
plt.ylabel('Electric Field Norm (V/m)')
plt.xlabel('Distance from Tip (m)')
plt.title('Field Decay (120V Applied)')
plt.legend()
plt.grid(True, which="both", ls="-", alpha=0.3)

# Save PDF
plt.savefig(os.path.join(output_dir, 'Corrected_Field_Decay.pdf'), format='pdf')
plt.show()