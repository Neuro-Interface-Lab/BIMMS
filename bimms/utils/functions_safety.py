"""
	Python library to use BIMMS measurement setup - STM32 constants
	Authors: Florian Kolbl / Louis Regnacq / Thomas Couppey
	(c) ETIS - University Cergy-Pontoise
		IMS - University of Bordeaux
		CNRS

	Requires:
		Python 3.6 or higher
"""
import numpy as np


#############################
## miscalleneous functions ##
#############################
def convert(int32_val):
    bin = np.binary_repr(int32_val, width=32)
    # int8_arr = [int(bin[24:32],2), int(bin[16:24],2), int(bin[8:16],2), int(bin[0:8],2)] 	# LSBs First
    int8_arr = [
        int(bin[0:8], 2),
        int(bin[8:16], 2),
        int(bin[16:24], 2),
        int(bin[24:32], 2),
    ]  # MSBs First
    return int8_arr

#Return true if val is in range else false
def in_range(val,range):
    if (np.abs(val)>range):
        return(False)
    return(True)

def in_range_min_max(val,min,max):
    if (val < min) or (val>max):
        return(False)
    else:
        return(True)

#return true if val is close to expected (tol in %) else return false
def in_tol(val,expected,tol):
    tol = tol/100
    max_val = expected *(1+tol)
    min_val = expected *(1-tol)
    if (val < min_val) or (val>max_val):
        return(False)
    else:
        return(True)


def ComputeSplitFit(coef_list, freq_lim, freq):
    Nsplit = len(freq_lim)
    data_arr = []
    data = []
    freq_list_array = []
    if Nsplit == 1:
        data_poly = np.poly1d(coef_list[0])
        data = data_poly(freq)
    else:
        for idx in range(Nsplit):
            if idx == 0:
                x = np.where(freq <= freq_lim[idx])
            else:
                x = np.where((freq <= freq_lim[idx]) & (freq > freq_lim[idx - 1]))
            if x:
                freq_split = freq[x]
                data_poly = np.poly1d(coef_list[idx])
                data = np.concatenate((data, data_poly(freq_split)), axis=0)
                freq_list_array = np.concatenate((freq_list_array, freq_split), axis=0)
        data = np.interp(freq, freq_list_array, data)
    return data


def unwrap_phase(phase):
    for x in range(len(phase)):
        if phase[x] > 180:
            phase[x] = 360 - phase[x]
            # print(open_cal_phase[x])
        if phase[x] < 0:
            phase[x] = -(phase[x])
    return -phase
