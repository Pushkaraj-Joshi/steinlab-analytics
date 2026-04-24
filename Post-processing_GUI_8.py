# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 13:15:53 2026

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
EPSILON_0 = 8.85418782e-12# Vacuum permittivity (F/m)
q = 1.60217663e-19       # Elementary charge (C)
k_B = 1.380649e-23       # Boltzmann constant (J/K)
h = 6.62607015e-34       # Planck constant (J*s)
T = 298.0                # Temperature in Kelvin

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
            try: return float(str(v).split('[')[0].strip())
            except: return np.nan
            
        row = {'Run_Name': entry.get('Run_Name')}
        for p in param_names:
            row[p] = parse_val(params.get(p))
            
        row['E_rayleigh_sim'] = results.get('E_rayleigh')
        row['E_taylor_sim'] = results.get('E_taylor')
        
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
        
        # --- SCROLLABLE LEFT PANEL SETUP ---
        self.left_container = tk.Frame(self.root)
        self.left_container.pack(side='left', fill='y', padx=(0, 10))
        
        self.left_canvas = tk.Canvas(self.left_container, width=430, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(self.left_container, orient="vertical", command=self.left_canvas.yview)
        
        self.left_panel = tk.Frame(self.left_canvas, width=430)
        self.left_panel.bind("<Configure>", lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))
        self.left_canvas.create_window((0, 0), window=self.left_panel, anchor="nw")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        self.left_canvas.pack(side="left", fill="both", expand=True)
        self.left_scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # --- RIGHT PANEL (PLOT) ---
        self.right_panel = tk.Frame(self.root)
        self.right_panel.pack(side='right', fill='both', expand=True)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_panel)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        self.build_ui()

    def build_ui(self):
        # --- 0. Plot Mode Selection ---
        f0 = tk.LabelFrame(self.left_panel, text="0. Plot Mode", padx=10, pady=5)
        f0.pack(fill='x', pady=5)
        
        self.plot_mode = tk.StringVar(value="Onset Voltage")
        ttk.Radiobutton(f0, text="Onset Voltage (Phase Space)", variable=self.plot_mode, value="Onset Voltage", command=self.update_dynamic_ui).grid(row=0, column=0, sticky='w')
        ttk.Radiobutton(f0, text="Emission Rate vs Angle (Meniscus Cap)", variable=self.plot_mode, value="Emission Rate vs Angle", command=self.update_dynamic_ui).grid(row=1, column=0, sticky='w')
        ttk.Radiobutton(f0, text="E-field vs Depth (Cone + Base)", variable=self.plot_mode, value="E-field vs Depth", command=self.update_dynamic_ui).grid(row=2, column=0, sticky='w')

        # --- 1. Axis Configuration ---
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

        # --- 2. Grouping Variable ---
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
        
        list_scrollbar = ttk.Scrollbar(f2, orient="vertical", command=self.group_listbox.yview)
        list_scrollbar.grid(row=1, column=2, sticky='ns', pady=5)
        self.group_listbox.config(yscrollcommand=list_scrollbar.set)

        # --- 3. Constants (N-2 Parameters) ---
        self.f3 = tk.LabelFrame(self.left_panel, text="3. Set Constants", padx=10, pady=10)
        self.f3.pack(fill='x', pady=5)
        
        # --- 4. Plot Options & Button ---
        f4 = tk.LabelFrame(self.left_panel, text="4. Onset & Display Options", padx=10, pady=10)
        f4.pack(fill='x', pady=10)
        
        self.plot_rayleigh = tk.BooleanVar(value=True)
        self.plot_taylor = tk.BooleanVar(value=True)
        self.plot_area_rayleigh = tk.BooleanVar(value=True)
        self.auto_save = tk.BooleanVar(value=True) 
        
        norm_frame = tk.Frame(f4)
        norm_frame.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))
        tk.Label(norm_frame, text="Normalization:").pack(side='left')
        self.normalize_var = tk.StringVar(value="None")
        ttk.Combobox(norm_frame, textvariable=self.normalize_var, values=["None", "Group Max", "Individual Curve Max"], state="readonly", width=18).pack(side='left', padx=5)
        
        self.chk_rayleigh = tk.Checkbutton(f4, text="Plot Point Rayleigh", variable=self.plot_rayleigh)
        self.chk_rayleigh.grid(row=1, column=0, sticky='w')
        
        self.chk_taylor = tk.Checkbutton(f4, text="Plot Taylor Limit", variable=self.plot_taylor)
        self.chk_taylor.grid(row=2, column=0, sticky='w')
        
        self.chk_area = tk.Checkbutton(f4, text="Plot Area-Based Rayleigh", variable=self.plot_area_rayleigh)
        self.chk_area.grid(row=1, column=1, sticky='w', padx=5)
        
        diam_frame = tk.Frame(f4)
        diam_frame.grid(row=2, column=1, sticky='w', padx=5)
        self.lbl_diam = tk.Label(diam_frame, text="Target Diam (nm):")
        self.lbl_diam.pack(side='left')
        self.ion_diameter_var = tk.StringVar(value="0.5")
        self.entry_diam = tk.Entry(diam_frame, textvariable=self.ion_diameter_var, width=5)
        self.entry_diam.pack(side='left', padx=(2, 5))

        tk.Checkbutton(f4, text="Auto-Save as PDF", variable=self.auto_save, fg="blue").grid(row=3, column=0, sticky='w', pady=5)

        margin_frame = tk.Frame(f4)
        margin_frame.grid(row=3, column=1, sticky='w', padx=5)
        tk.Label(margin_frame, text="Plot Width (0.1-0.9):").pack(side='left')
        self.right_margin_var = tk.StringVar(value="0.55")
        tk.Entry(margin_frame, textvariable=self.right_margin_var, width=5).pack(side='left', padx=2)

        # Partition Option Frame
        part_frame = tk.Frame(f4)
        part_frame.grid(row=4, column=0, columnspan=2, sticky='w', pady=(5, 0))
        self.partition_var = tk.BooleanVar(value=False)
        self.chk_partition = tk.Checkbutton(part_frame, text="Partition by Angle (Ri > d*tanθ)", variable=self.partition_var, fg="purple")
        self.chk_partition.pack(side='left')
        
        self.lbl_angle = tk.Label(part_frame, text="θ (deg):")
        self.lbl_angle.pack(side='left', padx=(5, 2))
        self.partition_angle_var = tk.StringVar(value="40.7")
        self.entry_angle = tk.Entry(part_frame, textvariable=self.partition_angle_var, width=5)
        self.entry_angle.pack(side='left')

        # G0 (Activation Energy) Input Frame
        g0_frame = tk.Frame(f4)
        g0_frame.grid(row=5, column=0, columnspan=2, sticky='w', pady=(5, 0))
        self.lbl_g0 = tk.Label(g0_frame, text="G0 Activation Energy (eV):")
        self.lbl_g0.pack(side='left')
        self.g0_var = tk.StringVar(value="1.5")
        self.entry_g0 = tk.Entry(g0_frame, textvariable=self.g0_var, width=5)
        self.entry_g0.pack(side='left', padx=5)
        
        ttk.Button(self.left_panel, text="Generate Preview & Save", command=self.generate_plot).pack(fill='x', pady=10, ipady=8)

        self.update_dynamic_ui()

    def update_dynamic_ui(self, event=None):
        mode = self.plot_mode.get()
        x_col = self.x_axis_var.get()
        g_col = self.group_var.get()

        if mode in ["Emission Rate vs Angle", "E-field vs Depth"]:
            self.x_axis_cb.config(state="disabled")
            self.chk_rayleigh.config(state="disabled")
            self.chk_taylor.config(state="disabled")
            self.chk_area.config(state="disabled")
            self.entry_diam.config(state="disabled")
            self.lbl_diam.config(state="disabled")
            self.chk_partition.config(state="disabled")
            self.lbl_angle.config(state="disabled")
            self.entry_angle.config(state="disabled")
            
            # Enable G0 only for Emission Rate plot
            if mode == "Emission Rate vs Angle":
                self.lbl_g0.config(state="normal")
                self.entry_g0.config(state="normal")
            else:
                self.lbl_g0.config(state="disabled")
                self.entry_g0.config(state="disabled")
        else:
            self.x_axis_cb.config(state="readonly")
            self.chk_rayleigh.config(state="normal")
            self.chk_taylor.config(state="normal")
            self.chk_area.config(state="normal")
            self.entry_diam.config(state="normal")
            self.lbl_diam.config(state="normal")
            self.chk_partition.config(state="normal")
            self.lbl_angle.config(state="normal")
            self.entry_angle.config(state="normal")
            
            self.lbl_g0.config(state="disabled")
            self.entry_g0.config(state="disabled")

        self.group_listbox.delete(0, tk.END)
        
        if g_col != "None":
            if mode == "Onset Voltage" and g_col == x_col:
                messagebox.showwarning("Logic Error", "Grouping variable cannot be the same as the X-Axis.")
                self.group_var.set("None")
            else:
                unique_vals = sorted(self.df[g_col].dropna().unique())
                for val in unique_vals:
                    self.group_listbox.insert(tk.END, str(val))

        for widget in self.f3.winfo_children():
            widget.destroy()
            
        self.constant_vars.clear()
        
        row_idx = 0
        for p in self.param_names:
            if p == g_col or (mode == "Onset Voltage" and p == x_col):
                continue 
                
            tk.Label(self.f3, text=p, width=15, anchor='w').grid(row=row_idx, column=0, pady=2, sticky='w')
            unique_vals_str = [str(val) for val in sorted(self.df[p].dropna().unique())]
            
            var = tk.StringVar(value=unique_vals_str[0] if unique_vals_str else "")
            ttk.Combobox(self.f3, textvariable=var, values=unique_vals_str, state="readonly", width=15).grid(row=row_idx, column=1, sticky='ew')
            self.constant_vars[p] = var
            row_idx += 1
            
        self.root.update_idletasks()
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _load_meniscus_df(self, row, sheet_type="Meniscus_cap"):
        run_name = str(row.get('Run_Name', ''))
        excel_name = row.get('Excel_File', '')
        
        if not excel_name or pd.isna(excel_name):
            excel_name = f"{run_name}.xlsx"
            
        possible_excel_paths = [
            os.path.join(self.folder_path, "PhaseSpace_Results", excel_name),
            os.path.join(self.folder_path, excel_name)
        ]
        excel_path = next((p for p in possible_excel_paths if os.path.exists(p)), None)
        
        csv_name = excel_name.replace('.xlsx', f' - {sheet_type}.csv')
        possible_csv_paths = [
            os.path.join(self.folder_path, "PhaseSpace_Results", csv_name),
            os.path.join(self.folder_path, csv_name)
        ]
        csv_path = next((p for p in possible_csv_paths if os.path.exists(p)), None)

        try:
            if excel_path:
                try: return pd.read_excel(excel_path, sheet_name=sheet_type)
                except ValueError: 
                    if sheet_type == "Meniscus_cap": return pd.read_excel(excel_path, sheet_name='Meniscus')
            elif csv_path:
                return pd.read_csv(csv_path)
            return None
        except Exception as e:
            return None

    def calc_area_onset(self, row, target_radius_nm):
        df_meniscus = self._load_meniscus_df(row, "Meniscus_cap")
        if df_meniscus is None: return np.nan

        try:
            angle_col = [c for c in df_meniscus.columns if 'angle' in str(c).lower() or 'theta' in str(c).lower()]
            e_col = [c for c in df_meniscus.columns if 'e' in str(c).lower() and ('field' in str(c).lower() or 'norm' in str(c).lower())]
            
            angles = df_meniscus[angle_col[0]].values if angle_col else df_meniscus.iloc[:, 0].values
            e_fields = df_meniscus[e_col[0]].values if e_col else df_meniscus.iloc[:, 1].values
            
            if np.max(np.abs(angles)) > 7: angles = np.deg2rad(angles)
                
            r_cap_nm = float(row.get('R_cap', 0))
            if pd.isna(r_cap_nm) or r_cap_nm <= 0: return np.nan
            
            r_arr = r_cap_nm * np.abs(np.sin(angles))
            sort_idx = np.argsort(r_arr)
            r_arr = r_arr[sort_idx]
            e_fields = e_fields[sort_idx]
            
            r_arr, unique_idx = np.unique(r_arr, return_index=True)
            e_fields = e_fields[unique_idx]
            
            e_interp = np.interp(target_radius_nm, r_arr, e_fields)
            if e_interp <= 0: return np.nan
            
            v_ext = float(row.get('V_ext', 100))
            e_req = float(row.get('E_req_rayleigh', 0))
            if e_req <= 0: return np.nan
            
            return v_ext * (e_req / e_interp)
        except Exception:
            return np.nan

    def generate_plot(self):
        mode = self.plot_mode.get()
        x_col = self.x_axis_var.get()
        g_col = self.group_var.get()
        norm_type = self.normalize_var.get()
        
        try: target_diam = float(self.ion_diameter_var.get())
        except ValueError: target_diam = 0.5
        target_radius_nm = target_diam / 2.0
        
        try:
            right_margin = float(self.right_margin_var.get())
            if not (0.1 <= right_margin <= 0.95): right_margin = 0.55
        except ValueError:
            right_margin = 0.55
            
        try: G0_eV = float(self.g0_var.get())
        except ValueError: G0_eV = 1.5
        
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
            
        base_df = self.df[condition].copy()
        
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
        
        # ========================================================
        # PLOT MODE: E-FIELD VS DEPTH (CONE + BASE)
        # ========================================================
        if mode == "E-field vs Depth":
            plot_items = []
            all_efield_maxes = []
            global_min_z = 0

            def collect_edepth_row(row, label_suffix, color_idx):
                df_cone = self._load_meniscus_df(row, "Meniscus_cone")
                df_base = self._load_meniscus_df(row, "Meniscus_base")
                
                dfs = []
                if df_cone is not None and not df_cone.empty: dfs.append(df_cone)
                if df_base is not None and not df_base.empty: dfs.append(df_base)
                
                if dfs:
                    df_cb = pd.concat(dfs, ignore_index=True)
                    z_col = [c for c in df_cb.columns if 'z' in str(c).lower()]
                    e_col = [c for c in df_cb.columns if 'e' in str(c).lower() and ('field' in str(c).lower() or 'norm' in str(c).lower())]

                    z_vals = df_cb[z_col[0]].values if z_col else df_cb.iloc[:, 1].values
                    e_fields = df_cb[e_col[0]].values if e_col else df_cb.iloc[:, 2].values

                    sort_idx = np.argsort(z_vals)
                    z_vals = z_vals[sort_idx]
                    e_fields = e_fields[sort_idx]

                    max_e = np.max(e_fields)
                    all_efield_maxes.append(max_e)
                    
                    z_center = row.get('z_cap_center', np.min(z_vals))
                    if pd.isna(z_center): z_center = np.min(z_vals)
                    
                    plot_items.append({
                        'z': z_vals, 'e_fields': e_fields, 
                        'label': f"E-field {label_suffix}", 
                        'color_idx': color_idx, 'max_e': max_e, 'z_center': z_center
                    })

            if g_col == "None":
                df_subset = base_df.head(10) if len(base_df) > 10 else base_df
                if len(base_df) > 10: messagebox.showwarning("Warning", "Over 10 runs match. Showing first 10.")
                for idx, (_, row) in enumerate(df_subset.iterrows()):
                    collect_edepth_row(row, f"Run {str(row['Run_Name'])[-4:]}", idx)
            else:
                color_idx = 0
                for g_val in selected_groups:
                    g_df = base_df[base_df[g_col] == g_val]
                    if not g_df.empty:
                        row = g_df.iloc[0]
                        unit = self.param_units.get(g_col, "")
                        collect_edepth_row(row, f"({g_col}={g_val} {unit})", color_idx)
                        color_idx += 1

            group_max = max(all_efield_maxes) if all_efield_maxes else 1.0
            if group_max == 0: group_max = 1.0
                
            for item in plot_items:
                c = colors[item['color_idx'] % len(colors)]
                e_plot = item['e_fields']
                if norm_type == "Group Max": e_plot = e_plot / group_max
                elif norm_type == "Individual Curve Max": e_plot = e_plot / item['max_e'] if item['max_e'] != 0 else e_plot
                
                if item['z_center'] < global_min_z: global_min_z = item['z_center']
                self.ax.plot(item['z'], e_plot, linestyle='-', color=c, label=item['label'])

            self.ax.set_title("Electric Field vs Depth (Cone & Base)", fontsize=12, pad=15)
            self.ax.set_xlabel("Depth z (m)")
            self.ax.set_ylabel("Normalized Electric Field" if norm_type != "None" else "Electric Field (V/m)")
            self.ax.set_xlim(left=global_min_z, right=0)
            safe_x = "Depth_Z"

        # ========================================================
        # PLOT MODE: EMISSION RATE VS ANGLE (CAP)
        # ========================================================
        elif mode == "Emission Rate vs Angle":
            plot_items = []
            all_emission_maxes = []
            
            def collect_emission_row(row, label_suffix, color_idx):
                df_meniscus = self._load_meniscus_df(row, "Meniscus_cap")
                if df_meniscus is not None:
                    angle_col = [c for c in df_meniscus.columns if 'angle' in str(c).lower() or 'theta' in str(c).lower()]
                    e_col = [c for c in df_meniscus.columns if 'e' in str(c).lower() and ('field' in str(c).lower() or 'norm' in str(c).lower())]

                    angles = df_meniscus[angle_col[0]].values if angle_col else df_meniscus.iloc[:, 0].values
                    e_fields = df_meniscus[e_col[0]].values if e_col else df_meniscus.iloc[:, 1].values

                    # Force absolute value to avoid math domain errors in sqrt
                    e_fields_abs = np.abs(e_fields)
                    
                    # --- Emission Rate Calculation ---
                    # Calculate pre-exponential factor and Schottky barrier lowering
                    pre_factor = EPSILON_0 * e_fields_abs * (k_B * T) / h
                    barrier_lowering = np.sqrt((q**3 * e_fields_abs) / (4 * np.pi * EPSILON_0))
                    
                    # Convert G0 to Joules and calculate exponential term
                    G0_J = G0_eV * q
                    exponent = - (G0_J - barrier_lowering) / (k_B * T)
                    
                    # Calculate absolute emission rate (j_emission)
                    j_emission = pre_factor * np.exp(exponent)
                    
                    # Store max for Group Max calculations
                    j_max = np.max(j_emission)
                    all_emission_maxes.append(j_max)

                    # FIX: Append raw j_emission, NOT j_normalized!
                    plot_items.append({
                        'angles': angles, 
                        'e_fields': j_emission,  # <--- Changed here
                        'label': f"Emission {label_suffix}", 
                        'color_idx': color_idx, 
                        'max_e': j_max
                    })
            
            if g_col == "None":
                df_subset = base_df.head(10) if len(base_df) > 10 else base_df
                if len(base_df) > 10: messagebox.showwarning("Warning", "Over 10 runs match. Showing first 10.")
                for idx, (_, row) in enumerate(df_subset.iterrows()):
                    collect_emission_row(row, f"Run {str(row['Run_Name'])[-4:]}", idx)
            else:
                color_idx = 0
                for g_val in selected_groups:
                    g_df = base_df[base_df[g_col] == g_val]
                    if not g_df.empty:
                        row = g_df.iloc[0]
                        unit = self.param_units.get(g_col, "")
                        collect_emission_row(row, f"({g_col}={g_val} {unit})", color_idx)
                        color_idx += 1

            group_max = max(all_emission_maxes) if all_emission_maxes else 1.0
            if group_max == 0: group_max = 1.0
                
            for item in plot_items:
                c = colors[item['color_idx'] % len(colors)]
                e_plot = item['e_fields']
                
                # The GUI plotting loop correctly applies the normalization here:
                if norm_type == "Group Max": 
                    e_plot = e_plot / group_max
                elif norm_type == "Individual Curve Max": 
                    e_plot = e_plot / item['max_e'] if item['max_e'] != 0 else e_plot
                
                self.ax.plot(item['angles'], e_plot, linestyle='-', color=c, label=item['label'])

            self.ax.set_title("Emission Rate vs Meniscus Angle", fontsize=12, pad=15)
            self.ax.set_xlabel("Angle (deg)")
            self.ax.set_ylabel("Normalized Emission Rate" if norm_type != "None" else "Emission Rate ($m^{-2}s^{-1}$)")
            safe_x = "Angle"

        # ========================================================
        # PLOT MODE: ONSET VOLTAGE (PHASE SPACE)
        # ========================================================
        else:
            if self.plot_area_rayleigh.get():
                base_df['V_onset_area'] = base_df.apply(lambda row: self.calc_area_onset(row, target_radius_nm), axis=1)

            group_max = 1.0
            if norm_type == "Group Max":
                active_cols = []
                if self.plot_rayleigh.get() and 'V_onset_rayleigh' in base_df.columns: active_cols.append('V_onset_rayleigh')
                if self.plot_taylor.get() and 'V_onset_taylor' in base_df.columns: active_cols.append('V_onset_taylor')
                if self.plot_area_rayleigh.get() and 'V_onset_area' in base_df.columns: active_cols.append('V_onset_area')
                
                if active_cols:
                    group_max = base_df[active_cols].max().max()
                    if pd.isna(group_max) or group_max == 0: group_max = 1.0

            def plot_onset_series(df_slice, label_suffix, color_idx):
                df_slice = df_slice.sort_values(x_col)
                c = colors[color_idx % len(colors)]
                
                slice_max = 1.0
                if norm_type == "Individual Curve Max":
                    active_slice_cols = []
                    if self.plot_rayleigh.get() and 'V_onset_rayleigh' in df_slice.columns: active_slice_cols.append('V_onset_rayleigh')
                    if self.plot_taylor.get() and 'V_onset_taylor' in df_slice.columns: active_slice_cols.append('V_onset_taylor')
                    if self.plot_area_rayleigh.get() and 'V_onset_area' in df_slice.columns: active_slice_cols.append('V_onset_area')
                    if active_slice_cols:
                        slice_max = df_slice[active_slice_cols].max().max()
                        if pd.isna(slice_max) or slice_max == 0: slice_max = 1.0
                elif norm_type == "Group Max":
                    slice_max = group_max

                do_partition = self.partition_var.get() and 'd' in df_slice.columns and 'Ext_elec_R_i' in df_slice.columns
                if do_partition:
                    try:
                        theta_rad = np.radians(float(self.partition_angle_var.get()))
                        condition_met = df_slice['Ext_elec_R_i'] > df_slice['d'] * np.tan(theta_rad)
                    except ValueError:
                        condition_met = pd.Series(True, index=df_slice.index)
                        do_partition = False

                def draw_segments(x_key, y_key, marker, base_ls, label_text):
                    x_data = df_slice[x_key]
                    y_data = df_slice[y_key] / slice_max
                    
                    if do_partition:
                        if (~condition_met).all():
                            false_ls = ':' if base_ls != ':' else '-.'
                            self.ax.plot(x_data, y_data, marker=marker, linestyle=false_ls, color=c, alpha=0.4, label=f"{label_text} (Excluded)")
                        elif condition_met.all():
                            self.ax.plot(x_data, y_data, marker=marker, linestyle=base_ls, color=c, label=label_text)
                        else:
                            false_ls = ':' if base_ls != ':' else '-.'
                            self.ax.plot(x_data, y_data, marker=marker, linestyle=false_ls, color=c, alpha=0.4, label='_nolegend_')
                            self.ax.plot(x_data[condition_met], y_data[condition_met], marker=marker, linestyle=base_ls, color=c, label=label_text)
                    else:
                        self.ax.plot(x_data, y_data, marker=marker, linestyle=base_ls, color=c, label=label_text)

                if self.plot_rayleigh.get():
                    draw_segments(x_col, 'V_onset_rayleigh', 'o', '-', f"Point Rayleigh {label_suffix}")
                if self.plot_taylor.get():
                    draw_segments(x_col, 'V_onset_taylor', 's', '--', f"Taylor {label_suffix}")
                if self.plot_area_rayleigh.get() and 'V_onset_area' in df_slice.columns:
                    if not df_slice['V_onset_area'].isna().all():
                        draw_segments(x_col, 'V_onset_area', '^', ':', f"Area Rayleigh (d={target_diam}nm) {label_suffix}")

            if g_col == "None":
                plot_onset_series(base_df, "", 0)
            else:
                color_idx = 0
                for g_val in selected_groups:
                    g_df = base_df[base_df[g_col] == g_val]
                    if not g_df.empty:
                        unit = self.param_units.get(g_col, "")
                        plot_onset_series(g_df, f"({g_col}={g_val} {unit})", color_idx)
                        color_idx += 1

            x_unit = self.param_units.get(x_col, "")
            x_label = f"{x_col} ({x_unit})" if x_unit else x_col
            self.ax.set_title("Onset Voltage vs " + x_col, fontsize=12, pad=15)
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel("Normalized Onset Voltage" if norm_type != "None" else "Onset Voltage (V)")
            safe_x = x_col.replace("/", "_")

        # --- FINAL FORMATTING ---
        self.ax.set_xscale("linear" if mode in ["Emission Rate vs Angle", "E-field vs Depth"] else self.x_scale.get())
        self.ax.set_yscale(self.y_scale.get())
        self.ax.grid(True, which="both", linestyle='--', alpha=0.5)

        try:
            if self.x_min_var.get() and mode != "E-field vs Depth": self.ax.set_xlim(left=float(self.x_min_var.get()))
            if self.x_max_var.get() and mode != "E-field vs Depth": self.ax.set_xlim(right=float(self.x_max_var.get()))
            if self.y_min_var.get(): self.ax.set_ylim(bottom=float(self.y_min_var.get()))
            if self.y_max_var.get(): self.ax.set_ylim(top=float(self.y_max_var.get()))
        except ValueError: pass 

        self.ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left") 
        param_text = "Fixed Parameters:\n" + "-"*20 + "\n" + "\n".join(table_consts)
        props = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.8)
        self.ax.text(1.04, 0.45, param_text, transform=self.ax.transAxes, fontsize=9, verticalalignment='top', bbox=props)

        self.fig.subplots_adjust(right=right_margin)
        self.canvas.draw()

        if self.auto_save.get():
            save_dir = os.path.join(self.folder_path, "Plots")
            os.makedirs(save_dir, exist_ok=True)
            safe_g = g_col if g_col != "None" else "NoGroup"
            const_str = "_".join(file_consts)
            if len(const_str) > 80: const_str = const_str[:80] + "_etc"
            prefix = "EDepth_vs" if mode == "E-field vs Depth" else ("Emission_vs" if mode == "Emission Rate vs Angle" else "Onset_vs")
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{prefix}_{safe_x}_Grp_{safe_g}_{const_str}_{timestamp}.pdf"
            filepath = os.path.join(save_dir, filename)
            self.fig.savefig(filepath, format='pdf', bbox_inches='tight')
            print(f"Saved PDF to: {filepath}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlotDashboard(root)
    root.mainloop()