# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 16:44:48 2026

@author: pjoshi11
"""

import numpy as np
import matplotlib.pyplot as plt

def calculate_emax(V, r, d, A=0.67):
    """
    Calculates E_max = V / (A * r * ln(4d/r))
    Using A = 0.67 as emperical constant.
    """
    # A is typically a dimensionless shape factor, often ~1 for sharp tips
    # Ref - "The Electrohydrodynamic Atomization of Liquids"
    #  IEEE TRANSACTIONS ON INDUSTRY APPLICATIONS, David Smith, 1986
    
    return V / (A * r * np.log(4 * d / r))

# Parameters
V_applied = 200  # Applied voltage in Volts (e.g., 1kV)
d_mm = np.linspace(0.1, 10, 1000)  # Distance from 0.1 to 10 mm
d_m = d_mm * 1e-3  # Convert mm to meters

r_values_nm = [25, 50, 100, 200, 500]
r_values_m = [r * 1e-9 for r in r_values_nm]  # Convert nm to meters
A=0.67

# Plotting
plt.figure(figsize=(10, 6))

for r_m, r_nm in zip(r_values_m, r_values_nm):
    E_max = calculate_emax(V_applied, r_m, d_m)
    # Convert V/m to V/nm or GV/m for readable scales if desired
    # Here we use GV/m (Gigavolts per meter)
    plt.plot(d_mm, E_max, label=f'r = {r_nm} nm')

# Formatting the plot
plt.title(f'Maximum Electric Field for Taylor Cone at Nanotip (V = {V_applied}V)')
plt.xlabel('Distance between electrode and tip (mm)')
plt.ylabel('E_max (V/m)')
plt.yscale('log')  # Field strength often varies orders of magnitude
plt.xscale('log') 
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.ylim(4E7,7E9)
plt.legend(title="Pore Radius", loc='upper left')

# Create a string for the formula using LaTeX formatting
formula_text = r'$E_{max} = \frac{V}{A \cdot r \cdot \ln(4d/r),}$'
additional_info = f'Where $V = {V_applied}V$ , $A = {A}$'

# Add the text box to the plot
plt.text(0.95, 0.95, formula_text + additional_info, 
         transform=plt.gca().transAxes, 
         fontsize=12, 
         verticalalignment='top', 
         horizontalalignment='right',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Save as PDF
plt.savefig('nanotip_field_analysis.pdf')
plt.show()

print("Plot saved as 'nanotip_field_analysis.pdf'")