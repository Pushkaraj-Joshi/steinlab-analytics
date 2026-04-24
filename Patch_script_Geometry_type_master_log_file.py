# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 15:48:41 2026

@author: pjoshi11
"""

import json
import os

def patch_master_json():
    # Define the path to your JSON file
    folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files\PhaseSpace_Results'
    json_path = os.path.join(folder_path, "master_simulation_log.json")
    
    if not os.path.exists(json_path):
        print(f"Error: Could not find {json_path}")
        return

    # 1. Load the existing log
    print("Loading master JSON...")
    with open(json_path, 'r') as f:
        master_log = json.load(f)
        
    updated_count = 0
    
    # 2. Iterate through all runs and inject the missing parameter
    for entry in master_log:
        params = entry.get('Input_Parameters', {})
        
        # If the parameter doesn't exist, this is an old run. Tag it as Conical_Tip.
        if 'Geometry_Type' not in params:
            params['Geometry_Type'] = "Conical_Tip"
            updated_count += 1
            
    # 3. Save the updated log back to the same file
    if updated_count > 0:
        with open(json_path, 'w') as f:
            json.dump(master_log, f, indent=4)
        print(f"Success! Retroactively tagged {updated_count} older runs with 'Geometry_Type': 'Conical_Tip'.")
    else:
        print("No older runs needed updating. The JSON is already up to date!")

if __name__ == "__main__":
    patch_master_json()