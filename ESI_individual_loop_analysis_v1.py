# -*- coding: utf-8 -*-
"""
Spyder Editor

@author: pjoshi11


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
    print(len(markers))

    markers = np.array(markers)
    
    markArray = np.zeros(len(V))
    if len(markers)> 0:
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
        
        if Vsteps_mean[j]-Vsteps_mean[j-1] < 0:  # changed the inequality
            markers_up.append(j)
        elif Vsteps_mean[j]-Vsteps_mean[j-1] > 0:  # changed the inequality
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
    
    #~~~ Filter noise in the V before finding the steps~~
    N = 20
    V_filtered =  np.convolve(V, np.ones(N)/N, mode='valid')
    
    m, mA = findMarkers(V_filtered, dV = dV, thresh = 0.2 , dt = 3)
    
    if len(m)>0:
    
        Vsteps_mean, Vsteps_std, Isteps_mean, Isteps_std, up_to_down = getMeansStds(V, I, m, i_skips = 100)
        return t,I,V, [Vsteps_mean, Vsteps_std, Isteps_mean, Isteps_std, up_to_down]
    else:
        print('Did not reach threshold current')
        return False

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
    
    #~~ Read Tip ID~~
    file_name = os.path.basename(path)
    keyword = "_automatic_loop"
    if keyword in file_name:
        index = file_name.find(keyword)
        Tip_ID = file_name[:index]
    
    logdata = read_log(path)
    
    IV_data = read_IV(path, dV=logdata['dV (V)'][0])
    
    if IV_data:
        t, I, V, steps = IV_data
        i = np.argmax(np.abs(steps[0]))
        thresh_I = logdata['Threshold Current (A)'][0]
           
        # Store the results in a dictionary and append to the list
        processed_data.append({
            'path': path,
            't': t,
            'I': I,
            'V': V,
            'steps': steps,
            'i': i,
            'Threshold Current (A)': thresh_I
        })

    
#~~~ Plot the data    


for idx, data_entry in enumerate(processed_data):
    
    I = data_entry['I']
    V = data_entry['V'] 
    t = data_entry['t']
    loop_number = idx + 1 # Use a descriptive loop number for the label
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    fig_title = f'{Tip_ID} - Loop no. {loop_number}'
    plt.suptitle(fig_title, fontsize = 18)
    
    #~Plot the raw IV loop data
    # Smooth the V applied
    
    
    
    
    N = 20
    Vnew =  np.convolve(V, np.ones(N)/N, mode='valid')
    
    ax1.plot(t[N//2:-N//2+1],-Vnew, linewidth = 2)
    # ax.set_ylim(350,390)
    # ax1.set_xlim(0,650)
    ax1.set_xlabel('Time (s)', fontsize = 16)
    ax1.set_ylabel('Voltage (V)', fontsize = 16, color = 'tab:blue')
    ax1.tick_params(axis = 'both', labelsize = 14, direction = 'in')
    ax1.tick_params(labelcolor = 'tab:blue', axis = 'y')
    
    ax11=plt.twinx(ax1)
    
    ax11.plot(t,I, color = 'tab:red')
    # ax11.set_ylim(0,400)
    ax11.set_ylabel('Current (pA)', fontsize = 16, color = 'tab:red')
    ax11.tick_params(labelsize = 14, direction = 'in', labelcolor = 'tab:red', axis = 'y')
    # ax2.set_xlim(400,450)
    
    
    ax1.set_zorder(ax11.get_zorder()+1)
    ax1.set_frame_on(False)
   
    # Extract the relevant parts of the steps arrays for plotting
    
    steps = data_entry['steps']
    i = data_entry['i']
    threshold_current = data_entry['Threshold Current (A)']
    x_data_fwd = -steps[0][1:i]  # Voltage
    y_data_fwd = steps[2][1:i] # Current
    x_error_fwd = steps[3][1:i] # x-error (e.g., dv)
    y_error_fwd = steps[1][1:i] # y-error (e.g., di)
    
    # Get the min/max of Current data
    min_y = min(np.min(I), np.min(y_data_fwd))
    max_y = max(np.max(I), np.max(y_data_fwd))
    
    # Add a little padding to the limits
    padding = (max_y - min_y) * 0.1
    ax11.set_ylim(min_y - padding, max_y + padding)
    
    
    x_data_bck = -steps[0][i:-1]  # Voltage
    y_data_bck = steps[2][i:-1] # Current
    x_error_bck = steps[3][i:-1] # x-error (e.g., dv)
    y_error_bck = steps[1][i:-1] # y-error (e.g., di)


    ax2.errorbar(x_data_fwd, y_data_fwd, x_error_fwd, y_error_fwd,
                fmt=':o', color = 'red', linewidth=3, markersize=8, capsize=2,
                label='forward_loop')
    
    ax2.errorbar(x_data_bck, y_data_bck, x_error_bck, y_error_bck,
                fmt=':o', color = 'green', linewidth=3, markersize=8, capsize=2,
                label=' backward_loop')
    

    ax2.plot(np.linspace(min(-V), max(-V), 100), np.ones(100)*threshold_current*1e12,
            ':', color='k', label='threshold current')
   
    
    ax2.set_xlabel('Voltage (V)', fontsize=16)
    # ax2.set_ylabel('Current (pA)', fontsize=16, labelcolor = 'tab:red')
    ax2.tick_params(axis = 'y', labelsize=14, direction='in', labelcolor = 'tab:red')
    ax2.tick_params(axis = 'x', labelsize=14, direction='in')
    ax2.set_ylim(min_y - padding, max_y + padding)
    ax2.legend(fontsize=14)
    fig.tight_layout(w_pad=0.5, h_pad=1.0) # Adjust horizontal and vertical padding between subplots

    # Set the limits if necessary (uncomment and adjust as needed)
    #ax.set_ylim(-0.1,40)
    #ax.set_xlim(200,520)
    
    # Construct the output PDF file path
    output_pdf_path = os.path.join(base_dir, f"loop {loop_number}_plot.pdf")
    
    # Save the figure as a PDF
    plt.savefig(output_pdf_path, bbox_inches="tight")
    plt.show()

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

