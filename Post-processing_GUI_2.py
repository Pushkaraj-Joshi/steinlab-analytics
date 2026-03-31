# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 03:13:54 2026

@author: pjoshi11
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# ==========================================
# 1. PHYSICS CONSTANTS & FUNCTIONS
# ==========================================
SURFACE_TENSION = 0.0728  # N/m 
EPSILON_0 = 8.854e-12     # F/m

def calculate_E_req_rayleigh(row):
    r_meters = row.get('R_cap', 0) * 1e-9 
    if pd.isna(r_meters) or r_meters <= 0: return np.nan
    return np.sqrt((4 * SURFACE_TENSION) / (EPSILON_0 * r_meters))

def calculate_E_req_taylor(row):
    r_meters = row.get('R_cap', 0) * 1e-9
    if pd.isna(r_meters) or r_meters <= 0: return np.nan
    return np.sqrt((2*SURFACE_TENSION) / (EPSILON_0 * r_meters))

# ==========================================
# 2. DATA LOADING & UNIT EXTRACTION
# ==========================================
def load_data():
    folder_path = r'C:\Users\pjoshi11\Documents\COMSOL_working files'
    json_path = os.path.join(folder_path, "PhaseSpace_Results", "master_simulation_log.json")
    
    if not os.path.exists(json_path):
        messagebox.showerror("Error", f"Could not find log file at:\n{json_path}")
        return None, [], {}, folder_path

    with open(json_path, 'r') as f:
        master_log = json.load(f)

    flat_data = []
    param_names = []
    param_units = {}
    
    if master_log:
        first_params = master_log[0].get('Input_Parameters', {})
        param_names = list(first_params.keys())
        for k, v in first_params.items():
            v_str = str(v)
            if '[' in v_str and ']' in v_str:
                param_units[k] = v_str.split('[')[1].split(']')[0]
            else:
                param_units[k] = "" 

    for entry in master_log:
        params = entry.get('Input_Parameters', {})
        results = entry.get('Results', {})
        
        def parse_val(v):
            try: return float(str(v).split()[0])
            except: return np.nan
            
        row = {'Run_Name': entry.get('Run_Name')}
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
        v_ext = df['V_ext'] if 'V_ext' in df.columns else 100
        df['V_onset_rayleigh'] = v_ext * (df['E_req_rayleigh'] / df['E_rayleigh_sim'])
        df['V_onset_taylor'] = v_ext * (df['E_req_taylor'] / df['E_taylor_sim'])

    return df, param_names, param_units, folder_path

