# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 21:08:13 2026

@author: pjoshi11
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
        
        # Locate the Excel filename dynamically
        excel_file = ""
        for k, v in list(entry.items()) + list(results.items()):
            if isinstance(v, str) and (v.endswith('.xlsx') or v.endswith('.csv')):
                excel_file = v
                break
        row['Excel_File'] = excel_file
        
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
        self.root.geometry("1250x850")
        self.root.configure(padx=10, pady=10)

        self.df, self.param_names, self.param_units, self.folder_path = load_data()
        if self.df is None or self.df.empty:
            tk.Label(root, text="No valid data loaded.", fg="red").pack()
            return
            
        self.constant_vars = {} 
        
        self.left_panel = tk.Frame(self.root, width=400)
        self.left_panel.pack(side='left', fill='y', padx=(0, 10))
        
        self.right_panel = tk.Frame(self.root)
        self.right_panel.pack(side='right', fill='both', expand=True)

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.build_ui()

    def build_ui(self):
        f1 = tk.LabelFrame(self.left_panel, text="1. Axes Configuration", padx=10, pady=10)
        f1.pack(fill='x', pady=5)
        
        tk.Label(f1, text="X-Axis Variable:").grid(row=0, column=0, sticky='w')
        self.x_axis_var = tk.StringVar(value=self.param_names[0])
        self.x_axis_cb = ttk.Combobox(f1, textvariable=self.x_axis_var, values=self.param_names, state="readonly", width=18)
        self.x_axis_cb.grid(row=0, column=1, columnspan=3, padx=5, pady=2, sticky='w')
        self.x_axis_cb.bind("<<ComboboxSelected>>", self.update_dynamic_ui)

        tk.Label(f1, text="X-Axis Scale:").grid(row=1, column=0, sticky='w')
        self.x_scale = tk.StringVar(value="linear")
        ttk.Combobox(f1, textvariable=self.x_scale, values=["linear", "log"], state="readonly", width=8).grid(row=1, column=1, sticky='w', padx=5, pady=2)

        tk.Label(f1, text="Y-Axis Scale:").grid(row=2, column=0, sticky='w')
        self.y_scale = tk.StringVar(value="linear")
        ttk.Combobox(f1, textvariable=self.y_scale, values=["linear", "log"], state="readonly", width=8).grid(row=2, column=1, sticky='w', padx=5, pady=2)

        tk.Label(f1, text="X Limits (min, max):").grid(row=3, column=0, sticky='w', pady=(5,0))
        self.x_min_var = tk.StringVar()
        self.x_max_var = tk.StringVar()
        tk.Entry(f1, textvariable=self.x_min_var, width=8).grid(row=3, column=1, padx=2, pady=(5,0))
        tk.Entry(f1, textvariable=self.x_max_var, width=8).grid(row=3, column=2, padx=2, pady=(5,0))

        tk.Label(f1, text="Y Limits (min, max):").grid(row=4, column=0, sticky='w')
        self.y_min_var = tk.StringVar()
        self.y_max_var = tk.StringVar()
        tk.Entry(f1, textvariable=self.y_min_var, width=8).grid(row=4, column=1, padx=2)
        tk.Entry(f1, textvariable=self.y_max_var, width=8).grid(row=4, column=2, padx=2)

        f2 = tk.LabelFrame(self.left_panel, text="2. Grouping (Multiple Curves)", padx=10, pady=10)
        f2.pack(fill='x', pady=5)

        tk.Label(f2, text="Trace Separate Lines By:").grid(row=0, column=0, sticky='w')
        self.group_var = tk.StringVar(value="None")
        group_opts = ["None"] + self.param_names
        self.group_cb = ttk.Combobox(f2, textvariable=self.group_var, values=group_opts, state="readonly", width=18)
        self.group_cb.grid(row=0, column=1, padx=5, pady=2)
        self.group_cb.bind("<<ComboboxSelected>>", self.update_dynamic_ui)

        tk.Label(f2, text="Select Values (Hold Ctrl):").grid(row=1, column=0, sticky='nw', pady=5)
        
        self.group_listbox = tk.Listbox(f2, selectmode=tk.MULTIPLE, height=4, exportselection=False)
        self.group_listbox.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(f2, orient="vertical", command=self.group_listbox.yview)
        scrollbar.grid(row=1, column=2, sticky='ns', pady=5)
        self.group_listbox.config(yscrollcommand=scrollbar.set)

        self.f3 = tk.LabelFrame(self.left_panel, text="3. Set Constants", padx=10, pady=10)
        self.f3.pack(fill='x', pady=5)
        
        f4 = tk.Frame(self.left_panel)
        f4.pack(fill='x', pady=10)
        
        self.plot_rayleigh = tk.BooleanVar(value=True)
        self.plot_area_rayleigh = tk.BooleanVar(value=True)
        self.plot_taylor = tk.BooleanVar(value=True)
        self.auto_save = tk.BooleanVar(value=True) 
        
        tk.Checkbutton(f4, text="Plot Point Rayleigh", variable=self.plot_rayleigh).grid(row=0, column=0, sticky='w', padx=5)
        tk.Checkbutton(f4, text="Plot Taylor Limit", variable=self.plot_taylor).grid(row=1, column=0, sticky='w', padx=5)
        tk.Checkbutton(f4, text="Auto-Save as PDF", variable=self.auto_save, fg="blue").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        tk.Checkbutton(f4, text="Plot Area-Based Rayleigh", variable=self.plot_area_rayleigh).grid(row=0, column=1, sticky='w', padx=10)
        
        diam_frame = tk.Frame(f4)
        diam_frame.grid(row=1, column=1, sticky='w', padx=10)
        tk.Label(diam_frame, text="Target Diameter (nm):").pack(side='left')
        self.ion_diameter_var = tk.StringVar(value="0.5")
        tk.Entry(diam_frame, textvariable=self.ion_diameter_var, width=6).pack(side='left', padx=5)
        
        ttk.Button(self.left_panel, text="Generate Preview & Save", command=self.generate_plot).pack(fill='x', pady=10, ipady=8)

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
            ttk.Combobox(self.f3, textvariable=var, values=unique_vals_str, state="readonly", width=15).grid(row=row_idx, column=1, sticky='ew')
            self.constant_vars[p] = var
            row_idx += 1

    def calc_area_onset(self, row, target_radius_nm):
        """Extracts spatial data from the attached Excel file to find Area Onset."""
        run_name = str(row.get('Run_Name', ''))
        excel_name = row.get('Excel_File', '')
        
        # Smart locator: if JSON is missing the excel file name, recreate it
        if not excel_name or pd.isna(excel_name):
            excel_name = f"{run_name}.xlsx"
            
        # 1. Look for the Master Excel file
        possible_excel_paths = [
            os.path.join(self.folder_path, "PhaseSpace_Results", excel_name),
            os.path.join(self.folder_path, excel_name)
        ]
        excel_path = next((p for p in possible_excel_paths if os.path.exists(p)), None)
        
        # 2. If no full Excel, look for standalone CSV exported directly
        csv_name = excel_name.replace('.xlsx', ' - Meniscus_cap.csv')
        possible_csv_paths = [
            os.path.join(self.folder_path, "PhaseSpace_Results", csv_name),
            os.path.join(self.folder_path, csv_name)
        ]
        csv_path = next((p for p in possible_csv_paths if os.path.exists(p)), None)

        if not excel_path and not csv_path:
            return np.nan

        try:
            df_meniscus = None
            if excel_path:
                try:
                    # UPDATED to look for Meniscus_cap instead of Meniscus
                    df_meniscus = pd.read_excel(excel_path, sheet_name='Meniscus_cap')
                except ValueError:
                    df_meniscus = pd.read_excel(excel_path, sheet_name='Meniscus')
            elif csv_path:
                df_meniscus = pd.read_csv(csv_path)

            if df_meniscus is None or df_meniscus.empty:
                return np.nan

            # Autodetect columns
            angle_col = [c for c in df_meniscus.columns if 'angle' in str(c).lower() or 'theta' in str(c).lower()]
            e_col = [c for c in df_meniscus.columns if 'e' in str(c).lower() and ('field' in str(c).lower() or 'norm' in str(c).lower())]
            
            angles = df_meniscus[angle_col[0]].values if angle_col else df_meniscus.iloc[:, 0].values
            e_fields = df_meniscus[e_col[0]].values if e_col else df_meniscus.iloc[:, 1].values
            
            # Convert to radians if the data is in degrees
            if np.max(np.abs(angles)) > 7:
                angles = np.deg2rad(angles)
                
            r_cap_nm = float(row.get('R_cap', 0))
            if pd.isna(r_cap_nm) or r_cap_nm <= 0: return np.nan
            
            # Geometric mapping: map angle from the symmetry axis to flat projected radius 'r'
            r_arr = r_cap_nm * np.abs(np.sin(angles))
            
            # Sort for clean interpolation and drop duplicates
            sort_idx = np.argsort(r_arr)
            r_arr = r_arr[sort_idx]
            e_fields = e_fields[sort_idx]
            
            r_arr, unique_idx = np.unique(r_arr, return_index=True)
            e_fields = e_fields[unique_idx]
            
            # Interpolate E-field at the target boundary
            e_interp = np.interp(target_radius_nm, r_arr, e_fields)
            
            if e_interp <= 0: return np.nan
            v_ext = float(row.get('V_ext', 100))
            e_req = float(row.get('E_req_rayleigh', 0))
            if e_req <= 0: return np.nan
            
            return v_ext * (e_req / e_interp)
            
        except Exception as e:
            print(f"Error processing meniscus data for run {run_name}: {e}")
            return np.nan

    def generate_plot(self):
        x_col = self.x_axis_var.get()
        g_col = self.group_var.get()
        
        try:
            target_diam = float(self.ion_diameter_var.get())
        except ValueError:
            target_diam = 0.5
            messagebox.showwarning("Input Error", "Invalid diameter. Defaulting to 0.5 nm.")
        
        target_radius_nm = target_diam / 2.0
        
        condition = pd.Series(True, index=self.df.index)
        table_consts = [] 
        file_consts = []  
        
        for p, var in self.constant_vars.items():
            val = float(var.get())
            condition &= (self.df[p] == val)
            unit = self.param_units.get(p, "")
            unit_str = f" [{unit}]" if unit else ""
            table_consts.append(f"{p} = {val}{unit_str}")
            file_consts.append(f"{p}{val}")
            
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

        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        colors = plt.cm.tab10.colors 
        
        def plot_series(df_slice, label_suffix, color_idx):
            df_slice = df_slice.copy().sort_values(x_col)
            c = colors[color_idx % len(colors)]
            
            # 1. Point Rayleigh
            if self.plot_rayleigh.get():
                self.ax.plot(df_slice[x_col], df_slice['V_onset_rayleigh'], marker='o', linestyle='-', color=c, label=f"Point Rayleigh {label_suffix}")
            
            # 2. Taylor
            if self.plot_taylor.get():
                self.ax.plot(df_slice[x_col], df_slice['V_onset_taylor'], marker='s', linestyle='--', color=c, label=f"Taylor {label_suffix}")

            # 3. Area-Based Rayleigh
            if self.plot_area_rayleigh.get():
                # Provide terminal feedback
                print(f"Extracting spatial data for Area-Rayleigh {label_suffix}...")
                
                df_slice['V_onset_area'] = df_slice.apply(lambda row: self.calc_area_onset(row, target_radius_nm), axis=1)
                
                valid_count = df_slice['V_onset_area'].notna().sum()
                print(f" -> Found {valid_count} valid Area-Onset data points.")
                
                if not df_slice['V_onset_area'].isna().all():
                    self.ax.plot(df_slice[x_col], df_slice['V_onset_area'], marker='^', linestyle=':', color=c, label=f"Area Rayleigh (d={target_diam}nm) {label_suffix}")

        # Grouping Logic
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
        
        self.ax.set_title("Onset Voltage vs " + x_col, fontsize=12, pad=15)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel("Onset Voltage (V)")
        self.ax.set_xscale(self.x_scale.get())
        self.ax.set_yscale(self.y_scale.get())
        self.ax.grid(True, which="both", linestyle='--', alpha=0.5)

        try:
            if self.x_min_var.get(): self.ax.set_xlim(left=float(self.x_min_var.get()))
            if self.x_max_var.get(): self.ax.set_xlim(right=float(self.x_max_var.get()))
            if self.y_min_var.get(): self.ax.set_ylim(bottom=float(self.y_min_var.get()))
            if self.y_max_var.get(): self.ax.set_ylim(top=float(self.y_max_var.get()))
        except ValueError:
            messagebox.showerror("Limit Error", "Axis limits must be numbers.")

        self.ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left") 
        
        param_text = "Fixed Parameters:\n" + "-"*20 + "\n" + "\n".join(table_consts)
        props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.8)
        self.ax.text(1.04, 0.45, param_text, transform=self.ax.transAxes, fontsize=9,
                     verticalalignment='top', bbox=props)

        self.fig.subplots_adjust(right=0.7)
        self.canvas.draw()

        if self.auto_save.get():
            save_dir = os.path.join(self.folder_path, "Plots")
            os.makedirs(save_dir, exist_ok=True)
            
            safe_x = x_col.replace("/", "_")
            safe_g = g_col if g_col != "None" else "NoGroup"
            const_str = "_".join(file_consts)
            
            if len(const_str) > 80:
                const_str = const_str[:80] + "_etc"
                
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"Onset_vs_{safe_x}_Grp_{safe_g}_{const_str}_{timestamp}.pdf"
            filepath = os.path.join(save_dir, filename)
            
            self.fig.savefig(filepath, format='pdf', bbox_inches='tight')
            print(f"Saved PDF to: {filepath}")

# ==========================================
# 4. MAIN LOOP
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = PlotDashboard(root)
    root.mainloop()