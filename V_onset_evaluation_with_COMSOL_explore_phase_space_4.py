# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 16:28:37 2026

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
import math

# ==========================================
# 1. SETUP PATHS & CONFIGURATION
# ==========================================
folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'

# Map your specific COMSOL files to their respective geometry types
GEOMETRY_MAP = {
    'Onset-field-study- Mar_26_2026.mph': 'Conical_Tip',
    'Onset-field-study- Cylinder_Apr_19_2026.mph': 'Cylindrical_Tip'  
}

# Define the file you want to run
mph_filename = 'Onset-field-study- Cylinder_Apr_19_2026.mph'
full_mph_path = os.path.join(folder_path, mph_filename)

# STRICT GEOMETRY CHECK: Stop script if file is not in the map
if mph_filename not in GEOMETRY_MAP:
    print("\n" + "!"*60)
    print("CRITICAL ERROR: GEOMETRY TYPE UNKNOWN")
    print(f"The file '{mph_filename}' was not found in the GEOMETRY_MAP.")
    print("Please add this file and its Geometry Type to the GEOMETRY_MAP")
    print("dictionary at the top of the script before running.")
    print("!"*60 + "\n")
    sys.exit(1)  # Instantly terminates the script

# Assign the mapped geometry type safely
GEOMETRY_TYPE = GEOMETRY_MAP[mph_filename]

output_dir = os.path.join(folder_path, "PhaseSpace_Results")
os.makedirs(output_dir, exist_ok=True)

master_json_path = os.path.join(output_dir, "master_simulation_log.json")

# ADD THIS LINE: Dynamically create the path for the specific geometry being run
geometry_json_path = os.path.join(output_dir, f"{GEOMETRY_TYPE}_log.json")

export_files = {
    'Meniscus_cap': 'Meniscus_cap_data.txt',
    'Meniscus_cone': 'Meniscus_cone_data.txt',
    'Meniscus_base': 'Meniscus_base_data.txt',
    'Capillary Edge': 'Capillary_edge_data.txt',
    'Base Plate': 'Base_plate_data.txt'
}

# ==========================================
# 2. DEFINE THE PHASE SPACE & VALIDATION
# ==========================================

# --- MODE SELECTION TOGGLE ---
# Set to True: R_inner varies, cap_thick is calculated dynamically to keep R_outer constant.
# Set to False: Standard Cartesian product. Every parameter listed is swept normally.
CONSTANT_R_OUTER_MODE = True
R_OUTER_CONSTANT = 500  # Defined in nm (Only used if mode above is True)

if CONSTANT_R_OUTER_MODE:
    # ---------------- MODE: CONSTANT R_OUTER ----------------
    phase_space_values = {
        'Ext_elec_R_i': [0.02],
        'R_cap': [10],
        'R_inner': [20, 40, 60, 100], # <--- Vary this
        # Note: 'cap_thick' is NOT here because it will be calculated automatically
        'd': [0.02],
        'capillary_depth': [30, 50],
        'base_half_pitch': [1000],
        'V_ext': [100] 
    }
else:
    # ---------------- MODE: STANDARD SWEEP ------------------
    phase_space_values = {
        'Ext_elec_R_i': [0.0],
        'R_cap': [10],
        'R_inner': [20, 40, 60, 100],
        # 'cap_thick': [460],       # <--- Standard sweep explicitly lists cap_thick
        'd': [1],
        'capillary_depth': [10],
        'base_half_pitch': [1000],
        'V_ext': [100] 
    }

# Units remain consistent regardless of the mode selected above
phase_space_units = {
    'Ext_elec_R_i': 'mm',
    'R_cap': 'nm',
    'R_inner': 'nm',
    'cap_thick': 'nm',  
    'd': 'mm',
    'capillary_depth': 'um',
    'base_half_pitch': 'um',
    'V_ext': 'V'
}

# Define all mathematically supported units and their SI multipliers here
KNOWN_UNITS = {
    'mm': 1e-3, 
    'um': 1e-6, 
    'nm': 1e-9, 
    'm': 1.0, 
    'V': 1.0, 
    'kV': 1e3
}

# --- STRICT SAFEGUARD 1: Check for missing units ---
missing_units = set(phase_space_values.keys()) - set(phase_space_units.keys())
if missing_units:
    print("\n" + "!"*60)
    print("CRITICAL ERROR: MISSING UNITS IN PHASE SPACE")
    for param in missing_units: print(f"  -> {param}")
    sys.exit(1)

# --- STRICT SAFEGUARD 2: Check for unsupported units ---
unsupported_units = [f"{p}: '{u}'" for p, u in phase_space_units.items() if u not in KNOWN_UNITS]
if unsupported_units:
    print("\n" + "!"*60)
    print("CRITICAL ERROR: UNSUPPORTED UNITS DETECTED")
    for item in unsupported_units: print(f"  -> {item}")
    sys.exit(1)

# Build the phase space strings for COMSOL
phase_space = {
    param: [f"{val} [{phase_space_units[param]}]" for val in values]
    for param, values in phase_space_values.items()
}

keys = phase_space.keys()
combinations = list(itertools.product(*phase_space.values()))

