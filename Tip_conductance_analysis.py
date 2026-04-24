# -*- coding: utf-8 -*-
"""
Created on Tue Jul 29 11:02:17 2025

@author: pjoshi11
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import matplotlib.ticker as ticker # Import ticker for EngFormatter
from si_prefix import si_format
import shutil
import math

def calculate_pore_diameter(pore_resistance, solution_conductivity, half_cone_angle):
    """
    Calculates the pore diameter based on equation in "Characterization of Nanopipette, Anal.Chem(2016), Perry et.al."

    """

    # Ensure valid inputs (avoid division by zero or negative values where not physically meaningful)
    if pore_resistance == 0 or solution_conductivity == 0:
        raise ValueError("Resistance and conductivity cannot be zero.")

    # Convert the angle (2.5) to radians for the tan function
    angle_in_radians = math.radians(half_cone_angle)  #  degrees to radians

    # Implement the given formula
    pore_dia = (1 / pore_resistance) * (1 / solution_conductivity) * (1 / (math.pi * math.tan(angle_in_radians)) + 0.25)

    return pore_dia


#~~~ Provide the base folder where data files are stored

base_dir = r'H:\Shared drives\Stein Lab Team Drive\Hannah\I-V_measurement\Apr_23_2026\Tip_02'

#~~ Entet solution conductivity in S/m
solution_conductivity = 2.96e-3/1e-2

#-- Enter the half cone angle in degree
half_cone_angle = 2


# --- Read and process data from multiple CSV files ---
csv_files = glob.glob(os.path.join(base_dir, "*.csv"))

all_voltages = []
all_currents = []


## Default fallback filename
output_csv_filename = "averaged_IV_data.csv" 

# Check if there are any CSV files to process
if csv_files:
    # Get the base filename (without path) of the first CSV file in the list
    first_csv_filename_base = os.path.basename(csv_files[0])
    
    # Get the filename without the .csv extension (first element of the tuple)
    filename_without_ext = os.path.splitext(first_csv_filename_base)
    
    # Find the index of the last underscore
    last_underscore_index = filename_without_ext[0].rfind('_')
    
    if last_underscore_index != -1: # Ensure an underscore was found
        # Extract the part before the last underscore
        main_part_of_filename = filename_without_ext[0][:last_underscore_index]
    else:
        # If no underscore, use the filename without extension as is
        main_part_of_filename = filename_without_ext

    output_csv_filename = f"averaged_{main_part_of_filename}.csv"
else:
    print("Warning: No CSV files found. Using default output filename.")
    
# Define the analysis subfolder path
analysis_folder = os.path.join(base_dir, 'Analysis')

# Create the analysis folder if it doesn't exist
if not os.path.exists(analysis_folder):
    os.makedirs(analysis_folder) # Use makedirs to create intermediate directories if needed
    
    
output_csv_path = os.path.join(analysis_folder, output_csv_filename) 

#-- Read the data --

for file_path in csv_files:
    
    df = pd.read_csv(file_path, skiprows=3, usecols=[0,1], names=['Voltage', 'Current'])

    all_voltages.append(df['Voltage'].values)
    all_currents.append(df['Current'].values)
           
    
    
# --- Average the I-V plots and calculate standard deviation ---

if len(set(len(v) for v in all_voltages)) != 1:
    print("Warning: IV curves have different lengths. Averaging might be inaccurate.")

average_voltage = np.mean(all_voltages, axis=0)
average_current = np.mean(all_currents, axis=0)

# Calculate the standard deviation of the current at each voltage point
std_current = np.std(all_currents, axis=0)

# --- Export averaged data to CSV ---
# Create a Pandas DataFrame from the NumPy arrays
averaged_data_df = pd.DataFrame({
    'Average Voltage (V)': average_voltage,
    'Average Current (A)': average_current,
    'Current Std Dev (A)': std_current
})


# Export the DataFrame to a CSV file
# index=False prevents writing the DataFrame index as a column in the CSV
averaged_data_df.to_csv(output_csv_path, index=False)


# --- Calculate Resistance centered around 0V ---

# Filtering by voltage range (-0.2V to 0.2V)
voltage_min = -0.2
voltage_max = 0.2


#~~ Converrt current in (nA) units
indices_in_range = np.where((average_voltage >= voltage_min) & (average_voltage <= voltage_max))
voltage_for_fit_range = average_voltage[indices_in_range]
current_for_fit_range = average_current[indices_in_range]*1e9 # Current in nA

# Fit a line to the data in the specified range (Voltage vs Current)
# The result `m_range, b_range` are the slope and intercept
m_range, b_range = np.polyfit(voltage_for_fit_range, current_for_fit_range, 1)

# The slope of the I-V curve (I vs V) is 1/R. So, R = 1/slope.
resistance_from_slope_range = (1 / m_range)*1e9 # Adjust for current in nA

formatted_resistance = si_format(resistance_from_slope_range, precision=2)



#---- Predict the pore diameter based on the Resitance of pore

pore_dia = calculate_pore_diameter(resistance_from_slope_range, solution_conductivity, half_cone_angle)
formatted_pore_dia = si_format(pore_dia, precision=0) 

# --- Plot the I-V curve with the fitted lines ---
fig, ax = plt.subplots(figsize=(8, 6)) # Create figure and axes objects for better control

# Plot the averaged data with error bars with current in nA units
ax.errorbar(average_voltage, average_current*1e9, yerr=std_current*1e9, fmt='o',
            markerfacecolor='none',  # Makes the marker hollow/transparent
            markeredgecolor='red',  # Sets the color of the marker's edge (e.g., to match the line)
            capsize=3, label='Averaged IV Data')

# Plot the fitted line for the voltage range
ax.plot(average_voltage, m_range * average_voltage + b_range, 'k--',
         label=f' Linear Fit,\n Pore Resistance = {formatted_resistance} $\Omega$ \n Predicted pore diameter = {formatted_pore_dia}m ')

ax.set_title('Averaged I-V Curve with Linear Fit (-0.2V to 0.2V)',fontsize= 16)
ax.set_xlabel('Voltage (V)',fontsize= 14)
ax.set_ylabel('Current (nA)', fontsize= 14) # We will let the formatter handle the units here
ax.tick_params(axis = 'both', labelsize = 12, direction = 'in')


ax.legend()
ax.grid(True) # Remove the grid 



# Construct the output PDF file path
output_pdf_path = os.path.join(analysis_folder,  f"averaged_{main_part_of_filename}.pdf")

# Save the figure as a PDF
plt.savefig(output_pdf_path, bbox_inches="tight")

plt.show()

#---- Store a copy of the analysis script in the base folder
# Get the path of the current Python script
current_script_path = os.path.abspath(__file__)

# Construct the destination path for the copied script
script_copy_path = os.path.join(base_dir, os.path.basename(current_script_path))

# Copy the current Python script to the base directory
try:
    shutil.copyfile(current_script_path, script_copy_path)
    print(f"Copied current script to: {script_copy_path}")
except shutil.SameFileError:
    print("The script is already in the target directory, skipping copy.")
except Exception as e:
    print(f"Error copying script: {e}")

plt.close(fig)

print(f"Plot saved to: {output_pdf_path}")
