# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 21:38:17 2026

@author: pjoshi11
"""

import mph
import numpy as np

# 1. Start COMSOL and Load Model
# This opens a background COMSOL server
client = mph.start() 
model = client.load(r'C:\Users\pjoshi11\Documents\COMSOL_working files\Onset-field-study- Mar_08_2026.mph')

# 2. Constants & Initial Parameters
# Constants
gamma = 0.072 
eps0 = 8.854e-12
r_inner_list = [20e-9, 40e-9, 60e-9, 80e-9, 100e-9]
r_caps = [1.0] # Ratios

results = {}

for r_inner in r_inner_list:

    for ratio in r_caps:
        r_cap = r_inner * ratio
        p_laplace = (2 * gamma) / r_cap
        model.parameter('R_cap', f'{r_cap} [m]')
        
        # Bisection Search Range
        v_low = 0
        v_high = 1000 # Set this to a value you know is ABOVE onset
        tol = 0.5      # Accuracy in Volts
        
        print(f"\n--- Searching for Onset: Ratio {ratio} ---")
        
        while (v_high - v_low) > tol:
            v_mid = (v_high + v_low) / 2
            model.parameter('V_ext', f'{v_mid} [V]')
            model.solve()
            
            # Extract E-max and calculate Maxwell Pressure
            # CRITICAL: Use es3 here to match your model
            e_max = model.evaluate('maxop1(es3.normE)')
            p_maxwell = 0.5 * eps0 * (e_max**2)
            
            if p_maxwell > p_laplace:
                v_high = v_mid # Too much pressure, go lower
            else:
                v_low = v_mid  # Not enough pressure, go higher
                
            print(f"  Testing {v_mid:.2f} V... P_max: {p_maxwell:.2e}")
    
        print(f"DONE: Onset Voltage = {v_high:.2f} V")
        results[ratio] = v_high

print("\nFinal Results Summary:")
print(results)