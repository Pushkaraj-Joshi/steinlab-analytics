# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 17:15:02 2026

@author: pjoshi11
"""

import os
import glob
import json
import re
import time

# ================= CONFIGURATION =================
BASE_DIR = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance'
# =================================================

def get_file_timestamp(filepath):
    """Returns the last modification time of a file."""
    return os.path.getmtime(filepath)

def parse_txt_content(text):
    """
    Extracts metadata from a plain text block using Regex.
    Returns a dictionary matching your JSON structure.
    """
    data = {
        "experiment_id": "N/A",
        "tip_prepared_date": "N/A",
        "solute": "N/A",
        "solvent": "N/A",
        "recipe": {
            "Heat": "N/A", "Pull": "N/A", "Velocity": "N/A", "Delay": "N/A"
        },
        "comments": text.strip()
    }
    
    # Extract Standard Fields
    date_match = re.search(r"Tips prepared on\s+(.*?)[\n\r]", text, re.IGNORECASE)
    if date_match: data["tip_prepared_date"] = date_match.group(1).strip()

    solute_match = re.search(r"Solution\s*[-–:]\s*(.*?)[\n\r]", text, re.IGNORECASE)
    if solute_match: data["solute"] = solute_match.group(1).strip()
    
    solvent_match = re.search(r"Solvent\s*[-–:]\s*(.*?)[\n\r]", text, re.IGNORECASE)
    if solvent_match: data["solvent"] = solvent_match.group(1).strip()
    
    # Extract Recipe Items (simple key-value search)
    for key in ["Heat", "Pull", "Velocity", "Delay", "Filament"]:
        # Looks for "Heat: 700" or "Heat 700"
        rec_match = re.search(rf"{key}\s*[:=]?\s*(\d+)", text, re.IGNORECASE)
        if rec_match:
            data["recipe"][key] = int(rec_match.group(1))

    return [data] # Return as list to match your template format

def convert_txt_to_json_data(txt_path):
    """Reads a txt file and returns the Python object (list/dict) ready for JSON saving."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        # Case A: The .txt file actually contains JSON text (like your Sept 29 file)
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            # Case B: It is actual plain text -> Use Regex
            return parse_txt_content(raw_content)
            
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return None

def process_folder(folder_path):
    txt_files = glob.glob(os.path.join(folder_path, "Notes.txt"))
    json_files = glob.glob(os.path.join(folder_path, "Notes.json"))
    
    txt_path = txt_files[0] if txt_files else None
    json_path = json_files[0] if json_files else None

    # Case 1: No notes at all. Skip.
    if not txt_path and not json_path:
        return

    # Case 2: Only JSON exists. Perfect. Do nothing.
    if json_path and not txt_path:
        return

    # Case 3: Only TXT exists. Convert it.
    if txt_path and not json_path:
        print(f"[CONVERTING] Only .txt found in: {os.path.basename(folder_path)}")
        data = convert_txt_to_json_data(txt_path)
        if data:
            new_json_path = os.path.join(folder_path, "Notes.json")
            with open(new_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.remove(txt_path) # Delete the old txt
            print("   -> Created JSON and removed TXT.")
        return

    # Case 4: BOTH exist. Compare Timestamps.
    if txt_path and json_path:
        txt_time = get_file_timestamp(txt_path)
        json_time = get_file_timestamp(json_path)
        
        if txt_time > json_time:
            # TXT is newer. It has the latest updates. Overwrite JSON.
            print(f"[UPDATING] .txt is newer than .json in: {os.path.basename(folder_path)}")
            data = convert_txt_to_json_data(txt_path)
            if data:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                os.remove(txt_path)
                print("   -> Updated JSON from TXT and removed TXT.")
        else:
            # JSON is newer (or same). TXT is obsolete.
            print(f"[CLEANING] .json is newer. Removing obsolete .txt in: {os.path.basename(folder_path)}")
            os.remove(txt_path)

def main():
    print(f"Starting Cleanup on: {BASE_DIR}")
    print("---------------------------------------------------")
    
    count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        # We process every folder that contains files, looking for Notes
        process_folder(root)
        count += 1
        
    print("---------------------------------------------------")
    print(f"Cleanup Complete. Scanned {count} folders.")
    print("Your data is now standardized to JSON.")

if __name__ == "__main__":
    main()