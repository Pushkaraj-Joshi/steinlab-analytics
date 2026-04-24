# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 12:35:41 2026

@author: pjoshi11
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# 1. Setup paths and parameters
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

h = 0.01  # Tip height in mm 
Ri_values = [0.01, 0.02, 0.05, 0.1, 0.2]  # Ri values in mm
d = np.logspace(np.log10(0.01), np.log10(2), 500)  # d from 0.01 to 2 mm

# Angle for partition
theta_deg = 40.7
theta_rad = np.radians(theta_deg)

# 2. Plotting
plt.figure(figsize=(10, 8))

for Ri in Ri_values:
    # Math logic
    dist_tip_el = np.sqrt(Ri**2 + d**2)
    dist_plate_el = d + h
    ratio = dist_tip_el / dist_plate_el
    
    # Partition Condition: Ri > d * tan(theta)
    condition_met = Ri > (d * np.tan(theta_rad))
    
    # Plot segments that DO meet the condition (Solid/Bold)
    # We capture the line object to get its color
    line, = plt.plot(d[condition_met], ratio[condition_met], 
                     label=f'$R_i = {Ri}$ mm', linewidth=2.5)
    
    # Get the color assigned to this Ri
    current_color = line.get_color()
    
    # Plot segments that do NOT meet the condition (Dotted, Same Color)
    plt.plot(d[~condition_met], ratio[~condition_met], 
             linestyle=':', color=current_color, linewidth=2.5, label='_nolegend_')

# 3. Add the Boundary Line (Locus where Ri = d * tan(theta))
# At this boundary, dist_tip_el = d / cos(theta)
boundary_ratio = (d / np.cos(theta_rad)) / (d + h)
plt.plot(d, boundary_ratio, color='black', linestyle='--', linewidth=1.5, 
         label=fr'Boundary: $R_i = d \cdot \tan({theta_deg}^\circ)$')

# 4. Formatting
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Distance of electrode from tip, $d$ (mm)', fontsize=14)
plt.ylabel(r'Ratio: $\mathrm{dist(tip, electrode)} / \mathrm{dist(plate, electrode)}$', fontsize=14)
plt.title(fr'Distance Ratio with $\theta={theta_deg}^\circ$ Partition ($h=30\mu m$)', fontsize=16)
plt.grid(True, which="both", ls="-", alpha=0.4)
plt.legend(fontsize=11, loc='best')
plt.tight_layout()

# 5. Save with dynamic filename
h_microns = int(h * 1000)
filename = f'ratio_partition_h{h_microns}um.pdf'
filepath = os.path.join(folder_path, filename)

plt.savefig(filepath, format='pdf', bbox_inches='tight')
print(f"Successfully saved to: {filepath}")
plt.show()