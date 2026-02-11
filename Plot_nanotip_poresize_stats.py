# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 23:58:27 2026

@author: pjoshi11
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FuncFormatter # <--- Add FuncFormatter to imports
import os
import string

# ================= CONFIGURATION =================
# Update this path if necessary to match your computer
BASE_DIR = r'D:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip_conductance'
INPUT_FILE = os.path.join(BASE_DIR, "Population analysis", "tip_population_summary.csv")
OUTPUT_PDF = os.path.join(BASE_DIR, "Population analysis", "pore_diameter_analysis.pdf")
OUTPUT_KEY_CSV = os.path.join(BASE_DIR, "Population analysis", "recipe_key.csv")
# =================================================

def main():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Could not find input file at {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # Filter and Clean
    df = df.dropna(subset=['Predicted Diameter (nm)'])
    df = df[df['Predicted Diameter (nm)'] != 'N/A']
    
    numeric_cols = ['Predicted Diameter (nm)', 'Heat', 'Pull', 'Velocity', 'Delay']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['Heat', 'Pull', 'Velocity', 'Delay', 'Predicted Diameter (nm)'])
    # Filter out zeros or negative numbers which break log scales
    df = df[df['Predicted Diameter (nm)'] > 0]

    print(f"Loaded {len(df)} valid data points.")

    # 2. Categorize Recipes
    recipe_cols = ['Heat', 'Pull', 'Velocity', 'Delay']
    unique_recipes = df[recipe_cols].drop_duplicates().sort_values(by=recipe_cols)
    
    def label_generator():
        for i in range(100):
            yield string.ascii_uppercase[i]
            
    label_gen = label_generator()
    recipe_map = {}
    
    for index, row in unique_recipes.iterrows():
        label = next(label_gen)
        combo = tuple(row[col] for col in recipe_cols)
        recipe_map[combo] = label

    df['Recipe Label'] = df.apply(
        lambda x: recipe_map[tuple(x[col] for col in recipe_cols)], axis=1
    )

    # Force Alphabetical Order
    sorted_labels = sorted(df['Recipe Label'].unique())
    df['Recipe Label'] = pd.Categorical(df['Recipe Label'], categories=sorted_labels, ordered=True)

    # Prepare Table Data (Label + Parameters)
    table_data = []
    for combo, label in recipe_map.items():
        # Only include labels that are actually in the sorted list (present in data)
        if label in sorted_labels:
            table_data.append([label, combo[0], combo[1], combo[2], combo[3]])
    
    # Sort table data by Label to match the X-axis
    table_data.sort(key=lambda x: x[0])
    
    # 3. Generate Visualization
    sns.set_theme(style="whitegrid")
    
    # Increase figure width to make room for the table on the right
    fig, ax = plt.subplots(figsize=(14, 7))

    # A. Violin Plot
    sns.violinplot(
        data=df, 
        x='Recipe Label', 
        y='Predicted Diameter (nm)',
        inner=None,
        color="0.9",
        linewidth=1,
        cut=0,
        ax=ax
    )

    # B. Swarm Plot
    sns.stripplot(
        data=df, 
        x='Recipe Label', 
        y='Predicted Diameter (nm)',
        hue='Preparation Date',
        dodge=False,
        jitter=True,
        size=6,
        alpha=0.8,
        palette="viridis",
        ax=ax
    )

    # C. Set Log Scale
    ax.set_yscale('log')
    
    # 1. MAJOR TICKS: Force standard numbers "10, 100" (Scalar)
    major_formatter = ScalarFormatter()
    major_formatter.set_scientific(False)
    ax.yaxis.set_major_formatter(major_formatter)

    # 2. MINOR TICKS: Show only '2' and '5' (e.g., 20, 50, 200) to declutter
    def custom_minor_formatter(x, pos):
        # Get the leading digit (e.g., for 300, digit is 3)
        if x <= 0: return ""
        s = str(int(x))
        if s[0] in ['2', '4', '6']: 
            return s
        return "" # Hide 3, 4, 6, 7, 8, 9

    ax.yaxis.set_minor_formatter(FuncFormatter(custom_minor_formatter))
    
    # 3. ENABLE GRID LINES 
    # Major grid (solid, slightly darker)
    ax.grid(visible=True, which='major', axis ='y', color='0.8', linestyle='-', linewidth=0.8)
    
    # Minor grid (dashed, lighter, targeting the 20, 30, 40... marks)
    ax.grid(visible=True, which='minor', color='0.9', linestyle='-', linewidth=0.5)

    # Labels
    ax.set_title('Pore Diameter Distribution by Recipe (Assumes cone half angle = 2°)', fontsize=16, pad=20)
    ax.set_xlabel('Recipe Configuration', fontsize=12, fontweight='bold')
    ax.set_ylabel('Predicted Pore Diameter (nm)', fontsize=12, fontweight='bold')

    # Add N= counts
    counts = df['Recipe Label'].value_counts()
    for i, label in enumerate(sorted_labels):
        count = counts[label]
        # For log scale, placing text is tricky. We place it slightly above the max value.
        group_data = df[df['Recipe Label']==label]
        if not group_data.empty:
             max_val = group_data['Predicted Diameter (nm)'].max()
             # Multiply by 1.2 to move it up visually on a log scale
             ax.text(i, max_val * 1.1, f'n={count}', 
                      ha='center', va='bottom', fontsize=9, fontweight='bold')

    # D. Legend & Table Positioning
    # Move Legend to top right, outside the plot
    legend = ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', title='Batch Date', borderaxespad=0)
    
    # Add The Recipe Table below the legend
    # We define columns: Label, Heat, Pull, Vel, Delay
    col_labels = ["Label", "Heat", "Pull", "Vel", "Delay"]
    
    # Create the table
    the_table = plt.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc='center',
        loc='right',
        # bbox = [x, y, width, height] relative to axes
        # x=1.02 (aligned with legend), y=0.0 (bottom), width=0.4, height=0.5 (half height)
        bbox=[1.02, 0.15, 0.45, 0.5] 
    )
    
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(9)
    the_table.scale(1, 1.5) # Add some padding to cells

    # Adjust layout to accommodate the extra elements on the right
    plt.subplots_adjust(right=0.65) # Leave 35% of space on the right for legend/table

    # 4. Save
    plt.savefig(OUTPUT_PDF, dpi=300, bbox_inches='tight') # bbox_inches='tight' ensures nothing gets cut off
    print(f"Plot saved to: {OUTPUT_PDF}")
    plt.show()

if __name__ == "__main__":
    main()