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
    """
    Finds the PDF in the Analysis folder and regex searches the legend text
    for Pore Resistance and Diameter, including units.
    """
    results = {
        "Pore Resistance": "N/A",
        "Predicted Diameter": "N/A"
    }
    
    if not os.path.exists(analysis_folder_path):
        return results

    pdf_files = glob.glob(os.path.join(analysis_folder_path, "*.pdf"))
    
    if not pdf_files:
        return results

    try:
        reader = PdfReader(pdf_files[0])
        # Text is usually on the first page
        page = reader.pages[0]
        text = page.extract_text()
        
        # --- IMPROVED REGEX FOR RESISTANCE ---
        # 1. Look for "Pore Resistance" followed by optional spaces and "="
        # 2. Capture the number (digits and decimals)
        # 3. Capture the Unit prefix (M, G, k, T) if present
        # 4. Capture the Ohm symbol (often read as 'Ω', 'Ohm', or just text by pypdf)
        
        # This regex looks for: 
        # Number + optional space + (M/G/k/T) + optional space + Omega/Ohm
        res_match = re.search(r"Pore Resistance\s*=\s*([0-9\.]+)\s*([kMGT]?)\s*(?:[Ω]|Ohm|\\Omega)?", text, re.IGNORECASE)
        
        if res_match:
            value = res_match.group(1)       # The number (e.g., "10.53")
            prefix = res_match.group(2)      # The prefix (e.g., "M")
            
            # Combine them into a clean string
            # We assume the base unit is Ohms, so we just append the prefix + "Ω"
            results["Pore Resistance"] = f"{value} {prefix}Ω"

        # --- EXISTING REGEX FOR DIAMETER ---
        # Looking for "diameter =" followed by number and unit (nm, m, etc)
        dia_match = re.search(r"Predicted pore diameter\s*=\s*([0-9\.]+\s*[nmku]?m|N/A)", text, re.IGNORECASE)
        if dia_match:
            results["Predicted Diameter"] = dia_match.group(1).strip()

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
                "Pore Resistance": results["Pore Resistance"],
                "Predicted Diameter": results["Predicted Diameter"],
                "Path": root # Useful for debugging
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