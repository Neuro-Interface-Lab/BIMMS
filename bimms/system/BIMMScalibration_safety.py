"""
    Python library to use BIMMS measurement setup
    Authors: Florian Kolbl / Louis Regnacq
    (c) ETIS - University Cergy-Pontoise
        IMS - University of Bordeaux
        CNRS

    Requires:
        Python 3.6 or higher
        Analysis_Instrument - class handling Analog Discovery 2 (Digilent)

    Dev notes:
        - LR: in BIMMS_constants, IO15 change with IO7 because hardware issue.  
        - LR: TIA relay modified too

"""
import sys
import os
import faulthandler

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .BIMMSconfig import BIMMSconfig
from ..utils import constants as cst

### for debug
faulthandler.enable()
### verbosity of the verbosity
verbose = True

calibration_path = os.environ["BIMMS"] + "/_misc/calibrations/"

##############################
## CLASS FOR BIMMS HANDLING ##
##############################
class BIMMScalibration(BIMMSconfig):
    def __init__(self, bimms_id=None, serialnumber=None):
        super().__init__(bimms_id=bimms_id, serialnumber=serialnumber)
        self.awg_offset = None
        self.awg_amp = None
        self.awg_gain = None

        self.calibrated = False
        self.cal_awg_offset = None
        self.cal_awg_gain = None

    #####################################
    ## Excitation calibration methodes ##
    #####################################

    def check_calibration(self):
        self.calibrated = False

    def get_calibration(self):
        self.check_calibration()
        if self.calibrated:
            pass
        else:
            self.cal_awg_offset = None
            self.cal_awg_gain = None

    def validate_excitation_parameter(self):
        print("validate_excitation_parameter not implemented")
        pass

    def get_recording_gains(self):
        self.check_calibration()
        self.cal_ch1_gain = None
        self.cal_ch2_gain = None
        self.cal_TIA_gain = None
        if self.calibrated:
            pass
        else:
            self.get_default_ch1_gain()
            self.get_default_ch2_gain()
            self.get_default_TIA_gain()

    def get_default_ch2_gain(self):
        if (self.config_mode == "MEASURE"):
            self.cal_ch2_gain = int(self.config.IRO_gain)
        else:
            self.cal_ch2_gain = int(self.manual_config.CH2_gain)

    def get_default_ch1_gain(self):
        if (self.config_mode == "MEASURE"):
            self.cal_ch1_gain = int(self.config.VRO_gain)
        else:
            self.cal_ch1_gain = int(self.manual_config.CH1_gain)
    
    def get_default_TIA_gain(self):
        self.cal_TIA_gain = cst.TIA_gain_default

    def get_awg_parameters(self):
        """
        
        """
        self.get_calibration()
        unit = 1

        if (self.config_mode == "MEASURE"):
            if self.config.excitation_mode == "P_EIS":
                self.awg_amp = float(self.config.V_amplitude)
                unit = cst.V2mV
                if self.config.excitation_signaling_mode == "DIFF":
                    self.awg_offset = cst.VCVS_DIFF_G_default
                    self.awg_gain = 1 / cst.VCVS_DIFF_G_default
                else:   # SE
                    self.awg_offset = cst.VCVS_SE_offset_default
                    self.awg_gain = 1 / cst.VCVS_SE_G_default
            else: # P_EIS
                self.awg_amp = float(self.config.I_amplitude)
                unit = cst.A2uA
                if self.config.G_EIS_gain == "LOW":
                    self.awg_gain =  cst.VCCS_LowR_default / cst.VCVS_DIFF_G_default
                    if self.config.excitation_signaling_mode == "DIFF":
                        self.awg_offset = cst.VCCS_LowR_DIFF_offset_default
                    else: #SE
                        self.awg_offset = cst.VCCS_LowR_SE_offset_default
                else:   #HIGH
                    self.awg_gain = cst.VCCS_HighR_default / cst.VCVS_DIFF_G_default
                    if self.config.excitation_signaling_mode == "DIFF":
                        self.awg_offset = cst.VCCS_HighR_DIFF_offset_default
                    else: #SE
                        self.awg_offset = cst.VCCS_HighR_SE_offset_default

            if self.calibrated:
                self.awg_offset = self.cal_awg_offset
                self.awg_gain = self.cal_awg_gain
            self.awg_amp *= self.awg_gain * unit

        else:
            self.awg_amp = float(self.manual_config.AWG_amp)
            self.awg_offset =  float(self.manual_config.AWG_offset)
        #self.validate_excitation_parameter()


    #####################################
    ## Reccording calibration methodes ##
    #####################################

    def bode2impendance(self, *args):

        if (not(self.calibrated)):
            pass
        return args[:2]

    def Scope2calibration(self, *args):
        return args[:2]