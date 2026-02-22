# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 12:13:56 2026

@author: pjoshi11
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FuncFormatter
import os

# ================= CONFIGURATION =================
BASE_DIR = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance'
INPUT_FILE = os.path.join(BASE_DIR, "Population analysis", "tip_population_summary.csv")

# Set which recipe you want to analyze here!
TARGET_RECIPE_LABEL = 'C' 

OUTPUT_PDF = os.path.join(BASE_DIR, "Population analysis", f'batch_variability_Recipe_{TARGET_RECIPE_LABEL}.pdf')

#=======================

def main():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find input file at {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Clean Data
    df = df.dropna(subset=['Predicted Diameter (nm)'])
    df = df[df['Predicted Diameter (nm)'] != 'N/A']
    df['Predicted Diameter (nm)'] = pd.to_numeric(df['Predicted Diameter (nm)'], errors='coerce')
    df = df[df['Predicted Diameter (nm)'] > 0]

    # Re-create Recipe Labels (Assuming this script is run standalone)
    recipe_cols = ['Heat', 'Pull', 'Velocity', 'Delay']
    df = df.dropna(subset=recipe_cols)
    for col in recipe_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    unique_recipes = df[recipe_cols].drop_duplicates().sort_values(by=recipe_cols)
    
    import string
    def label_generator():
        for i in range(100):
            yield string.ascii_uppercase[i]
            
    label_gen = label_generator()
    recipe_map = {tuple(row): next(label_gen) for _, row in unique_recipes.iterrows()}
    
    df['Recipe Label'] = df.apply(
        lambda x: recipe_map[tuple(x[col] for col in recipe_cols)], axis=1
    )

    # 2. Filter for the Target Recipe
    df_target = df[df['Recipe Label'] == TARGET_RECIPE_LABEL].copy()
    
    if df_target.empty:
        print(f"No data found for Recipe {TARGET_RECIPE_LABEL}.")
        return

    # 3. Handle Dates (Ensure chronological order on X-axis)
    # Convert string dates to actual datetime objects, sort them, then format back to clean strings
    df_target['Date Obj'] = pd.to_datetime(df_target['Preparation Date'], errors='coerce')
    df_target = df_target.sort_values(by='Date Obj')
    df_target['Clean Date'] = df_target['Date Obj'].dt.strftime('%b %d, %Y')

    # 4. Generate Visualization
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(8, 6))

    # Boxplot to show the median and spread (quartiles) for each batch
    sns.boxplot(
        data=df_target,
        x='Clean Date',
        y='Predicted Diameter (nm)',
        color="0.9",
        showfliers=False, # Hide outliers in the boxplot so the stripplot can handle them
        ax=ax
    )

    # Stripplot to show the actual individual tips
    sns.stripplot(
        data=df_target,
        x='Clean Date',
        y='Predicted Diameter (nm)',
        hue='Clean Date',
        jitter=True,
        size=7,
        alpha=0.8,
        palette="viridis",
        legend=False,
        ax=ax
    )

    # Log Scale Formatting
    ax.set_yscale('log')
    major_formatter = ScalarFormatter()
    major_formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(major_formatter)
    
    def custom_minor_formatter(x, pos):
        if x <= 0: return ""
        s = str(int(x))
        if s[0] in ['2', '5']: return s
        return ""
    ax.yaxis.set_minor_formatter(FuncFormatter(custom_minor_formatter))

    # Gridlines
    ax.grid(visible=True, which='major', axis='y', color='0.8', linestyle='-', linewidth=0.8)
    ax.grid(visible=True, which='minor', axis='y', color='0.9', linestyle=':', linewidth=0.5)

    # Labels
    recipe_params = unique_recipes.iloc[string.ascii_uppercase.index(TARGET_RECIPE_LABEL)]
    subtitle = f"Heat: {recipe_params['Heat']} | Pull: {recipe_params['Pull']} | Vel: {recipe_params['Velocity']} | Del: {recipe_params['Delay']}"
    
    ax.set_title(f'Batch Reproducibility for Recipe {TARGET_RECIPE_LABEL}\n({subtitle})', fontsize=14, pad=15)
    ax.set_xlabel('Preparation Date (Batch)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Predicted Pore Diameter (nm)', fontsize=12, fontweight='bold')
    
    # Rotate X-axis dates if they overlap
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(OUTPUT_PDF, dpi=300)
    print(f"Plot saved to: {OUTPUT_PDF}")
    plt.show()

if __name__ == "__main__":
    main()