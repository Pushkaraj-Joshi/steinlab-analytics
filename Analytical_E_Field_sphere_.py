# -*- coding: utf-8 -*-
"""
Created on Fri Mar  6 21:44:33 2026

@author: pjoshi11
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm



# Constants
V0 = 200  # Potential on sphere (Volts)
R = 50e-9  # Radius of sphere (100nm diameter)
d = 1e-3   # Distance from plate to bottom of sphere (1mm)
epsilon_0 = 8.854e-12

R_list = [25E-9, 100E-9, 1000E-9, 10000E-9, 100000E-9]
d_list = [1E-3, 1E-2]
total_lines = len(R_list) * len(d_list)

# Generate a gradient of colors (you can change 'viridis' to 'plasma', 'jet', etc.)
colors = cm.viridis(np.linspace(0, 1, total_lines))
color_idx = 0

# Plotting
plt.figure(figsize=(8, 6))

for R in R_list:
    for d in d_list:
        

        # The center of the sphere is at z_c
        z_c = d + R
        
        # Approximating charge Q to maintain potential V0 on the sphere surface
        Q = 4 * np.pi * epsilon_0 * R * V0
        
        def electric_field(z):
            """Calculates E-field along the z-axis."""
            k = 1 / (4 * np.pi * epsilon_0)
            E_sphere = k * Q / (z_c - z)**2
            E_image = k * (-Q) / ((-z_c) - z)**2
            return np.abs(E_sphere - E_image)
        
        # Generate r_vals logarithmically from the sphere's surface (R) to the plate (z_c)
        r_vals = np.geomspace(R, z_c, 1000)
        
        # Calculate the corresponding z_vals for the electric_field function
        z_vals = z_c - r_vals
        
        # Calculate E_vals
        E_vals = electric_field(z_vals)
        
       
        
        # Plot E vs r on a log-log scale
        plt.loglog(r_vals, E_vals, label=f'R_tip = {R*1E9} nm, d ={d*1E3} mm', color=colors[color_idx], linewidth=2)
        color_idx += 1
        
        if R == R_list[0] and d == d_list[0]:
            # Add a reference line with an exact slope of -2
            # We anchor it to a point close to the sphere for easy visual comparison
            anchor_idx = -1 # Closest point to the sphere
            C = E_vals[anchor_idx] * (r_vals[anchor_idx]**2) 
            plt.loglog(r_vals, C / (r_vals**2), '--', color='darkorange', label='Reference Slope: -2 ($1/r^2$)')
        


plt.title('Electric Field vs. Distance from Sphere Center')
plt.xlabel('Distance from Sphere Center, r (m) [Log Scale]')
plt.ylabel('Electric Field (V/m) [Log Scale]')
plt.xlim(1E-8,2E-2)
plt.ylim(5E-2,2E10)

plt.grid(True, which="both", ls="-", alpha=0.3)
plt.legend()
    
    
plt.show()