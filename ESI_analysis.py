# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: pjoshi11

This is a temporary script file.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob 
import os
import shutil


def findMarkers(V, dV, thresh, dt):
    markers = []
    i=0
    while i < len(V)-50:
        if np.abs(np.mean(V[i:i+50])-np.mean(V[i-50:i])) > dV*thresh:
            markers.append(i+1)
            i+=dt*70
        i+=25
    # print(markers)

    markers = np.array(markers)
    
    markArray = np.zeros(len(V))
    markArray[markers] = 500
    
    return markers, markArray

def getMeansStds(V, I, markers, i_skips):
    ''' This code finds the mean and std of the voltages and currents at each step'''
    ''' It also separates the markers into upward and downward steps'''

    Vsteps_mean = np.zeros(len(markers))
    Isteps_mean = np.zeros(len(markers))
    Vsteps_std = np.zeros(len(markers))
    Isteps_std = np.zeros(len(markers))
    
    markers_up = []
    markers_down = []

    for j in range(len(markers)-1):
        Vsteps_mean[j] = np.mean(V[markers[j]+i_skips:markers[j+1]-i_skips])
        Vsteps_std[j] = np.std(V[markers[j]+i_skips:markers[j+1]-i_skips])
        Isteps_mean[j] = np.mean(I[markers[j]+i_skips:markers[j+1]-i_skips])
        Isteps_std[j] = np.std(I[markers[j]+i_skips:markers[j+1]-i_skips])
        if Vsteps_mean[j]-Vsteps_mean[j-1] > 0:
            markers_up.append(j)
        elif Vsteps_mean[j]-Vsteps_mean[j-1] < 0:
            markers_down.append(j)

    ''' Finds which markers mark turning points '''

    up_to_down = []
    
    for i in range(len(markers)-1):
        if i in markers_up and i+1 in markers_down:
            up_to_down.append(i)
    
    return Vsteps_mean, Vsteps_std, Isteps_mean, Isteps_std, up_to_down

def read_IV(path, dV):
    data = pd.read_csv(path, header = 21, delimiter = '\t')
    V = data['Measured Voltage']
    I = data['Current']*1e12
    t = np.linspace(0,len(V)/100, len(V))
    
    m, mA = findMarkers(V, dV = dV, thresh = 0.2 , dt = 3)
    Vsteps_mean, Vsteps_std, Isteps_mean, Isteps_std, up_to_down = getMeansStds(V, I, m, i_skips = 100)
    return t,I,V, [Vsteps_mean, Vsteps_std, Isteps_mean, Isteps_std, up_to_down]

def read_log(path):
    logpath = path[0:-4] + ' log.lvm'
    logdata = pd.read_csv(logpath, header = 21, delimiter = '\t')
    return logdata

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Base directory for your files
base_dir = r"H:\Shared drives\Stein Lab Team Drive\Pushkaraj\ESI characterization\Dec_02_2025\Tip_05"

# Using glob to find files matching a pattern

all_files = glob.glob(os.path.join(base_dir, "*automatic_loop_*.lvm"))

# Filter out files that contain "log.lvm"
file_paths = [f for f in all_files if "log.lvm" not in os.path.basename(f)]

# Sort the file paths to ensure consistent processing order
file_paths.sort()

# Initialize a list to store the processed data for each file
processed_data = []




for path in file_paths:
    
    logdata = read_log(path)
    t, I, V, steps = read_IV(path, dV=logdata['dV (V)'][0])
    i = np.argmax(np.abs(steps[0]))
    
    # Store the results in a dictionary and append to the list
    processed_data.append({
        'path': path,
        't': t,
        'I': I,
        'V': V,
        'steps': steps,
        'i': i
    })
    
    
#~~~ Plot the data    
fig, ax = plt.subplots(figsize=[7, 5.5])

# Define a list of colors or markers to differentiate the lines, if desired.
# For simplicity, we'll use default colors here.
# If you have many loops, consider using a colormap for more distinct colors.

for idx, data_entry in enumerate(processed_data):
    steps = data_entry['steps']
    i = data_entry['i']
    loop_number = idx + 1 # Use a descriptive loop number for the label

    # Extract the relevant parts of the steps arrays for plotting
    x_data = -steps[0][i:-2]  # Voltage
    y_data = steps[2][i:-2] # Current
    x_error = steps[3][i:-2] # x-error (e.g., dv)
    y_error = steps[1][i:-2] # y-error (e.g., di)

    ax.errorbar(x_data, y_data, x_error, y_error,
                fmt=':o', linewidth=1, markersize=3, capsize=2,
                label=f'loop {loop_number}')
if processed_data:
    # Assuming 'logdata' is the same for all files or you want to use the first one
    # You might need to adjust how logdata is stored or passed if it changes per file.
    logdata = read_log(processed_data[0]['path']) # Re-read log for threshold current or store it
    ax.plot(np.linspace(100, 500, 100), np.ones(100) * logdata['Threshold Current (A)'][0] * 1e12,
            ':', color='k', label='threshold current')
else:
    print("No data processed to plot the threshold current.")
    
    
ax.set_xlabel('Voltage (V)', fontsize=16)
ax.set_ylabel('Current (pA)', fontsize=16)
ax.tick_params(labelsize=14, direction='in')
ax.legend(fontsize=14)
    

# Set the limits if necessary (uncomment and adjust as needed)
#ax.set_ylim(-0.1,40)
#ax.set_xlim(200,520)

# Construct the output PDF file path
output_pdf_path = os.path.join(base_dir, "combined_loops_plot.pdf")

# Save the figure as a PDF
plt.savefig(output_pdf_path, bbox_inches="tight") # {Link: according to Stack Overflow https://stackoverflow.com/questions/79306481/how-can-i-save-a-figure-to-pdf-with-a-specific-page-size-and-padding}  Saving a plot with `bbox_inches=\"tight\"` can ensure that the entire figure, including labels and legends, fits within the PDF bounds.
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

plt.show() # Display the plot

print(f"Plot saved to: {output_pdf_path}")
