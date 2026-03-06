"""Generic numerical helper functions for BIMMS.

This module provides small utility routines used in several low-level and
post-processing operations, including integer-to-byte conversion, range and
tolerance checks, evaluation of piecewise polynomial fits, and normalization of
phase data.
"""
import numpy as np


#############################
## miscalleneous functions ##
#############################
def convert(int32_val):
    """Convert a 32-bit integer into a list of four 8-bit values.

    The output ordering follows the original implementation and corresponds to
    most-significant byte first.

    Parameters
    ----------
    int32_val : int
        Integer value encoded over 32 bits.

    Returns
    -------
    list of int
        Four-element list containing the byte-wise representation of the input
        integer.
    """
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
    """Test whether the absolute value of a quantity is below a limit.

    Parameters
    ----------
    val : float or array-like
        Value to test.
    range : float
        Symmetric admissible bound around zero.

    Returns
    -------
    bool
        ``True`` when ``abs(val) <= range``, otherwise ``False``.
    """
    if (np.abs(val)>range):
        return(False)
    return(True)

def in_range_min_max(val,min,max):
    """Test whether a value belongs to a closed interval.

    Parameters
    ----------
    val : float
        Value to test.
    min : float
        Lower admissible bound.
    max : float
        Upper admissible bound.

    Returns
    -------
    bool
        ``True`` when ``min <= val <= max``, otherwise ``False``.
    """
    if (val < min) or (val>max):
        return(False)
    else:
        return(True)

#return true if val is close to expected (tol in %) else return false
def in_tol(val,expected,tol):
    """Test whether a value remains within a relative tolerance band.

    Parameters
    ----------
    val : float
        Measured or estimated value.
    expected : float
        Reference value.
    tol : float
        Relative tolerance expressed in percent.

    Returns
    -------
    bool
        ``True`` when ``val`` lies inside the interval defined by
        ``expected ± tol%``, otherwise ``False``.
    """
    tol = tol/100
    max_val = expected *(1+tol)
    min_val = expected *(1-tol)
    if (val < min_val) or (val>max_val):
        return(False)
    else:
        return(True)


def ComputeSplitFit(coef_list, freq_lim, freq):
    """Evaluate a piecewise polynomial fit over a frequency vector.

    Parameters
    ----------
    coef_list : list of array-like
        Polynomial coefficients for each frequency segment, as returned by
        :func:`numpy.polyfit`.
    freq_lim : list or array-like
        Upper frequency limit associated with each polynomial segment.
    freq : array-like
        Frequencies at which the fit is evaluated.

    Returns
    -------
    numpy.ndarray
        Interpolated values of the piecewise polynomial fit evaluated on
        ``freq``.
    """
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
    """Map phase values to a negative wrapped representation.

    The routine mirrors phase values above 180 degrees and converts negative
    values to their absolute magnitude before returning the negated array.

    Parameters
    ----------
    phase : array-like
        Phase values, typically expressed in degrees.

    Returns
    -------
    array-like
        Phase vector modified in place and returned with negative sign.
    """
    for x in range(len(phase)):
        if phase[x] > 180:
            phase[x] = 360 - phase[x]
            # print(open_cal_phase[x])
        if phase[x] < 0:
            phase[x] = -(phase[x])
    return -phase
