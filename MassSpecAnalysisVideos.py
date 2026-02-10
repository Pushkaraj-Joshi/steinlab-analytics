# -*- coding: utf-8 -*-
"""
Created on Thu Aug 11 14:47:05 2022

@author: bpugn
"""

import msplot
from msplot import *
# import easygui
import os

s = Spectrum()
#s.load("C:\\Users\\ishma\\Dropbox (SteinLab)\\spectra\\(ID     186nm) 2016-07-26-tip15\\mass spec\\FEB 23 2017 16-51.cd","C:\\Users\\ishma\\Dropbox (SteinLab)\\spectra\\(ID     186nm) 2016-07-26-tip15\\ivpt\\ivpt1.tsv")

#path = easygui.diropenbox()

#path = r"C:\Users\William\Dropbox (SteinLab)\Will\Electrospray Research\Experiment\Mass Spectra\Ion Evap Vs Tip Size\currentnorm_metric_2\82nm"

# s.load(r"C:\Users\William\Dropbox (SteinLab)\Will\Electrospray Research\Experiment\Mass Spectra\2017-11-15 Calibration\2017-11-17_tip(20171117)\plot", onblast_cutoff = 150)


#path = easygui.diropenbox()
#s.load(path4
s.load(r'H:\Shared drives\Stein Lab Team Drive\Pushkaraj\Mass Spectrometry\Aug_01_2025\trial_2', onblast_cutoff = 0)


s.makeAnimation(
	window = 250,
	step = 250,
	scan_range = (0, None), 
	#scan_range = (19300, None), 
    mass_range = (20, 1000),
	out_name = "FullEmissionWithHeatMarkers4.mp4",
	normalization=SpecNorm.SCAN,
	#markers=[Marker("22.1C", 4848), Marker("40C", 5255), Marker("60C", 5706), Marker("80C", 6210), Marker("85C", 6440)], #Marker("1M NaI in formamide", 10000)],
    #markers=[Marker("52C", 4638), Marker("61C", 6538), Marker("L1 = 100V", 7538), Marker("71C", 9380), Marker("L1 = 90V", 10070), Marker("L1 = 70V", 11070), Marker("75C", 13079), Marker("L1 = 60V", 14090), Marker("82C", 15070), Marker("L1 = 70V", 16050), Marker("90C", 17720)], #Marker("1M NaI in formamide", 10000)],
    #markers=[Marker("50C", 9900), Marker("55C", 14000), Marker("L1 = 62C", 15360), Marker("70C", 16915)],
    #markers=[Marker("50C", 100), Marker("heat off", 5600), Marker("40C", 8890), Marker("37C", 10710), Marker("34C", 12000), Marker("30C", 15822), Marker("29C", 16273), Marker("27C", 19300)],
    #markers=[Marker("43C", 20390), Marker("50C", 22290), Marker("60C", 24427)],# Marker("37C", 10710), Marker("34C", 12000), Marker("30C", 15822), Marker("29C", 16273), Marker("27C", 19300)],
    markers=[Marker("Histidine/NaI pH 7.72", 6170), Marker("Turn heater on", 14070), Marker("55C", 16060), Marker("70C", 16527)],
    aux_plot_type=AuxPlots.DETECTOR_CURRENT,
	aux_plot_type_2=AuxPlots.L1_VOLTAGE,
	aux_smoothing=1,
	aux_smoothing_2=1,
	spec_smoothing=1.5,
	aux_range=(0,None),
	aux_range_2=(0,None),
	show_plot=False,
	frame_rate=6,
	font_size=16.5
	)


print("\a")




# def multiplot(start_scan,current,concentration):

# 	for x in range(1,10):
# 		s.plotSpectrum(
# 		mass_range = (150, None),
# 		window_range = (start_scan, (start_scan+x)),
# 		label_peaks = True,
# 		show_plot = False,
# 		out_name = current + "_" + concentration + "_" + str(start_scan) + "startscan_" + str(x) + "scans.png"
# 		)
# 	for x in range(10,91,10):
# 		s.plotSpectrum(
# 		mass_range = (150, None),
# 		window_range = (start_scan, (start_scan+x)),
# 		label_peaks = True,
# 		show_plot = False,
# 		out_name = current + "_" + concentration + "_" + str(start_scan) + "startscan_" + str(x) + "scans.png"
# 		)
# 	for x in range(100,2001,100):
# 		s.plotSpectrum(
# 		mass_range = (150, None),
# 		window_range = (start_scan, (start_scan+x)),
# 		label_peaks = True,
# 		show_plot = False,
# 		out_name = current + "_" + concentration + "_" + str(start_scan) + "startscan_" + str(x) + "scans.png"
# 		)
# 	print("\a")

# multiplot( 3000,  "80nA", "1M")

# s.plotSpectrum(
# 		mass_range = (None, 500),
# 		window_range = (3960, 5960),
# 		label_peaks = True,
# 		show_plot = False,
# 		out_name = "transition_3960to5960scans_0to500mz.png"
# 		)



# s.makeAnimation(
# 	window = 100,
# 	step = 100,
# 	scan_range = (None, None),
# 	mass_range = (None, None),
# 	out_name = "ratioandsource_100scan_s.mp4",
# 	normalization=SpecNorm.SCAN,
# 	markers=[Marker("500mM", 1)],
# 	aux_plot_type=AuxPlots.DETECTOR_SOURCE_RATIO,
# 	aux_plot_type_2=AuxPlots.SOURCE_CURRENT,
# 	aux_smoothing=10,
# 	aux_smoothing_2=1,
# 	aux_range=(0,None),
# 	aux_range_2=(0,None),
# 	show_plot=False
# 	)

# markers=[Marker("100mM", 1),Marker("200mM", 2610),Marker("600kPa", 30000),Marker("1050kPa", 32300)],
# normalization=SpecNorm.GLOBAL,
# aux_smoothing=20,
# aux_plot_type=AuxPlots.DETECTOR_SOURCE_RATIO,
# out_name = "detectorandsource_0.77nA_50mM_s.mp4",