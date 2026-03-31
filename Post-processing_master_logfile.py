# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 02:23:45 2026

@author: pjoshi11
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. SETUP & CONSTANTS
# ==========================================
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
master_json_path = os.path.join(folder_path, "PhaseSpace_Results", "master_simulation_log.json")

# FLUID & PHYSICS CONSTANTS (Update these!)
SURFACE_TENSION = 0.0728  # N/m (e.g., water)
EPSILON_0 = 8.854e-12     # F/m

# ==========================================
# 2. PHYSICS FUNCTIONS FOR E_REQUIRED
# ==========================================
def calculate_E_req_rayleigh(row):
    """
    Calculate the required electric field based on the Rayleigh limit.
    Uses 'R_cap' or 'R_inner' from the row data.
    """
    # Example formula: E = sqrt(2 * gamma / (epsilon_0 * r))
    # Note: R_cap is extracted in nm, so we convert to meters
    r_meters = row['R_cap'] * 1e-9 
    
    if r_meters <= 0: return np.nan
    e_req = np.sqrt((4 * SURFACE_TENSION) / (EPSILON_0 * r_meters))
    return e_req

def calculate_E_req_taylor(row):
    """
    Calculate the required electric field based on Taylor cone formation.
    """
    # Example placeholder formula (Update with your specific Taylor math!)
    r_meters = row['R_inner'] * 1e-9
    
    if r_meters <= 0: return np.nan
    e_req = np.sqrt((2*SURFACE_TENSION) / (EPSILON_0 * r_meters)) # Placeholder
    return e_req

# ==========================================
# 3. DATA LOADING AND PREPARATION
# ==========================================
print("Loading master log...")
with open(master_json_path, 'r') as f:
    master_log = json.load(f)

# Flatten JSON into a list of dictionaries for Pandas
flat_data = []
for entry in master_log:
    params = entry.get('Input_Parameters', {})
    results = entry.get('Results', {})
    
    # Extract numerical values from strings (e.g., "10 [nm]" -> 10.0)
    def parse_val(v):
        try: return float(str(v).split()[0])
        except: return np.nan
        
    row = {
        'Run_Name': entry.get('Run_Name'),
        'Ext_elec_R_i': parse_val(params.get('Ext_elec_R_i')),
        'R_cap': parse_val(params.get('R_cap')),
        'R_inner': parse_val(params.get('R_inner')),
        'd': parse_val(params.get('d')),
        'capillary_depth': parse_val(params.get('capillary_depth')),
        'IFE_spacing': parse_val(params.get('IFE_spacing')),
        'V_ext_sim': parse_val(params.get('V_ext')),
        
        'E_rayleigh_sim': results.get('E_rayleigh'),
        'E_taylor_sim': results.get('E_taylor'),
        'Mesh_Qual': results.get('Min_Mesh_Quality_FTri2')
    }
    flat_data.append(row)

df = pd.DataFrame(flat_data)

# Drop runs where mesh evaluation failed or field data is missing
df = df.dropna(subset=['E_rayleigh_sim', 'E_taylor_sim', 'V_ext_sim'])

# ==========================================
# 4. CALCULATE ONSET VOLTAGES
# ==========================================
print("Calculating V_onset...")

# Calculate theoretical required fields
df['E_req_rayleigh'] = df.apply(calculate_E_req_rayleigh, axis=1)
df['E_req_taylor'] = df.apply(calculate_E_req_taylor, axis=1)

# V_onset = V_simulated * (E_required / E_simulated)
df['V_onset_rayleigh'] = df['V_ext_sim'] * (df['E_req_rayleigh'] / df['E_rayleigh_sim'])
df['V_onset_taylor'] = df['V_ext_sim'] * (df['E_req_taylor'] / df['E_taylor_sim'])

# ==========================================
# 5. GENERATE PLOTS
# ==========================================
print("Generating plots...")
os.makedirs(os.path.join(folder_path, "Plots"), exist_ok=True)

# ---------------------------------------------------------
# Plot 1: Effect of R_inner (keeping all other parameters const)
# ---------------------------------------------------------
# Define your "constant" baseline conditions here
baseline_cond = (df['R_cap'] == 10) & \
                (df['d'] == 1) & \
                (df['capillary_depth'] == 10) & \
                (df['IFE_spacing'] == 1000)

df_p1 = df[baseline_cond].sort_values('R_inner')