# ==========================================
# 3. GUI APPLICATION CLASS
# ==========================================
class PlotDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("COMSOL Phase Space Visualizer")
        self.root.geometry("550x780")
        self.root.configure(padx=15, pady=15)

        self.df, self.param_names, self.param_units, self.folder_path = load_data()
        if self.df is None or self.df.empty:
            tk.Label(root, text="No valid data loaded.", fg="red").pack()
            return
            
        self.constant_vars = {} 
        self.build_ui()

    def build_ui(self):
        # --- 1. Axis Selection & Scaling ---
        f1 = tk.LabelFrame(self.root, text="1. Axes Configuration", padx=10, pady=10)
        f1.pack(fill='x', pady=5)
        
        tk.Label(f1, text="X-Axis Variable:").grid(row=0, column=0, sticky='w')
        self.x_axis_var = tk.StringVar(value=self.param_names[0])
        self.x_axis_cb = ttk.Combobox(f1, textvariable=self.x_axis_var, values=self.param_names, state="readonly", width=20)
        self.x_axis_cb.grid(row=0, column=1, padx=5, pady=2)
        self.x_axis_cb.bind("<<ComboboxSelected>>", self.update_dynamic_ui)

        tk.Label(f1, text="X-Axis Scale:").grid(row=1, column=0, sticky='w')
        self.x_scale = tk.StringVar(value="linear")
        ttk.Combobox(f1, textvariable=self.x_scale, values=["linear", "log"], state="readonly", width=8).grid(row=1, column=1, sticky='w', padx=5, pady=2)

        tk.Label(f1, text="Y-Axis Scale:").grid(row=2, column=0, sticky='w')
        self.y_scale = tk.StringVar(value="linear")
        ttk.Combobox(f1, textvariable=self.y_scale, values=["linear", "log"], state="readonly", width=8).grid(row=2, column=1, sticky='w', padx=5, pady=2)

        # --- 2. Grouping Variable (Multiple Curves) ---
        f2 = tk.LabelFrame(self.root, text="2. Grouping (Multiple Curves)", padx=10, pady=10)
        f2.pack(fill='x', pady=5)

        tk.Label(f2, text="Trace Separate Lines By:").grid(row=0, column=0, sticky='w')
        self.group_var = tk.StringVar(value="None")
        group_opts = ["None"] + self.param_names
        self.group_cb = ttk.Combobox(f2, textvariable=self.group_var, values=group_opts, state="readonly", width=20)
        self.group_cb.grid(row=0, column=1, padx=5, pady=2)
        self.group_cb.bind("<<ComboboxSelected>>", self.update_dynamic_ui)

        tk.Label(f2, text="Select Values (Hold Ctrl):").grid(row=1, column=0, sticky='nw', pady=5)
        
        self.group_listbox = tk.Listbox(f2, selectmode=tk.MULTIPLE, height=4, exportselection=False)
        self.group_listbox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(f2, orient="vertical", command=self.group_listbox.yview)
        scrollbar.grid(row=1, column=2, sticky='ns', pady=5)
        self.group_listbox.config(yscrollcommand=scrollbar.set)

        # --- 3. Constants (N-2 Parameters) ---
        self.f3 = tk.LabelFrame(self.root, text="3. Set Constants", padx=10, pady=10)
        self.f3.pack(fill='x', pady=5)
        
        # --- 4. Plot Options & Button ---
        f4 = tk.Frame(self.root)
        f4.pack(fill='x', pady=10)
        
        self.plot_rayleigh = tk.BooleanVar(value=True)
        self.plot_taylor = tk.BooleanVar(value=True)
        self.auto_save = tk.BooleanVar(value=True) # Enabled by default
        
        tk.Checkbutton(f4, text="Plot Rayleigh", variable=self.plot_rayleigh).pack(side='left', padx=5)
        tk.Checkbutton(f4, text="Plot Taylor", variable=self.plot_taylor).pack(side='left', padx=5)
        tk.Checkbutton(f4, text="Auto-Save as PDF", variable=self.auto_save, fg="blue").pack(side='right', padx=5)
        
        ttk.Button(self.root, text="Generate Plot", command=self.generate_plot).pack(fill='x', pady=10, ipady=5)

        self.update_dynamic_ui()

    def update_dynamic_ui(self, event=None):
        x_col = self.x_axis_var.get()
        g_col = self.group_var.get()

        self.group_listbox.delete(0, tk.END)
        if g_col != "None" and g_col != x_col:
            unique_vals = sorted(self.df[g_col].dropna().unique())
            for val in unique_vals:
                self.group_listbox.insert(tk.END, str(val))
        elif g_col == x_col:
            messagebox.showwarning("Logic Error", "Grouping variable cannot be the same as the X-Axis.")
            self.group_var.set("None")

        for widget in self.f3.winfo_children():
            widget.destroy()
            
        self.constant_vars.clear()
        
        row_idx = 0
        for p in self.param_names:
            if p == x_col or p == g_col:
                continue 
                
            tk.Label(self.f3, text=p, width=15, anchor='w').grid(row=row_idx, column=0, pady=2, sticky='w')
            unique_vals_str = [str(val) for val in sorted(self.df[p].dropna().unique())]
            
            var = tk.StringVar(value=unique_vals_str[0] if unique_vals_str else "")
            ttk.Combobox(self.f3, textvariable=var, values=unique_vals_str, state="readonly").grid(row=row_idx, column=1, sticky='ew')
            self.constant_vars[p] = var
            row_idx += 1

    def generate_plot(self):
        x_col = self.x_axis_var.get()
        g_col = self.group_var.get()
        
        condition = pd.Series(True, index=self.df.index)
        title_consts = []
        file_consts = [] # Compact list for the filename
        
        for p, var in self.constant_vars.items():
            val = float(var.get())
            condition &= (self.df[p] == val)
            title_consts.append(f"{p}={val}")
            file_consts.append(f"{p}{val}") # e.g., "d1.0" or "R_inner10.0"
            
        base_df = self.df[condition]
        
        if base_df.empty:
            messagebox.showwarning("No Data", "No runs match the selected constants.")
            return

        selected_groups = []
        if g_col != "None":
            selected_indices = self.group_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("Selection Required", f"Please select at least one value for {g_col}.")
                return
            selected_groups = [float(self.group_listbox.get(i)) for i in selected_indices]

        plt.figure(figsize=(9, 6))
        colors = plt.cm.tab10.colors 
        
        def plot_series(df_slice, label_suffix, color_idx):
            df_slice = df_slice.sort_values(x_col)
            c = colors[color_idx % len(colors)]
            if self.plot_rayleigh.get():
                plt.plot(df_slice[x_col], df_slice['V_onset_rayleigh'], marker='o', linestyle='-', color=c, label=f"Rayleigh {label_suffix}")
            if self.plot_taylor.get():
                plt.plot(df_slice[x_col], df_slice['V_onset_taylor'], marker='s', linestyle='--', color=c, label=f"Taylor {label_suffix}")

        if g_col == "None":
            plot_series(base_df, "", 0)
        else:
            color_idx = 0
            for g_val in selected_groups:
                g_df = base_df[base_df[g_col] == g_val]
                if not g_df.empty:
                    unit = self.param_units.get(g_col, "")
                    unit_str = f" {unit}" if unit else ""
                    plot_series(g_df, f"({g_col}={g_val}{unit_str})", color_idx)
                    color_idx += 1

        x_unit = self.param_units.get(x_col, "")
        x_label = f"{x_col} ({x_unit})" if x_unit else x_col
        
        plt.title("Onset Voltage vs " + x_col + "\n" + " | ".join(title_consts), fontsize=10)
        plt.xlabel(x_label)
        plt.ylabel("Onset Voltage (V)")
        plt.xscale(self.x_scale.get())
        plt.yscale(self.y_scale.get())
        plt.grid(True, which="both", linestyle='--', alpha=0.5)
        plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left") 
        plt.tight_layout()

        # --- NEW: PDF AUTO-SAVE LOGIC ---
        if self.auto_save.get():
            save_dir = os.path.join(self.folder_path, "Plots")
            os.makedirs(save_dir, exist_ok=True)
            
            safe_x = x_col.replace("/", "_")
            safe_g = g_col if g_col != "None" else "NoGroup"
            const_str = "_".join(file_consts)
            
            # Prevent the filename from exceeding OS length limits
            if len(const_str) > 80:
                const_str = const_str[:80] + "_etc"
                
            # Add a quick timestamp so you don't overwrite older plots by mistake
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"Onset_vs_{safe_x}_Grp_{safe_g}_{const_str}_{timestamp}.pdf"
            
            filepath = os.path.join(save_dir, filename)
            plt.savefig(filepath, format='pdf', bbox_inches='tight')
            print(f"Saved PDF to: {filepath}")

        # Show the plot window last
        plt.show()

# ==========================================
# 4. MAIN LOOP
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PlotDashboard(root)
    root.mainloop()