run_list = []
for combo in combinations:
    params = dict(zip(keys, combo))
    
    # --- DYNAMIC PARAMETER INJECTION (Only triggers if in CONSTANT mode) ---
    if CONSTANT_R_OUTER_MODE:
        r_inner_val = float(params['R_inner'].split()[0])
        cap_thick_val = R_OUTER_CONSTANT - r_inner_val
        params['cap_thick'] = f"{cap_thick_val} [{phase_space_units['cap_thick']}]"
    # -----------------------------------------------------------------------
    
    params["Geometry_Type"] = GEOMETRY_TYPE
    params["COMSOL_File"] = mph_filename
    run_list.append(params)
# ==========================================
# 3. INITIALIZE COMSOL & FILTER COMPLETED RUNS
# ==========================================

print("Starting COMSOL Client...")
client = mph.start()
model = client.load(full_mph_path)

# --- LOAD MASTER LOG ---
if os.path.exists(master_json_path):
    with open(master_json_path, 'r') as f:
        master_log = json.load(f)
    print(f"Loaded existing master log with {len(master_log)} completed runs.")
else:
    master_log = []
    print("No existing master log found. Starting fresh.")

# --- LOAD GEOMETRY-SPECIFIC LOG ---
if os.path.exists(geometry_json_path):
    with open(geometry_json_path, 'r') as f:
        geo_log = json.load(f)
    print(f"Loaded existing {GEOMETRY_TYPE} log with {len(geo_log)} completed runs.")
else:
    geo_log = []
    print(f"No existing {GEOMETRY_TYPE} log found. Starting fresh.")

# --- Helper function to convert phase space strings (e.g., '400 [nm]') to SI floats ---
def get_si_value(val_str):
    if isinstance(val_str, (int, float)): return float(val_str)
    val_str = str(val_str).strip()
    if "[" in val_str and "]" in val_str:
        num_part = val_str.split("[")[0].strip()
        unit_part = val_str.split("[")[1].split("]")[0].strip()
        try:
            val = float(num_part)
            # Use the global KNOWN_UNITS dictionary we validated against
            return val * KNOWN_UNITS.get(unit_part, 1.0)
        except ValueError: pass
    try: return float(val_str)
    except ValueError: return val_str

total_runs = len(run_list)
pending_runs = []

for current_params in run_list:
    already_simulated = False
    for entry in master_log:
        is_match = True
        
        for param_key, param_value in current_params.items():
            # Check 1: Exact string match in Input_Parameters (handles Geometry_Type)
            if str(param_value) == str(entry.get('Input_Parameters', {}).get(param_key)):
                continue
            
            # Check 2: Exact string match in Parameter_Expressions (legacy hardcoded variables)
            if str(param_value) == str(entry.get('Parameter_Expressions', {}).get(param_key)):
                continue
            
            # Check 3: Mathematical match using Evaluated_Parameters (The Ultimate Fallback)
            if param_key not in ["Geometry_Type", "COMSOL_File"]:
                target_si = get_si_value(param_value)
                evaluated_val = entry.get('Evaluated_Parameters', {}).get(param_key)
                
                # If both are numbers, check if they match within a 0.001% tolerance
                if isinstance(target_si, float) and isinstance(evaluated_val, (int, float)):
                    if math.isclose(target_si, float(evaluated_val), rel_tol=1e-5):
                        continue # It's a numerical match!
                        
            # If all 3 checks fail, this is a genuinely new parameter setup
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
failed_empty_exports = []

for idx, current_params in enumerate(run_list):
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n[{run_timestamp}] --- Starting Run {idx + 1} of {total_runs} ---")
    
    # Build a safe, shorter run name for the Excel file
    name_parts = ["Run"]
    for k, v in current_params.items():
        # Do not include the long metadata strings in the filename
        if k not in ["Geometry_Type", "COMSOL_File"]:
            safe_val = str(v).replace(" ", "").replace("[", "").replace("]", "")
            name_parts.append(f"{k}_{safe_val}")
            
    run_name = "_".join(name_parts) + f"_{run_timestamp}"
    print(f"Configuration: {run_name}")
    
    
    run_results = {}  
    excel_path = os.path.join(output_dir, f"{run_name}.xlsx") 

    for param_name, param_value in current_params.items():
        # Do not try to feed the python-only metadata strings into COMSOL
        if param_name not in ["Geometry_Type", "COMSOL_File"]:
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

    # --- VALIDATION BLOCK ---
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
                loaded_dataframes[sheet_name] = df_data 
        except Exception:
            empty_exports.append(sheet_name)
            
    if empty_exports:
        print(f"  -> RUN FAILED VALIDATION! Empty data detected in: {empty_exports}")
        print("  -> Skipping Excel generation and log entry for this run.")
        
        failed_empty_exports.append({
            'Run_Name': run_name,
            'Empty_Files': empty_exports,
            'Parameters': current_params
        })
        continue 
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

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_params.to_excel(writer, sheet_name='Parameters', index=False)
        
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
    
    # --- UPDATE MASTER LOG ---
    master_log.append(log_entry)
    with open(master_json_path, 'w') as f:
        json.dump(master_log, f, indent=4)
        
    # --- UPDATE GEOMETRY-SPECIFIC LOG ---
    geo_log.append(log_entry)
    with open(geometry_json_path, 'w') as f:
        json.dump(geo_log, f, indent=4)

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