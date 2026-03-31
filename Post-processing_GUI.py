# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 02:41:01 2026

@author: pjoshi11
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# 1. PHYSICS CONSTANTS & FUNCTIONS
# ==========================================
SURFACE_TENSION = 0.0728  # N/m (Update for your fluid!)
EPSILON_0 = 8.854e-12     # F/m

def calculate_E_req_rayleigh(row):
    r_meters = row.get('R_cap', 0) * 1e-9 
    if pd.isna(r_meters) or r_meters <= 0: return np.nan
    return np.sqrt((2 * SURFACE_TENSION) / (EPSILON_0 * r_meters))

def calculate_E_req_taylor(row):
    r_meters = row.get('R_inner', 0) * 1e-9
    if pd.isna(r_meters) or r_meters <= 0: return np.nan
    return np.sqrt((SURFACE_TENSION) / (EPSILON_0 * r_meters)) # Placeholder formula

# ==========================================
# 2. DATA LOADING
# ==========================================
def load_data():
    folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
    json_path = os.path.join(folder_path, "PhaseSpace_Results", "master_simulation_log.json")
    
    if not os.path.exists(json_path):
        messagebox.showerror("Error", f"Could not find log file at:\n{json_path}")
        return None, []

    with open(json_path, 'r') as f:
        master_log = json.load(f)

    flat_data = []
    param_names = []
    
    # Grab parameter names dynamically from the first run
    if master_log:
        param_names = list(master_log[0].get('Input_Parameters', {}).keys())

    for entry in master_log:
        params = entry.get('Input_Parameters', {})
        results = entry.get('Results', {})
        
        def parse_val(v):
            try: return float(str(v).split()[0])
            except: return np.nan
            
        row = {'Run_Name': entry.get('Run_Name')}
        
        # Dynamically load all parameters
        for p in param_names:
            row[p] = parse_val(params.get(p))
            
        row['E_rayleigh_sim'] = results.get('E_rayleigh')
        row['E_taylor_sim'] = results.get('E_taylor')
        flat_data.append(row)

    df = pd.DataFrame(flat_data)
    df = df.dropna(subset=['E_rayleigh_sim', 'E_taylor_sim'])

    if not df.empty:
        df['E_req_rayleigh'] = df.apply(calculate_E_req_rayleigh, axis=1)
        df['E_req_taylor'] = df.apply(calculate_E_req_taylor, axis=1)
        
        # Assuming V_ext is your driving voltage parameter (fallback to 100 if missing)
        v_ext = df['V_ext'] if 'V_ext' in df.columns else 100
        df['V_onset_rayleigh'] = v_ext * (df['E_req_rayleigh'] / df['E_rayleigh_sim'])
        df['V_onset_taylor'] = v_ext * (df['E_req_taylor'] / df['E_taylor_sim'])

    return df, param_names

