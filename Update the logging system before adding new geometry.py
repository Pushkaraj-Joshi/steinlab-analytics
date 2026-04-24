# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 19:46:06 2026

@author: pjoshi11
"""

import json
import os

def split_master_json():
    # Define paths
    folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files\PhaseSpace_Results'
    master_json_path = os.path.join(folder_path, "master_simulation_log.json")

    if not os.path.exists(master_json_path):
        print(f"Error: Could not find {master_json_path}")
        return

    print("Loading Master JSON...")
    with open(master_json_path, 'r') as f:
        master_log = json.load(f)

    geometry_logs = {}
    unlabeled_count = 0

    # Sort runs into their respective geometry buckets
    for entry in master_log:
        params = entry.get('Input_Parameters', {})
        geo_type = params.get('Geometry_Type')

        # If an old run lacks the tag, assign it to Conical_Tip automatically
        if not geo_type:
            geo_type = "Conical_Tip"
            params['Geometry_Type'] = geo_type
            unlabeled_count += 1

        # Create a new list for this geometry if it doesn't exist yet
        if geo_type not in geometry_logs:
            geometry_logs[geo_type] = []

        geometry_logs[geo_type].append(entry)

    print(f"\nAnalysis Complete! Found {len(master_log)} total runs.")
    if unlabeled_count > 0:
        print(f"-> Auto-assigned 'Geometry_Type': 'Conical_Tip' to {unlabeled_count} older runs.")

    # Save the individual geometry files
    for geo_type, log_data in geometry_logs.items():
        geo_file_path = os.path.join(folder_path, f"{geo_type}_log.json")
        with open(geo_file_path, 'w') as f:
            json.dump(log_data, f, indent=4)
        print(f"-> Saved {len(log_data)} runs to {geo_file_path}")

    # If we had to fix unlabeled runs, update the Master file so it's clean too
    if unlabeled_count > 0:
        with open(master_json_path, 'w') as f:
            json.dump(master_log, f, indent=4)
        print("-> Updated Master JSON with missing geometry tags.")

if __name__ == "__main__":
    split_master_json()