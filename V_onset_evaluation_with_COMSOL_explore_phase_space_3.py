# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 14:50:12 2026

@author: pjoshi11
"""

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
import sys

# ==========================================
# 1. SETUP PATHS & CONFIGURATION
# ==========================================
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
mph_filename = 'Onset-field-study- Mar_26_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)

output_dir = os.path.join(folder_path, "PhaseSpace_Results")
os.makedirs(output_dir, exist_ok=True)

master_json_path = os.path.join(output_dir, "master_simulation_log.json")

export_files = {
    'Meniscus_cap': 'Meniscus_cap_data.txt',
    'Meniscus_cone': 'Meniscus_cone_data.txt',
    'Meniscus_base': 'Meniscus_base_data.txt',
    'Capillary Edge': 'Capillary_edge_data.txt',
    'Base Plate': 'Base_plate_data.txt'
}

# ==========================================
# 2. DEFINE THE PHASE SPACE
# ==========================================
phase_space_values = {
    'Ext_elec_R_i': [0.0, 0.1, 0.2, 0.5, 1],
    'R_cap': [10],
    'R_inner': [40],
    'd': [0.1, 0.5, 1, 2],
    'capillary_depth': [10, 100],
    'base_half_pitch': [1000],
    'V_ext': [100] 
}

phase_space_units = {
    'Ext_elec_R_i': 'mm',
    'R_cap': 'nm',
    'R_inner': 'nm',
    'd': 'mm',
    'capillary_depth': 'um',
    'base_half_pitch': 'um',
    'V_ext': 'V'
}

phase_space = {
    param: [f"{val} [{phase_space_units[param]}]" for val in values]
    for param, values in phase_space_values.items()
}

keys = phase_space.keys()
combinations = list(itertools.product(*phase_space.values()))
run_list = [dict(zip(keys, combo)) for combo in combinations]

# ==========================================
# 3. INITIALIZE COMSOL & FILTER COMPLETED RUNS
# ==========================================
print("Starting COMSOL Client...")
client = mph.start()
model = client.load(full_mph_path)

if os.path.exists(master_json_path):
    with open(master_json_path, 'r') as f:
        master_log = json.load(f)
    print(f"Loaded existing master log with {len(master_log)} completed runs.")
else:
    master_log = []
    print("No existing master log found. Starting fresh.")

total_runs = len(run_list)
pending_runs = []

for current_params in run_list:
    already_simulated = False
    for entry in master_log:
        old_expressions = entry.get('Parameter_Expressions', {})
        is_match = True
        for param_key, param_value in current_params.items():
            if old_expressions.get(param_key) != param_value:
                is_match = False
                break 
        if is_match:
            already_simulated = True
            break 
    if not already_simulated:
        pending_runs.append(current_params)

run_list = pending_runs
completed_count = total_runs - len(run_list)

print(f"Found {completed_count} runs already completed in the database.")
print(f"Queued {len(run_list)} NEW runs to execute.")

if len(run_list) == 0:
    print("All combinations in the current phase space have already been simulated. Exiting.")
    sys.exit()

# ==========================================
# 4. MAIN EXECUTION LOOP
# ==========================================
total_runs = len(run_list) 
failed_empty_exports = [] # NEW: Tracking list for failed runs

for idx, current_params in enumerate(run_list):
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n[{run_timestamp}] --- Starting Run {idx + 1} of {total_runs} ---")
    
    name_parts = [f"{k}_{v.replace(' [', '').replace(']', '')}" for k, v in current_params.items() if k != 'V_ext']
    run_name = "Run_" + "_".join(name_parts) + f"_{run_timestamp}"
    print(f"Configuration: {run_name}")
    
    run_results = {}  
    excel_path = os.path.join(output_dir, f"{run_name}.xlsx") 

    for param_name, param_value in current_params.items():
        model.parameter(param_name, param_value)

    target_size_m = 35e-9  
    try:
        base_half_pitch_um = float(current_params['base_half_pitch'].split()[0])
        base_half_pitch_m = base_half_pitch_um * 1e-6 
        cap_depth_um = float(current_params['capillary_depth'].split()[0])
        cap_depth = cap_depth_um * 1e-6  
        
        
        if base_half_pitch_m >= 1000e-6:
            n_plate = max(1, int(round(base_half_pitch_m / (target_size_m*1.3))))
        elif base_half_pitch_m >= 100e-6:
            n_plate = max(1, int(round(base_half_pitch_m / (target_size_m*1.3))))
        else:
            n_plate = max(1, int(round(base_half_pitch_m / (target_size_m))))
            
        if cap_depth >= 1000e-6:
            n_cap = max(1, int(round(cap_depth / (target_size_m*1.3))))
        elif cap_depth >= 100e-6:
            n_cap = max(1, int(round(cap_depth / (target_size_m*1.3))))
        else:
            n_cap = max(1, int(round(cap_depth / (target_size_m/2.0))))

        model.parameter('Num_elem_plate', str(n_plate))
        model.parameter('Num_elem_cap_side', str(n_cap))
    except Exception as e:
        print(f"  -> Warning: Could not calculate dynamic mesh nodes. Error: {e}")

    print("Solving model...")
    model.solve()
    
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

    print("Executing COMSOL data exports...")
    for sheet_name, txt_filename in export_files.items():
        txt_path = os.path.join(folder_path, txt_filename)
        if os.path.exists(txt_path):
            try: os.remove(txt_path)
            except: pass
                
        try:
            model.export(sheet_name, txt_path) 
            print(f"  -> Exported: {sheet_name}")
        except Exception as e:
            print(f"  -> Error: COMSOL failed to export {sheet_name}. Error: {e}")

    # --- NEW: VALIDATION BLOCK ---
    print("Validating exported data...")
    empty_exports = []
    loaded_dataframes = {}
    
    for sheet_name, txt_filename in export_files.items():
        txt_path = os.path.join(folder_path, txt_filename)
        try:
            df_data = pd.read_csv(txt_path, sep=r'\s+', comment='%', names=['r_mesh', 'z_mesh', 'r', 'z', 'E'])
            df_data = df_data.drop(columns=['r_mesh', 'z_mesh'])
            
            if df_data.empty:
                empty_exports.append(sheet_name)
            else:
                loaded_dataframes[sheet_name] = df_data # Save it so we don't have to read it again!
        except Exception:
            empty_exports.append(sheet_name)
            
    if empty_exports:
        print(f"  -> RUN FAILED VALIDATION! Empty data detected in: {empty_exports}")
        print("  -> Skipping Excel generation and log entry for this run.")
        
        # Log the failure for the end-of-script report
        failed_empty_exports.append({
            'Run_Name': run_name,
            'Empty_Files': empty_exports,
            'Parameters': current_params
        })
        continue # <-- This safely aborts the rest of the loop and starts the next run
    # -----------------------------

    try:
        z_center_eval = float(model.evaluate('z_cap_center'))
    except Exception:
        z_center_eval = 0.0

    try:
        min_mesh_qual = float(model.evaluate('comp3.minop1(qualskewness)'))
        run_results['Min_Mesh_Quality_FTri2'] = min_mesh_qual
        print(f"  -> Mesh Quality (Free Tri 2): {min_mesh_qual:.4f}")
    except Exception as e:
        run_results['Min_Mesh_Quality_FTri2'] = None

    # Process Spatial Data and Generate Excel Sheets
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_params.to_excel(writer, sheet_name='Parameters', index=False)
        
        # Notice we are using 'loaded_dataframes' now instead of reading the files again
        for sheet_name, df_data in loaded_dataframes.items():
            try:
                if sheet_name == 'Meniscus_cap':
                    df_data['Angle (deg)'] = np.abs(np.degrees(np.arctan2(df_data['r'], df_data['z'] - z_center_eval)))
                    df_data = df_data.sort_values('Angle (deg)')
                    df_data = df_data[['Angle (deg)', 'E']] 
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                    
                    run_results['E_rayleigh'] = float(df_data['E field'].max())
                    run_results['E_taylor'] = float(df_data['E field'].iloc[-1])
                        
                elif sheet_name in ['Meniscus_cone', 'Meniscus_base']:
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                        
                elif sheet_name == 'Base Plate':
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                    run_results['Max_E_Base_Plate'] = float(df_data['E field'].max())
                    run_results['Median_E_Base_Plate'] = float(df_data['E field'].median())
                    
                elif sheet_name == 'Capillary Edge':
                    df_data.rename(columns={'E': 'E field'}, inplace=True)
                    run_results['Max_E_Capillary_Edge'] = float(df_data['E field'].max())

                df_data.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"  -> Warning: Math processing failed for {sheet_name}. Error: {e}")

    print(f"Saved run data to Excel: {excel_path}")

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

# ==========================================
# 5. FINAL REPORT
# ==========================================
print("\n=== Phase Space Exploration Complete! ===")
print(f"Master log saved to: {master_json_path}")

if failed_empty_exports:
    print("\n" + "!"*60)
    print("WARNING: THE FOLLOWING RUNS GENERATED EMPTY DATA")
    print("These runs were NOT saved to the Master Log or Excel.")
    print("!"*60)
    for fail in failed_empty_exports:
        print(f"\n-> Run: {fail['Run_Name']}")
        print(f"   Empty Files: {', '.join(fail['Empty_Files'])}")
        print(f"   Parameters: {fail['Parameters']}")
    print("\n" + "!"*60)