# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 16:28:20 2026

@author: pjoshi11
"""

import os
import glob
import json
import csv
import re
from pypdf import PdfReader  # pip install pypdf

# ================= CONFIGURATION =================
# Update this path to your actual Base Folder
BASE_DIR = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance'
OUTPUT_FOLDER_NAME = "Population analysis"
OUTPUT_FILE_NAME = "tip_population_summary.csv"
# =================================================

def convert_to_base_unit(value_str, unit_type):
    """
    Parses a string like "10.5 M" or "15 nm" and converts it to a float 
    in the requested base unit (Ohms for resistance, nm for diameter).
    """
    if not value_str:
        return "N/A"
        
    try:
        # Extract the numeric part and the text part
        # This regex looks for a number followed by any text
        match = re.match(r"([0-9\.]+)\s*([a-zA-ZµΩ]*)", value_str.strip())
        if not match:
            return "N/A"
            
        number = float(match.group(1))
        unit_suffix = match.group(2)
        
        if unit_type == 'resistance':
            # Multipliers for Ohms
            if 'G' in unit_suffix: return number * 1e9
            if 'M' in unit_suffix: return number * 1e6
            if 'k' in unit_suffix: return number * 1e3
            if 'T' in unit_suffix: return number * 1e12
            return number # Base Ohms
            
        elif unit_type == 'diameter':
            # Target is nanometers (nm)
            if 'nm' in unit_suffix: return number
            if 'µm' in unit_suffix or 'um' in unit_suffix: return number * 1000
            if 'mm' in unit_suffix: return number * 1e6
            if unit_suffix.strip() == 'm': return number * 1e9
            return number # Assume nm if unsure, or modify logic as needed
            
    except Exception as e:
        return "N/A"

def extract_metadata_from_notes(tip_folder_path):
    """
    Searches for Notes (.json preferred, then .txt) and extracts:
    Preparation Date, Recipe, Solute, Solvent.
    """
    data = {
        "Preparation Date": "N/A",
        "Recipe": "N/A",
        "Solute": "N/A",
        "Solvent": "N/A"
    }

    # 1. Try to find a JSON file first (Robust method)
    json_files = glob.glob(os.path.join(tip_folder_path, "Notes*.json"))
    
    if json_files:
        try:
            with open(json_files[0], 'r') as f:
                content = json.load(f)
                # Handle case where JSON is a list of dicts (as per your templates)
                if isinstance(content, list) and len(content) > 0:
                    note = content[0]
                else:
                    note = content

                data["Preparation Date"] = note.get("tip_prepared_date", "N/A")
                data["Solute"] = note.get("solute", "N/A")
                data["Solvent"] = note.get("solvent", "N/A")
                
                # Recipe might be a dictionary, convert to string for CSV compatibility
                recipe_data = note.get("recipe", "N/A")
                if isinstance(recipe_data, dict):
                    # Format it nicely like "Heat:690, Pull:210"
                    data["Recipe"] = ", ".join([f"{k}:{v}" for k, v in recipe_data.items()])
                else:
                    data["Recipe"] = str(recipe_data)
                    
            return data # Return immediately if JSON succeeded
        except Exception as e:
            print(f"Error reading JSON in {tip_folder_path}: {e}")

    # 2. Fallback to TXT file if JSON missing
    txt_files = glob.glob(os.path.join(tip_folder_path, "Notes*.txt"))
    if txt_files:
        try:
            with open(txt_files[0], 'r') as f:
                text = f.read()
                
            # Simple Regex parsing for the paragraph format
            # Looking for patterns like "Tips prepared on Sep 31, 2025"
            date_match = re.search(r"Tips prepared on\s+(.*?)[\n\r]", text, re.IGNORECASE)
            if date_match: data["Preparation Date"] = date_match.group(1).strip()

            solute_match = re.search(r"Solution\s*[-–:]\s*(.*?)[\n\r]", text, re.IGNORECASE)
            if solute_match: data["Solute"] = solute_match.group(1).strip()
            
            # Use 'Solute' as solvent if specific solvent field isn't explicitly in text
            # (Or refine regex if you have a specific "Solvent" line)
            
            recipe_match = re.search(r"Recipe\s*[-:]\s*(.*?)[\n\r]", text, re.IGNORECASE)
            if recipe_match: data["Recipe"] = recipe_match.group(1).strip()
            
        except Exception as e:
            print(f"Error reading TXT in {tip_folder_path}: {e}")

    return data

def extract_results_from_pdf(analysis_folder_path):
    results = {
        "Pore Resistance (Ohm)": "N/A",
        "Predicted Diameter (nm)": "N/A"
    }
    
    if not os.path.exists(analysis_folder_path):
        return results

    pdf_files = glob.glob(os.path.join(analysis_folder_path, "*.pdf"))
    if not pdf_files:
        return results

    try:
        reader = PdfReader(pdf_files[0])
        text = reader.pages[0].extract_text()
        
        # --- 1. Resistance Extraction ---
        # Capture number + prefix (k, M, G, T)
        res_match = re.search(r"Pore Resistance\s*=\s*([0-9\.]+)\s*([kMGT]?)", text, re.IGNORECASE)
        if res_match:
            raw_num = res_match.group(1)
            raw_prefix = res_match.group(2)
            # Pass combined string to converter (e.g. "10.5 M")
            results["Pore Resistance (Ohm)"] = convert_to_base_unit(f"{raw_num}{raw_prefix}", 'resistance')

        # --- 2. Diameter Extraction ---
        # Capture number + unit (nm, um, m)
        dia_match = re.search(r"Predicted pore diameter\s*=\s*([0-9\.]+)\s*([nμum]?m)", text, re.IGNORECASE)
        if dia_match:
            raw_num = dia_match.group(1)
            raw_unit = dia_match.group(2)
            # Pass combined string to converter (e.g. "15 nm")
            results["Predicted Diameter (nm)"] = convert_to_base_unit(f"{raw_num}{raw_unit}", 'diameter')

    except Exception as e:
        print(f"Error parsing PDF in {analysis_folder_path}: {e}")

    return results

def main():
    print(f"Scanning directory: {BASE_DIR}...")
    
    aggregated_data = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(BASE_DIR):
        # We are looking for folders that look like "Tip_XX" or "Tip XX"
        folder_name = os.path.basename(root)
        
        # flexible check: starts with 'Tip' and has a number (e.g. Tip_01, Tip 1)
        if folder_name.lower().startswith("tip") and any(char.isdigit() for char in folder_name):
            
            # --- 1. Identify Context (Date) ---
            # The parent folder is usually the Experiment/Recipe or Date
            # We try to climb up to find a folder that looks like a Date (20XX-XX-XX)
            path_parts = os.path.normpath(root).split(os.sep)
            date_folder = "Unknown"
            
            # Heuristic: Find the part that looks like a date 
            # (This handles both Level 1 and Level 2 variations)
            for part in path_parts:
                if re.match(r"20\d{2}[-_]\d{2}[-_]\d{2}", part) or \
                   re.match(r"[A-Za-z]{3}[-_]\d{2}[-_]\d{4}", part): # Matches Dec_05_2025
                    date_folder = part
            
            print(f"Processing: {date_folder} -> {folder_name}")

            # --- 2. Extract Metadata ---
            meta = extract_metadata_from_notes(root)
            
            # --- 3. Extract Results ---
            analysis_path = os.path.join(root, "Analysis")
            results = extract_results_from_pdf(analysis_path)
            
            # --- 4. Combine ---
            entry = {
                "Folder Date": date_folder,
                "Tip ID": folder_name,
                "Preparation Date": meta["Preparation Date"],
                "Recipe": meta["Recipe"],
                "Solute": meta["Solute"],
                "Solvent": meta["Solvent"],
                # UPDATED KEYS HERE
                "Pore Resistance (Ohm)": results["Pore Resistance (Ohm)"],
                "Predicted Diameter (nm)": results["Predicted Diameter (nm)"],
                "Path": root 
            }
            
            aggregated_data.append(entry)

    # --- 5. Export ---
    if aggregated_data:
        # Create Output Directory
        output_dir = os.path.join(BASE_DIR, OUTPUT_FOLDER_NAME)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_csv_path = os.path.join(output_dir, OUTPUT_FILE_NAME)
        
        keys = aggregated_data[0].keys()
        
        try:
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(aggregated_data)
            print(f"\nSUCCESS: Data exported to {output_csv_path}")
            print(f"Total Tips Processed: {len(aggregated_data)}")
        except PermissionError:
            print("\nERROR: Could not write to CSV. Is the file open in Excel?")
    else:
        print("\nNo 'Tip' folders found. Check your BASE_DIR path.")

if __name__ == "__main__":
    main()