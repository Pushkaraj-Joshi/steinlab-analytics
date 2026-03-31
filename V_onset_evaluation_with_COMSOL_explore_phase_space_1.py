# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 14:50:12 2026

@author: pjoshi11
"""

import mph
import os
import json
import itertools
import pandas as pd
import numpy as np
from datetime import datetime
import sys  # <-- ADDED: Required for cleanly exiting the script

# ==========================================
# 1. SETUP PATHS & CONFIGURATION
# ==========================================
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_23_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)

output_dir = os.path.join(folder_path, "PhaseSpace_Results")
os.makedirs(output_dir, exist_ok=True)

master_json_path = os.path.join(output_dir, "master_simulation_log.json")

# Filenames exactly as configured in your COMSOL Export nodes
export_files = {
    'Meniscus': 'Meniscus_data.txt',
    'Capillary Edge': 'Capillary_edge_data.txt',
    'Base Plate': 'Base_plate_data.txt'
}

# ==========================================
# 2. DEFINE THE PHASE SPACE
# ==========================================
# 1. Specify the purely numerical values you want to sweep
phase_space_values = {
    'Ext_elec_R_i': [0.0],
    'R_cap': [10],
    'R_inner': [25],
    'd': [1],
    'capillary_depth': [1000],# 50, 100, 500, 1000],
    'IFE_spacing': [5000],
    'V_ext': [100] 
}

# 2. Specify the exact COMSOL unit for each parameter just once
phase_space_units = {
    'Ext_elec_R_i': 'mm',
    'R_cap': 'nm',
    'R_inner': 'nm',
    'd': 'mm',
    'capillary_depth': 'um',
    'IFE_spacing': 'um',
    'V_ext': 'V'
}

# 3. Automatically stitch them together for COMSOL
phase_space = {
    param: [f"{val} [{phase_space_units[param]}]" for val in values]
    for param, values in phase_space_values.items()
}

# Generate all parameter combinations using the stitched list
keys = phase_space.keys()
combinations = list(itertools.product(*phase_space.values()))
run_list = [dict(zip(keys, combo)) for combo in combinations]

# ==========================================
# 3. INITIALIZE COMSOL & FILTER COMPLETED RUNS
# ==========================================
print("Starting COMSOL Client...")
client = mph.start()
model = client.load(full_mph_path)

# 1. Load existing history or start fresh
if os.path.exists(master_json_path):
    with open(master_json_path, 'r') as f:
        master_log = json.load(f)
    print(f"Loaded existing master log with {len(master_log)} completed runs.")
else:
    master_log = []
    print("No existing master log found. Starting fresh.")

total_runs = len(run_list)

# 2. Filter the run_list to ONLY include truly new physical combinations
pending_runs = []

for current_params in run_list:
    already_simulated = False
    
    for entry in master_log:
        # Grab the FULL list of parameters COMSOL had during that old run
        old_expressions = entry.get('Parameter_Expressions', {})
        
        # Check if EVERY parameter in our current proposed run matches the old run's state
        is_match = True
        for param_key, param_value in current_params.items():
            if old_expressions.get(param_key) != param_value:
                is_match = False
                break 
                
        if is_match:
            already_simulated = True
            break # We found a historical match, no need to check older runs
            
    # If no historical run matched this exact physical state, queue it up
    if not already_simulated:
        pending_runs.append(current_params)

# 3. Replace the old list with the filtered list
run_list = pending_runs
completed_count = total_runs - len(run_list)

print(f"Found {completed_count} runs already completed in the database.")
print(f"Queued {len(run_list)} NEW runs to execute.")

if len(run_list) == 0:
    print("All combinations in the current phase space have already been simulated. Exiting.")
    sys.exit()  # <-- FIXED: Using sys.exit() instead of exit()

# ==========================================
# 4. MAIN EXECUTION LOOP
# ==========================================
total_runs = len(run_list) # This now correctly tracks the number of *pending* runs

for idx, current_params in enumerate(run_list):
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n[{run_timestamp}] --- Starting Run {idx + 1} of {total_runs} ---")
    
    # Generate clean run name
    name_parts = [f"{k}_{v.replace(' [', '').replace(']', '')}" for k, v in current_params.items() if k != 'V_ext']
    run_name = "Run_" + "_".join(name_parts) + f"_{run_timestamp}"
    print(f"Configuration: {run_name}")
    
    run_results = {}  # Initializes the dictionary so we don't get a NameError
    excel_path = os.path.join(output_dir, f"{run_name}.xlsx") # Tells Pandas where to save!

    # A. Set Parameters in live COMSOL memory
    for param_name, param_value in current_params.items():
        model.parameter(param_name, param_value)

    # --- Dynamic Mesh Resolution Calculation ---
 
    target_size_m = 35e-9  
    try:
        # Bypass COMSOL's dataset lag by parsing the exact strings Python is about to send
        ife_spacing_um = float(current_params['IFE_spacing'].split()[0])
        ife_spacing = ife_spacing_um * 1e-6  # Convert to meters
        print(f'IFE extracted natively: {ife_spacing}')
        
        cap_depth_um = float(current_params['capillary_depth'].split()[0])
        cap_depth = cap_depth_um * 1e-6      # Convert to meters
        print(f'cap_depth extracted natively: {cap_depth}')

        n_plate = max(1, int(round(ife_spacing / (target_size_m*4.0))))
        n_cap = max(1, int(round(cap_depth / (target_size_m/2.0))))

        model.parameter('Num_elem_plate', str(n_plate))
        model.parameter('Num_elem_cap_side', str(n_cap))
        
        print(f"  -> Mesh Updated: Plate Elements = {n_plate}, Cap Side Elements = {n_cap}")
    except Exception as e:
        print(f"  -> Warning: Could not calculate dynamic mesh nodes. Error: {e}")
    # ------------------------------------------------

    # B. Solve the Model
    print("Solving model...")
    model.solve()
    
    # C. Extract and Evaluate ALL Parameters
    print("Extracting evaluated parameters...")
    evaluated_params = {}
    param_expressions = {}
    param_sheet_data = []
    
    for name, expr in model.parameters().items():
        try:
            val = float(model.evaluate(name))
            evaluated_params[name] = val
            param_expressions[name] = expr
            param_sheet_data.append({'Parameter': name, 'Expression': expr, 'Value (SI)': val})
        except Exception:
            param_expressions[name] = expr
            param_sheet_data.append({'Parameter': name, 'Expression': expr, 'Value (SI)': 'N/A'})
            
    df_params = pd.DataFrame(param_sheet_data)

    # D. Trigger COMSOL Exports
    print("Executing COMSOL data exports...")
    
    # Iterate explicitly through our expected exports
    for sheet_name, txt_filename in export_files.items():
        # Define the strict absolute path
        txt_path = os.path.join(folder_path, txt_filename)
        
        # 1. DELETE the old file first to prevent reading stale data or appending errors
        if os.path.exists(txt_path):
            try:
                os.remove(txt_path)
            except Exception as e:
                print(f"  -> Warning: Could not delete old {txt_filename}. It may be open/locked.")
                
        # 2. Force COMSOL to export EXACTLY to our intended path
        try:
            # Passing txt_path overrides whatever is saved in the .mph GUI
            model.export(sheet_name, txt_path) 
            print(f"  -> Exported: {sheet_name}")
        except Exception as e:
            print(f"  -> Error: COMSOL failed to export {sheet_name}. Error: {e}")
    
    # 1. Pre-evaluate Capillary Center for Angle Math
    try:
        z_center_eval = float(model.evaluate('z_cap_center'))
    except Exception as e:
        print(f"  -> Warning: Could not evaluate 'z_cap_center'. Defaulting to 0.")
        z_center_eval = 0.0

    # 2. Pre-evaluate Mesh Quality using predefined COMSOL Operator
    try:
        # Changed 'meshelementquality' to 'qual'
        min_mesh_qual = float(model.evaluate('comp3.minop1(qual)'))
        run_results['Min_Mesh_Quality_FTri2'] = min_mesh_qual
        print(f"  -> Mesh Quality (Free Tri 2): {min_mesh_qual:.4f}")
    except Exception as e:
        print(f"  -> Warning: Could not evaluate mesh quality. Error: {e}")
        run_results['Min_Mesh_Quality_FTri2'] = None

    # 3. Process Spatial Data and Generate Excel Sheets
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_params.to_excel(writer, sheet_name='Parameters', index=False)
        
        for sheet_name, txt_filename in export_files.items():
            txt_path = os.path.join(folder_path, txt_filename)
            
            try:
                # Read 5-column COMSOL text file and drop mesh coordinates
                df_data = pd.read_csv(txt_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
                df_data = df_data.drop(columns=['r_mesh', 'z_mesh'])
                
                if sheet_name == 'Meniscus':
                    # NEW: Check if the file is completely empty first!
                    if df_data.empty:
                        print(f"  -> Warning: Meniscus data is empty! Geometry likely collapsed.")
                        run_results['E_rayleigh'] = None
                        run_results['E_taylor'] = None
                    else:
                        df_data['Angle (deg)'] = np.abs(np.degrees(np.arctan2(df_data['r'], df_data['z'] - z_center_eval)))
                        df_data = df_data.sort_values('Angle (deg)')
                        df_data = df_data[['Angle (deg)', 'E']] 
                        df_data.rename(columns={'E': 'E field'}, inplace=True)
                        
                        run_results['E_rayleigh'] = float(df_data['E field'].max())
                        run_results['E_taylor'] = float(df_data['E field'].iloc[-1])
                    
                elif sheet_name == 'Base Plate':
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                    run_results['Max_E_Base_Plate'] = float(df_data['E field'].max())
                    run_results['Median_E_Base_Plate'] = float(df_data['E field'].median())
                    
                elif sheet_name == 'Capillary Edge':
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                    run_results['Max_E_Capillary_Edge'] = float(df_data['E field'].max())

                df_data.to_excel(writer, sheet_name=sheet_name, index=False)
                
            except Exception as e:
                print(f"  -> Warning: Could not process {txt_filename} for {sheet_name}. Error: {e}")
                if sheet_name == 'Meniscus':
                    run_results['E_rayleigh'] = None
                    run_results['E_taylor'] = None
                elif sheet_name == 'Base Plate':
                    run_results['Max_E_Base_Plate'] = None
                    run_results['Median_E_Base_Plate'] = None
                elif sheet_name == 'Capillary Edge':
                    run_results['Max_E_Capillary_Edge'] = None

    print(f"Saved run data to Excel: {excel_path}")

    # F. Append to Master JSON Log
    log_entry = {
        "Run_Name": run_name,
        "Timestamp": run_timestamp,
        "Excel_File": f"{run_name}.xlsx",
        "Input_Parameters": current_params,
        "Evaluated_Parameters": evaluated_params,
        "Parameter_Expressions": param_expressions,
        "Results": run_results
    }
    
    master_log.append(log_entry)
    
    with open(master_json_path, 'w') as f:
        json.dump(master_log, f, indent=4)

print("\n=== Phase Space Exploration Complete! ===")
print(f"Master log saved to: {master_json_path}")