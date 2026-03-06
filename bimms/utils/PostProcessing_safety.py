"""
    Python library to use BIMMS measurement setup - Post Processing 
    Authors: Florian Kolbl / Louis Regnacq
    (c) ETIS - University Cergy-Pontoise
        IMS - University of Bordeaux
        CNRS

    Requires:
        Python 3.6 or higher

"""
import andi as ai
import numpy as np
import json
from scipy.signal import savgol_filter

def SplitFit(N_fit,freq,data,polyOrder):
    SizeN = int(len(freq)/N_fit)
    if (N_fit==1):
        coef_list = [np.polyfit(freq, data, polyOrder)]
        freq_lim = [0]
    else:
        coef_list = []
        freq_lim = []
        for idx in range (N_fit):
            idx_min = SizeN*idx
            if (idx == N_fit):
                idx_max = SizeN*(idx+1)-1
            else:
                idx_max = SizeN*(idx+1)
            freq_split = freq[idx_min:idx_max]
            data_split = data[idx_min:idx_max]

            if type(polyOrder) is list:
                coef_split = np.polyfit(freq_split, data_split, polyOrder[idx])
            else:
                coef_split = np.polyfit(freq_split, data_split, polyOrder)

            coef_list.append(coef_split)
            freq_lim.append(freq_split[-1])
    return(coef_list,freq_lim)

def ComputeSplitFit(coef_list,freq_lim,freq):
    Nsplit = len(freq_lim)
    data_arr = []
    data = []
    freq_list_array = []
    if (Nsplit == 1):
        data_poly = np.poly1d(coef_list[0])
        data = data_poly(freq)
    else:
        for idx in range (Nsplit):
            if (idx==0):
                x = np.where(freq<=freq_lim[idx])
            else:
                x = np.where((freq<=freq_lim[idx]) & (freq>freq_lim[idx-1]))
            if (x):
                freq_split = freq[x]
                data_poly = np.poly1d(coef_list[idx])
                data = np.concatenate((data,data_poly(freq_split)),axis =0)
                freq_list_array = np.concatenate((freq_list_array,freq_split),axis =0)
        data = np.interp(freq, freq_list_array, data)
    return(data)

def unwrap_phase(phase):
    for x in range (len(phase)):
        if phase[x]>180:
            phase[x] = 360-phase[x]
            #print(open_cal_phase[x])
        if phase[x]<0:
            phase[x] = -(phase[x])
    return(-phase)

