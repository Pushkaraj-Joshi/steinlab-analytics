# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 16:53:40 2026

@author: pjoshi11
"""
import os
import glob
import json
import csv
import re
from pypdf import PdfReader

# ================= CONFIGURATION =================
# Ensure this path is exactly correct (no trailing spaces)
BASE_DIR = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance'
OUTPUT_FOLDER_NAME = "Population analysis"
OUTPUT_FILE_NAME = "tip_population_summary.csv"
# =================================================

def convert_to_base_unit(value_str, unit_type):
    """
    Parses strings like "10.5 M" or "15 nm" and converts to float base units.
    """
    if not value_str or value_str == "N/A":
        return "N/A"
        
    try:
        # Regex to separate number and unit (e.g., "10.5" and "M")
        match = re.match(r"([0-9\.]+)\s*([a-zA-ZµΩ]*)", str(value_str).strip())
        if not match: return "N/A"
            
        number = float(match.group(1))
        unit_suffix = match.group(2)
        
        if unit_type == 'resistance':
            if 'G' in unit_suffix: return number * 1e9
            if 'M' in unit_suffix: return number * 1e6
            if 'k' in unit_suffix: return number * 1e3
            return number 
            
        elif unit_type == 'diameter':
            if 'nm' in unit_suffix: return number
            if 'µm' in unit_suffix or 'um' in unit_suffix: return number * 1000
            if 'm' in unit_suffix: return number * 1e9
            return number 
            
    except Exception:
        return "N/A"

def parse_notes_file(file_path):
    """
    Robust parser: Extracts standard fields plus pH and Conductivity.
    """
    # Initialize all fields with N/A
    data = {
        "Preparation Date": "N/A", "Solute": "N/A", "Solvent": "N/A",
        "pH": "N/A", "Conductivity": "N/A",
        "Heat": "N/A", "Pull": "N/A", "Velocity": "N/A", "Delay": "N/A"
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
            
        # --- STRATEGY 1: JSON Parsing ---
        try:
            content = json.loads(text_content)
            note = content[0] if isinstance(content, list) else content
            
            # Extract Fields
            data["Preparation Date"] = note.get("tip_prepared_date", "N/A")
            data["Solute"] = note.get("solute", "N/A")
            data["Solvent"] = note.get("solvent", "N/A")
            data["pH"] = note.get("pH", "N/A")
            data["Conductivity"] = note.get("conductivity", "N/A")
            
            # Extract Recipe
            recipe = note.get("recipe", {})
            if isinstance(recipe, dict):
                data["Heat"] = recipe.get("Heat", "N/A")
                data["Pull"] = recipe.get("Pull", "N/A")
                data["Velocity"] = recipe.get("Velocity", "N/A")
                data["Delay"] = recipe.get("Delay", "N/A")
            
            return data # Success

        except json.JSONDecodeError:
            pass # Fallback to Text/Regex

        # --- STRATEGY 2: Text/Regex Fallback ---
        
        # Existing regex...
        date_match = re.search(r"Tips prepared on\s+(.*?)[\n\r]", text_content, re.IGNORECASE)
        if date_match: data["Preparation Date"] = date_match.group(1).strip()

        solute_match = re.search(r"Solution\s*[-–:]\s*(.*?)[\n\r]", text_content, re.IGNORECASE)
        if solute_match: data["Solute"] = solute_match.group(1).strip()
        
        # New regex for pH and Conductivity
        ph_match = re.search(r"pH\s*[:=]?\s*([0-9\.]+)", text_content, re.IGNORECASE)
        if ph_match: data["pH"] = ph_match.group(1).strip()

        cond_match = re.search(r"Conductivity\s*[:=]?\s*([0-9\.]+)", text_content, re.IGNORECASE)
        if cond_match: data["Conductivity"] = cond_match.group(1).strip()

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
            
    return data

def get_hierarchical_metadata(tip_folder_path):
    # Update defaults to include new fields
    final_data = {
        "Preparation Date": "N/A", "Solute": "N/A", "Solvent": "N/A",
        "pH": "N/A", "Conductivity": "N/A",
        "Heat": "N/A", "Pull": "N/A", "Velocity": "N/A", "Delay": "N/A"
     }
    def find_best_note(directory):
        # Priority 1: JSON
        jsons = glob.glob(os.path.join(directory, "Notes*.json"))
        if jsons: return jsons[0]
        # Priority 2: TXT
        txts = glob.glob(os.path.join(directory, "Notes*.txt"))
        if txts: return txts[0]
        return None

    # Step 1: Check Tip Folder
    tip_file = find_best_note(tip_folder_path)
    if tip_file:
        final_data.update(parse_notes_file(tip_file))
    else:
        # Step 2: Check Parent Folder
        parent_dir = os.path.dirname(tip_folder_path)
        parent_file = find_best_note(parent_dir)
        if parent_file:
            print(f"   -> Inheriting metadata from parent: {os.path.basename(parent_dir)}")
            final_data.update(parse_notes_file(parent_file))

    return final_data

def extract_results_from_pdf(analysis_folder_path):
    results = {
        "Pore Resistance (Ohm)": "N/A",
        "Predicted Diameter (nm)": "N/A"
    }
    
    if not os.path.exists(analysis_folder_path): return results
    pdf_files = glob.glob(os.path.join(analysis_folder_path, "*.pdf"))
    if not pdf_files: return results

    try:
        reader = PdfReader(pdf_files[0])
        text = reader.pages[0].extract_text()
        
        # Resistance (Look for number + prefix + Ohm)
        res_match = re.search(r"Pore Resistance\s*=\s*([0-9\.]+)\s*([kMGT]?)", text, re.IGNORECASE)
        if res_match:
            results["Pore Resistance (Ohm)"] = convert_to_base_unit(f"{res_match.group(1)}{res_match.group(2)}", 'resistance')

        # Diameter (Look for number + unit)
        dia_match = re.search(r"Predicted pore diameter\s*=\s*([0-9\.]+)\s*([nμum]?m)", text, re.IGNORECASE)
        if dia_match:
            results["Predicted Diameter (nm)"] = convert_to_base_unit(f"{dia_match.group(1)}{dia_match.group(2)}", 'diameter')

    except Exception as e:
        print(f"Error parsing PDF in {analysis_folder_path}: {e}")

    return results

def main():
    print(f"Scanning directory: {BASE_DIR}...")
    aggregated_data = []

    for root, dirs, files in os.walk(BASE_DIR):
        folder_name = os.path.basename(root)
        
        # Looser check: 'Tip' anywhere in name + contains digit (e.g. Tip 1, Tip_01)
        if "tip" in folder_name.lower() and any(char.isdigit() for char in folder_name):
            
            # Attempt to identify the date from path
            path_parts = os.path.normpath(root).split(os.sep)
            date_folder = "Unknown"
            for part in path_parts:
                # Matches YYYY-MM-DD or Mon_DD_YYYY
                if re.search(r"\d{4}[-_]\d{2}[-_]\d{2}", part) or re.search(r"[A-Za-z]{3}[-_]\d{2}", part):
                    date_folder = part
            
            print(f"Processing: {date_folder} -> {folder_name}")

            # --- Extract Metadata ---
            meta = get_hierarchical_metadata(root)
            
            # --- Extract Results ---
            results = extract_results_from_pdf(os.path.join(root, "Analysis"))
            
            # --- Combine ---
            entry = {
                "Folder Date": date_folder,
                "Tip ID": folder_name,
                "Preparation Date": meta["Preparation Date"],
                "Solute": meta["Solute"],
                "Solvent": meta["Solvent"],
                "pH": meta["pH"],                         # <--- NEW
                "Conductivity": meta["Conductivity"],     # <--- NEW
                "Heat": meta["Heat"],
                "Pull": meta["Pull"],
                "Velocity": meta["Velocity"],
                "Delay": meta["Delay"],
                "Pore Resistance (Ohm)": results["Pore Resistance (Ohm)"],
                "Predicted Diameter (nm)": results["Predicted Diameter (nm)"],
                "Path": root
            }
            aggregated_data.append(entry)

    # --- Export ---
    if aggregated_data:
        output_dir = os.path.join(BASE_DIR, OUTPUT_FOLDER_NAME)
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        output_csv_path = os.path.join(output_dir, OUTPUT_FILE_NAME)
        
        try:
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
                dict_writer = csv.DictWriter(f, fieldnames=aggregated_data[0].keys())
                dict_writer.writeheader()
                dict_writer.writerows(aggregated_data)
            print(f"\nSUCCESS: Data exported to {output_csv_path}")
            print(f"Total Tips Processed: {len(aggregated_data)}")
        except PermissionError:
            print("\nERROR: Could not write to CSV. Is the file open in Excel?")
    else:
        print("\nNo 'Tip' folders found. Please double-check the BASE_DIR path.")

if __name__ == "__main__":
    main()