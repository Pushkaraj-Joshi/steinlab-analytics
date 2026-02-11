# -*- coding: utf-8 -*-
"""
Created on Tue Feb 10 23:58:27 2026

@author: pjoshi11
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import string

# ================= CONFIGURATION =================
# Update this path if necessary to match your computer
BASE_DIR = r'H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Tip conductance'
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
    
    # Filter out rows where Diameter is N/A or missing
    df = df.dropna(subset=['Predicted Diameter (nm)'])
    df = df[df['Predicted Diameter (nm)'] != 'N/A']
    
    # Ensure numerical columns are actually numbers
    numeric_cols = ['Predicted Diameter (nm)', 'Heat', 'Pull', 'Velocity', 'Delay']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where critical recipe data is missing
    df = df.dropna(subset=['Heat', 'Pull', 'Velocity', 'Delay', 'Predicted Diameter (nm)'])

    print(f"Loaded {len(df)} valid data points.")

    # 2. Categorize Recipes (Task 1)
    # create a new column combining all 4 parameters
    recipe_cols = ['Heat', 'Pull', 'Velocity', 'Delay']
    
    # Get unique combinations
    unique_recipes = df[recipe_cols].drop_duplicates().sort_values(by=recipe_cols)
    
    # Assign Labels (A, B, C...)
    # We use a generator to create A, B, ... Z, AA, AB, etc. if needed
    def label_generator():
        for i in range(100): # excessive limit
            yield string.ascii_uppercase[i]
            
    label_gen = label_generator()
    recipe_map = {}
    
    # Create the mapping dictionary
    for index, row in unique_recipes.iterrows():
        label = next(label_gen)
        # Create a tuple of the parameters to use as a dictionary key
        combo = tuple(row[col] for col in recipe_cols)
        recipe_map[combo] = label

    # Apply the mapping to the main dataframe
    df['Recipe Label'] = df.apply(
        lambda x: recipe_map[tuple(x[col] for col in recipe_cols)], axis=1
    )

    # 3. Save the Recipe Key (Output Requirement)
    key_data = []
    for combo, label in recipe_map.items():
        key_data.append({
            'Label': label,
            'Heat': combo[0],
            'Pull': combo[1],
            'Velocity': combo[2],
            'Delay': combo[3]
        })
    
    key_df = pd.DataFrame(key_data)
    key_df.to_csv(OUTPUT_KEY_CSV, index=False)
    print(f"Recipe Key saved to: {OUTPUT_KEY_CSV}")

    # 4. Generate Visualization (Task 2)
    # Set the aesthetic style
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))

    # A. Violin Plot (Distribution)
    ax = sns.violinplot(
        data=df, 
        x='Recipe Label', 
        y='Predicted Diameter (nm)',
        inner=None,          # Hide inner boxplot (too cluttered with swarm)
        color="0.9",         # Light grey background color
        linewidth=1,
        cut=0                # Don't extend past data range
    )

    # B. Swarm Plot (Individual Points)
    # We color by 'Preparation Date' to show batch effects
    sns.stripplot(
        data=df, 
        x='Recipe Label', 
        y='Predicted Diameter (nm)',
        hue='Preparation Date', # Color by Batch/Date
        dodge=False,            # Don't split points by hue group on x-axis
        jitter=True,            # Add random noise to X position
        size=6,
        alpha=0.8,
        palette="viridis",      # Nice color map
        ax=ax
    )

    # Move legend outside if it's too big
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Batch Date')

    # Labels and Title
    plt.title('Pore Diameter Distribution by Recipe\n(Color indicates Fabrication Batch)', fontsize=14)
    plt.xlabel('Recipe Configuration (See Key)', fontsize=12)
    plt.ylabel('Predicted Pore Diameter (nm)', fontsize=12)
    
    # Add the "N=" count above each violin
    counts = df['Recipe Label'].value_counts().sort_index()
    for i, label in enumerate(sorted(df['Recipe Label'].unique())):
        count = counts[label]
        # Position text slightly above the max value for that group
        max_val = df[df['Recipe Label']==label]['Predicted Diameter (nm)'].max()
        plt.text(i, max_val + (max_val*0.05), f'n={count}', 
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()

    # 5. Save Output
    plt.savefig(OUTPUT_PDF, dpi=300)
    print(f"Plot saved to: {OUTPUT_PDF}")
    # plt.show() # Uncomment if running in Jupyter/IDE to see it immediately

if __name__ == "__main__":
    main()