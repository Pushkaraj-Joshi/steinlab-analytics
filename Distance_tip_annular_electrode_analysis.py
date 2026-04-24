# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 23:26:41 2026

@author: pjoshi11
"""

import numpy as np
import matplotlib.pyplot as plt
import os
plt.rcParams['ytick.labelsize'] = 18
plt.rcParams['xtick.labelsize'] = 18


# 1. Define folder path
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files\Plots'

# Ensure the directory exists (optional but recommended)
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# 2. Parameters
# Note: 10 microns = 0.01 mm. If you want 30 microns, use 0.03.
h = 0.1  # Tip height in mm (30 microns)
Ri_values = [0, 0.01, 0.02, 0.05, 0.1, 0.2]  # Ri values in mm
d = np.logspace(np.log10(0.01), np.log10(2), 500)  # d from 0.01 to 2 mm

# 3. Plotting
plt.figure(figsize=(10, 8))

for Ri in Ri_values:
    # Distance tip to electrode: hypotenuse of Ri and d
    dist_tip_el = np.sqrt(Ri**2 + d**2)
    # Distance plate to electrode: d + h
    dist_plate_el = d + h
    # Ratio calculation
    ratio = dist_tip_el / dist_plate_el
    
    plt.plot(d, ratio, label=f'$R_i = {Ri}$ mm', linewidth = 3.0)

# 4. Formatting
plt.xscale('log')
plt.yscale('log') # Keeps the log-log perspective for wide ratio ranges
plt.xlabel(' $d$ (mm)', fontsize=20)
plt.ylabel(r'Ratio: $\mathrm{dist(tip, electrode)} / \mathrm{dist(plate, electrode)}$', fontsize=20)
plt.title(f'Ratio of Distances vs. $d$ for different $R_i$\n'
          fr'(Capillary depth $ = {h*1000:.0f}\ \mathrm{{\mu m}}$)', fontsize=22)
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.ylim(0.08, 12)
plt.legend(fontsize=16)
plt.tight_layout()

# 5. Save the file with a dynamic filename
# Converts h from mm to microns (e.g., 0.03 -> 30) for the filename
h_microns = int(h * 1000)
filename = f'distance_ratio_h{h_microns}um.pdf'

filepath = os.path.join(folder_path, filename)

plt.savefig(filepath, format='pdf', bbox_inches='tight')
print(f"Plot saved as: {filepath}")