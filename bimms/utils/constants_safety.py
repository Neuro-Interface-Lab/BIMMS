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

cmd_shift = 2**29
## Comannd values
nothing = 0x00
set_STM32_state = 0x01
set_relay = 0x02
read_register = 0x03

## STM32 STATE
STM32_stopped = 0x00
STM32_idle = 0x01
STM32_locked = 0x02
STM32_error = 0x03

## STM32 to AD2 SPI
STM32_CLK = 1e6
STM32_CLK_p = 1
STM32_MOSI_p = 2
STM32_MISO_p = 3
STM32_CS_p = 0


## IA Gain IOs
CH1_A0_0 = 8
CH1_A1_0 = 9
CH1_A0_1 = 10
CH1_A1_1 = 11

CH2_A0_0 = 12
CH2_A1_0 = 13
CH2_A0_1 = 14
CH2_A1_1 = 15

## LEDs IO
LED_err = 5
LED_status = 4

## Free IOs
IO6 = 6
IO7 = 7

## Relay mapping
Ch1Coupling_rly = 2**0
Chan1Scope1_rly = 2**1
Ch2Coupling_rly = 2**2
Chan2Scope2_rly = 2**3
DCFeedback_rly = 2**4
InternalAWG_rly = 2**5
TIANegIn1_rly = 2**6
TIANegIn2_rly = 2**7
TIA2Chan2_rly = 2**8
TIACoupling_rly = 2**9
EnPotentiostat_rly = 2**10
EnCurrentSource_rly = 2**11
GainCurrentSource_rly = 2**12
Potentiostat2StimPos_rly = 2**13
Ipos2StimPos_rly = 2**14
VoutPos2StimPos_rly = 2**15
Ineg2StimNeg_rly = 2**16
VoutNeg2StimNeg_rly = 2**17
TIA2StimNeg_rly = 2**18
GND2StimNeg_rly = 2**19
StimCoupling_rly = 2**20
StimNeg2VNeg_ryl = 2**21
StimPos2VPos_rly = 2**22

## Memory registers
ID_add = 0
state_add = 1
error_add = 2
relays_map_add = 3

## Gains
gain_array = np.array([1, 2, 4, 5, 10, 20, 25, 50, 100])
gain_IA1 = np.array([1, 2, 2, 5, 5, 10, 5, 10, 10])
gain_IA2 = np.array([1, 1, 2, 1, 2, 2, 5, 5, 10])

## Channels
VRO_channel = 1
IRO_channel = 2

## BIMMS Board/serial-numbers dictionary

BimmsSerialNumbers = {1: 'SN:210321B28CCD',\
                    2: '',\
                    3: 'SN:210321B2825B',\
                    4: 'SN:210321B28C03',\
                    5: 'SN:210321B281BF',\
                    6: '',\
                    7: '',\
                    8: 'SN:210321B2825D',\
                    9: 'SN:210321B28CEB'}

#AD2 constants
AD2_AWG_ch = 0      #AWG connected to AD2 AWG CH1
AD2_VRO_ch = 0      #Voltage readout connected to AD2 scope CH1
AD2_IRO_ch = 1     #Current readout connected to AD2 scope CH2


#Default Analog Gains
VCVS_SE_G_default = 1.1                                          #Default Voltage source gain (Single-Ended)
VCVS_DIFF_G_default = 2.2                                        #Default Voltage source gain (Differential)
VCCS_LowR_max = 51000                                            #Maximum Rg in Low Gain mode (G current source = 1/Rg)
VCCS_LowR_min = 1000                                             #Minimum Rg in Low Gain mode 
VCCS_LowR_default = (VCCS_LowR_max+VCCS_LowR_min)/2        #Default Rg value in Low gain mode
VCCS_HighR_max = 94000                                           #Maximum Rg in High Gain mode 
VCCS_HighR_min = 47000                                           #Minimum Rg in High Gain mode 
VCCS_HighR_default = (VCCS_HighR_max+VCCS_HighR_min)/2     #Default Rg value in High gain mode

VCCS_default_HG = VCVS_DIFF_G_default*1e6/VCCS_LowR_default   #gain in uA/V
VCCS_default_LG = VCVS_DIFF_G_default*1e6/VCCS_HighR_default  #gain in uA/V
VCVS_gain_tol = 10              #gain tolerance in %