# ==========================================
# 3. GUI APPLICATION CLASS
# ==========================================
class PlotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("COMSOL Phase Space Visualizer")
        self.root.geometry("450x650")
        self.root.configure(padx=20, pady=20)

        # Load Data
        self.df, self.param_names = load_data()
        if self.df is None or self.df.empty:
            tk.Label(root, text="No valid data loaded.", fg="red").pack()
            return
            
        self.param_vars = {}      # Stores the selected value for N-1 parameters
        self.dropdowns = {}       # Stores the actual UI ComboBox widgets
        
        self.build_ui()

    def build_ui(self):
        # --- 1. X-Axis Selection ---
        tk.Label(self.root, text="1. Select Independent Variable (X-Axis)", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.x_axis_var = tk.StringVar()
        self.x_axis_cb = ttk.Combobox(self.root, textvariable=self.x_axis_var, values=self.param_names, state="readonly")
        self.x_axis_cb.pack(fill='x', pady=(0, 15))
        self.x_axis_cb.bind("<<ComboboxSelected>>", self.on_xaxis_change)
        
        # --- 2. N-1 Parameter Selection ---
        tk.Label(self.root, text="2. Set Constants (N-1 Parameters)", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.constants_frame = tk.Frame(self.root)
        self.constants_frame.pack(fill='x', pady=(0, 15))
        
        # Build dropdowns for all parameters
        for p in self.param_names:
            frame = tk.Frame(self.constants_frame)
            frame.pack(fill='x', pady=2)
            
            tk.Label(frame, text=p, width=15, anchor='w').pack(side='left')
            
            # Get unique sorted values for this parameter to populate the dropdown
            unique_vals = sorted(self.df[p].dropna().unique())
            unique_vals_str = [str(val) for val in unique_vals]
            
            var = tk.StringVar()
            if unique_vals_str:
                var.set(unique_vals_str[0]) # Default to first value
                
            cb = ttk.Combobox(frame, textvariable=var, values=unique_vals_str, state="readonly")
            cb.pack(side='right', fill='x', expand=True)
            
            self.param_vars[p] = var
            self.dropdowns[p] = cb

        # Initialize UI state (select the first parameter as default X-axis)
        if self.param_names:
            self.x_axis_cb.set(self.param_names[0])
            self.on_xaxis_change(None)

        # --- 3. Plot Options ---
        tk.Label(self.root, text="3. Plot Options", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.plot_rayleigh = tk.BooleanVar(value=True)
        self.plot_taylor = tk.BooleanVar(value=True)
        
        tk.Checkbutton(self.root, text="Plot Rayleigh Onset", variable=self.plot_rayleigh).pack(anchor='w')
        tk.Checkbutton(self.root, text="Plot Taylor Onset", variable=self.plot_taylor).pack(anchor='w')

        # --- 4. Plot Button ---
        ttk.Button(self.root, text="Generate Plot", command=self.generate_plot).pack(fill='x', pady=20, ipady=5)

    def on_xaxis_change(self, event):
        """Disables the dropdown for the selected X-axis parameter."""
        selected_x = self.x_axis_var.get()
        
        for p, cb in self.dropdowns.items():
            if p == selected_x:
                cb.set("--- (X-Axis) ---")
                cb.configure(state="disabled")
            else:
                cb.configure(state="readonly")
                # Reset to a valid number if it was previously disabled
                if cb.get() == "--- (X-Axis) ---":
                    valid_vals = cb['values']
                    if valid_vals: cb.set(valid_vals[0])

    def generate_plot(self):
        x_col = self.x_axis_var.get()
        
        # Build the filter condition based on N-1 dropdowns
        condition = pd.Series(True, index=self.df.index)
        plot_title_parts = []
        
        for p in self.param_names:
            if p != x_col:
                selected_val = float(self.param_vars[p].get())
                condition = condition & (self.df[p] == selected_val)
                plot_title_parts.append(f"{p}={selected_val}")
                
        # Filter the dataframe
        plot_df = self.df[condition].sort_values(x_col)
        
        if plot_df.empty:
            messagebox.showwarning("No Data", "No simulation runs match this exact combination of constants.")
            return
            
        # Create Plot
        plt.figure(figsize=(8, 5))
        
        if self.plot_rayleigh.get():
            plt.plot(plot_df[x_col], plot_df['V_onset_rayleigh'], marker='o', label='Rayleigh Onset', color='#1f77b4')
        if self.plot_taylor.get():
            plt.plot(plot_df[x_col], plot_df['V_onset_taylor'], marker='s', label='Taylor Onset', color='#d62728')
            
        plt.title(f"Effect of {x_col}\n" + " | ".join(plot_title_parts), fontsize=10)
        plt.xlabel(x_col)
        plt.ylabel("Onset Voltage (V)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        
        # Pops out a standard matplotlib interactive window
        plt.show()

# ==========================================
# 4. MAIN LOOP
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PlotDashboard(root)
    root.mainloop()