if not df_p1.empty:
    plt.figure(figsize=(8, 5))
    plt.plot(df_p1['R_inner'], df_p1['V_onset_rayleigh'], marker='o', label='Rayleigh Onset')
    plt.plot(df_p1['R_inner'], df_p1['V_onset_taylor'], marker='s', label='Taylor Onset')
    plt.title('Effect of Inner Radius on Onset Voltage')
    plt.xlabel('Inner Radius (nm)')
    plt.ylabel('V Onset (V)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(folder_path, "Plots", "Plot_1_R_inner_effect.png"))
    plt.close()

# ---------------------------------------------------------
# Plot 2: Effect of R_cap for Cap depth 1000um, IFE_spacing 0.5um
# ---------------------------------------------------------
cond_p2 = (df['capillary_depth'] == 1000) & (df['IFE_spacing'] == 0.5)
df_p2 = df[cond_p2].sort_values('R_cap')

if not df_p2.empty:
    plt.figure(figsize=(8, 5))
    plt.plot(df_p2['R_cap'], df_p2['V_onset_rayleigh'], marker='o', color='blue', label='Rayleigh Method')
    plt.plot(df_p2['R_cap'], df_p2['V_onset_taylor'], marker='s', color='red', label='Taylor Method')
    plt.title('Effect of Capillary Radius (Depth 1000um, IFE 0.5um)')
    plt.xlabel('Capillary Radius (nm)')
    plt.ylabel('V Onset (V)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(folder_path, "Plots", "Plot_2_R_cap_effect.png"))
    plt.close()

# ---------------------------------------------------------
# Plot 3: Effect of cap depth for constant IFE spacing (1000um)
# ---------------------------------------------------------
cond_p3 = (df['IFE_spacing'] == 0.5)
df_p3 = df[cond_p3].sort_values('capillary_depth')

if not df_p3.empty:
    # If multiple R_cap values exist for this IFE spacing, group by R_cap to make multiple lines
    plt.figure(figsize=(8, 5))
    
    for r_cap, group_data in df_p3.groupby('R_cap'):
        plt.plot(group_data['capillary_depth'], group_data['V_onset_taylor'], 
                 marker='^', label=f'R_cap = {r_cap} nm (Taylor)')
                 
    plt.title('Effect of Capillary Depth (IFE Spacing 1000um)')
    plt.xlabel('Capillary Depth (um)')
    plt.ylabel('V Onset (V)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(folder_path, "Plots", "Plot_3_Cap_depth_effect.png"))
    plt.close()

print("All available plots saved to the 'Plots' folder.")

# ---------------------------------------------------------
# Plot 4: Rayleigh Onset vs Taylor Onset for cap_depth 10, 100, 1000 um
# ---------------------------------------------------------
target_depths = [10, 100, 1000]

# Filter for only the three depths we care about
df_p4 = df[df['capillary_depth'].isin(target_depths)]

if not df_p4.empty:
    plt.figure(figsize=(8, 6))
    
    # Assign distinct markers and colors for visual clarity
    markers = {10: 'o', 100: 's', 1000: '^'}
    colors = {10: '#1f77b4', 100: '#ff7f0e', 1000: '#2ca02c'}
    
    for depth in target_depths:
        subset = df_p4[df_p4['capillary_depth'] == depth]
        if not subset.empty:
            plt.scatter(subset['V_onset_rayleigh'], subset['V_onset_taylor'], 
                        marker=markers[depth], color=colors[depth], 
                        label=f'Cap Depth = {depth} um', 
                        s=70, alpha=0.8, edgecolors='k')
    
    # Add a y = x parity line to easily see which onset requires more voltage
    max_val = max(df_p4['V_onset_rayleigh'].max(), df_p4['V_onset_taylor'].max())
    min_val = min(df_p4['V_onset_rayleigh'].min(), df_p4['V_onset_taylor'].min())
    
    if pd.notna(max_val) and pd.notna(min_val):
        # Extend the line slightly past the min/max data points
        buffer = (max_val - min_val) * 0.05
        line_lims = [min_val - buffer, max_val + buffer]
        plt.plot(line_lims, line_lims, 'k--', alpha=0.5, label='y = x (Equal Onset)')
        
    plt.title('Rayleigh vs. Taylor Onset Voltage by Capillary Depth')
    plt.xlabel('Rayleigh Onset Voltage (V)')
    plt.ylabel('Taylor Onset Voltage (V)')
    
    # Force axes to be scaled equally so the y=x line is perfectly 45 degrees
    plt.axis('equal') 
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(folder_path, "Plots", "Plot_4_Rayleigh_vs_Taylor.png"))
    plt.close()