VCCS_min_LG = VCVS_DIFF_G_default*1e6/VCCS_HighR_max           #gain in uA/V
VCCS_max_LG = VCVS_DIFF_G_default*1e6/VCCS_HighR_min           #gain in uA/V
VCCS_min_HG = VCVS_DIFF_G_default*1e6/VCCS_LowR_max            #gain in uA/V
VCCS_max_HG = VCVS_DIFF_G_default*1e6/VCCS_LowR_min            #gain in uA/V

VCCS_min_LG = VCCS_min_LG*(1-VCVS_gain_tol/100)
VCCS_max_LG = VCCS_max_LG*(1+VCVS_gain_tol/100)
VCCS_min_HG = VCCS_min_HG*(1-VCVS_gain_tol/100)
VCCS_max_HG = VCCS_max_HG*(1+VCVS_gain_tol/100)


TIA_gain_default = 100                                                 #Default TIA gain
TIA_gain_tol = 10                               #TIA GAIN tolerance in %


#Max/Min excitation current and voltage
max_current = float(1e3)       # uA
min_current = 0.         # uA
default_current = 1e2   # uA
max_voltage = float(1e3)       # mV
min_voltage = 0.         # mV
default_voltage = 1e2   # mV

#Default compensation offsets
VCCS_LowR_SE_offset_default = 0
VCCS_LowR_DIFF_offset_default = 0
VCCS_HighR_SE_offset_default = 0
VCCS_HighR_DIFF_offset_default = 0
VCVS_SE_offset_default = 0
VCVS_DIFF_offset_default = 0

#Max/min Voltage and Current readout values
max_current_readout = 1
min_current_readout = 0
max_voltage_readout = 1
min_voltage_readout = 0

#Self-test constants
max_IA_DC_offset = 5e-3     #Max DC IA offset (in V)
max_IA_AC_offset = 50e-3     #Max AC IA offset (in V)
IA_gain_DC_tol = 1             #IA gain DC tolerance (in %)
IA_gain_AC_tol = 75             #IA gain AC tolerance (in %) 

max_VCVS_SE_DC_offset = 50e-3   #Max DC-SE voltage source offset (in V)
max_VCVS_SE_AC_offset = 50e-3   #Max AC-SE voltage source offset (in V)
max_VCVS_DIFF_DC_offset = 50e-3   #Max DC-DIFF voltage source offset (in V)
max_VCVS_DIFF_AC_offset = 50e-3   #Max AC-DIFF voltage source offset (in V)

VCVS_SE_DC_gain_tol = 5
VCVS_SE_AC_gain_tol = 5
VCVS_DIFF_DC_gain_tol = 5
VCVS_DIFF_AC_gain_tol = 5

max_VCCS_SE_HG_DC_offset = 10   #Max HG-DC-SE current source offset (in µA)
max_VCCS_SE_HG_AC_offset = 10  #Max HG-DC-SE current source offset (in µA)
max_VCCS_DIFF_HG_DC_offset = 10   #Max HG-DC-SE current source offset (in µA)
max_VCCS_DIFF_HG_AC_offset = 10   #Max HG-DC-SE current source offset (in µA)
max_VCCS_SE_LG_DC_offset = 10   #Max LG-DC-SE current source offset (in µA)
max_VCCS_SE_LG_AC_offset = 10  #Max LG-DC-SE current source offset (in µA)
max_VCCS_DIFF_LG_DC_offset = 10   #Max LG-DC-SE current source offset (in µA)
max_VCCS_DIFF_LG_AC_offset = 10   #Max LG-DC-SE current source offset (in µA)

max_TIA_SE_DC_offset = 50e-3   #Max DC-SE TIA source offset (in V)
max_TIA_SE_AC_offset = 50e-3   #Max AC-SE TIA source offset (in V)
max_TIA_DIFF_DC_offset = 50e-3   #Max DC-DIFF TIA source offset (in V)
max_TIA_DIFF_AC_offset = 50e-3   #Max AC-DIFF TIA source offset (in V)

#Conversion units

V2mV = 1e-3
A2uA = 1e-6





#AD2 constants: 
min_AWG_amp = 0.0
max_AWG_amp = 5.0