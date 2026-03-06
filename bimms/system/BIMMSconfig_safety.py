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
import numpy as np
import os
from warnings import warn

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .BIMMShardware import BIMMShardware
from ..utils.config_mode import config_mode, config_range, config_mode_list
from ..utils import constants as cst


### for debug
faulthandler.enable()
### verbosity of the verbosity
verbose = True

###################################
## CLASS FOR BIMMS CONFIGURATION ##
###################################
class BIMMSconfig(BIMMShardware):
    def __init__(self, bimms_id=None, serialnumber=None):
        super().__init__(bimms_id=bimms_id, serialnumber=serialnumber)

        #self.set_STM32_idle()
        #self.set_STM32_stopped()

        self.config = config_mode_list()
        self.manual_config = config_mode_list()
        self.config_mode = config_mode("MEASURE" ,"MANUAL", default="MEASURE")

        ## Measuremenet
        self.config.add_mode("excitation_sources", config_mode("EXTERNAL" ,"INTERNAL", default="INTERNAL"))
        self.config.add_mode("excitation_mode",  config_mode("G_EIS", "P_EIS", default="P_EIS"))
        self.config.add_mode("wire_mode",  config_mode("2_WIRE", "4_WIRE", "2", "4",default="2_WIRE"))
        self.config.add_mode("excitation_signaling_mode", config_mode("SE", "DIFF", default="SE"))
        self.config.add_mode("excitation_coupling", config_mode("AC", "DC", default="DC"))
        self.config.add_mode("readout_coupling", config_mode("AC", "DC", default="DC"))
        self.config.add_mode("recording_mode",  config_mode("I", "V", "BOTH",default="BOTH"))
        self.config.add_mode("recording_signaling_mode", config_mode("SE", "DIFF", "AUTO", default="AUTO"))
        self.config.add_mode("DC_feedback", config_mode(True, False, default=False))

        # gains
        self.config.add_mode("G_EIS_gain", config_mode("LOW", "HIGH", "AUTO", default="AUTO"))
        self.config.add_mode("IRO_gain", config_mode(*cst.gain_array.tolist(), default=1))
        self.config.add_mode("VRO_gain", config_mode(*cst.gain_array.tolist(), default=1))
        
        # Signals
        self.config.add_mode("I_amplitude", config_range(cst.min_current, cst.max_current, default=cst.default_current))
        self.config.add_mode("V_amplitude", config_range(cst.min_voltage, cst.max_voltage, default=cst.default_voltage))

        # Other
        self.config.add_mode("config_settling", config_range(0, 100, default=0))

        #TEST CONFIG (Excitation)
        self.manual_config.add_mode("waveform_gen", config_mode("EXTERNAL" ,"INTERNAL", default="INTERNAL"))
        self.manual_config.add_mode("excitation_source",  config_mode("CURRENT", "VOLTAGE","NONE", default="NONE"))
        self.manual_config.add_mode("I_source_gain", config_mode("LOW", "HIGH", default="HIGH"))
        self.manual_config.add_mode("wire_mode",  config_mode("2_WIRE", "4_WIRE", "2", "4",default="2_WIRE"))
        self.manual_config.add_mode("excitation_signaling_mode", config_mode("SE", "DIFF", default="SE"))
        self.manual_config.add_mode("excitation_coupling", config_mode("AC", "DC", default="DC"))
        self.manual_config.add_mode("DC_feedback", config_mode(True, False, default=False))
        self.manual_config.add_mode("Enable_Isource", config_mode(True, False, default=True))
        self.manual_config.add_mode("AWG_amp", config_range(cst.min_AWG_amp, cst.max_AWG_amp, default=cst.min_AWG_amp))
        self.manual_config.add_mode("AWG_offset", config_range(cst.min_AWG_amp, cst.max_AWG_amp, default=cst.min_AWG_amp))

        #TEST CONFIG (Readout)
        self.manual_config.add_mode("CHx_to_Scopex", config_mode("CH1" ,"CH2","BOTH","NONE", default="NONE"))
        self.manual_config.add_mode("CH1_coupling", config_mode("AC", "DC", default="DC"))
        self.manual_config.add_mode("CH2_coupling", config_mode("AC", "DC", default="DC"))
        self.manual_config.add_mode("TIA_coupling", config_mode("AC", "DC", default="DC"))
        self.manual_config.add_mode("TIA_to_CH2", config_mode(True, False, default=False))
        self.manual_config.add_mode("connect_TIA", config_mode(True, False, default=False))
        self.manual_config.add_mode("TIA_NEG", config_mode("GND" ,"Vneg","Ineg", default="GND"))
        self.manual_config.add_mode("CH1_gain", config_mode(*cst.gain_array.tolist(), default=1))
        self.manual_config.add_mode("CH2_gain", config_mode(*cst.gain_array.tolist(), default=1))

    ####################
    ## Save and load  ##
    ####################
    def save_config(self, save=False, fname="bimms_config.json", blacklist=[], manual=False, **kwargs):
        """
        Save the bimms the configuration

        Parameters
        ----------
        save : bool, optional
            If True, save the BIMMS object in a json file
        fname : str, optional
            Name of the json file
        **kwargs : dict, optional
            Additional arguments to be passed to the save method of the BIMMS object
        """
        if not manual:
            self.config.save(save=save, fname=fname, **kwargs)
        else:
            self.config_mode("MANUAL")
            self.manual_config.save(save=save, fname=fname, **kwargs)

    def load_config(self, data, blacklist={}, manual=False, **kwargs):
        """
        Load the bimms the configuration

        Parameters
        ----------
        data : dict
            Dictionary containing the BIMMS object
        blacklist : dict, optional
            Dictionary containing the keys to be excluded from the load
        **kwargs : dict, optional
            Additional arguments to be passed to the load method of the BIMMS object
        """
        if not manual:
            self.config.load(data, blacklist, **kwargs)
        else:
            self.config_mode("MANUAL")
            self.manual_config.load(data, blacklist, **kwargs)

    ##############################################
    ## AD2 Digital IO methods for gains control ##
    ##############################################
    def set_gain_IA(self, channel=1, gain=1):
        gain_array = cst.gain_array
        gain_IA1 = cst.gain_IA1
        gain_IA2 = cst.gain_IA2
        idx_gain = np.where(gain_array == gain)
        idx_gain = int(idx_gain[0])
        if idx_gain != None:
            if channel == 1:
                self.set_gain_ch1_1(gain_IA1[idx_gain])
                self.set_gain_ch1_2(gain_IA2[idx_gain])
            if channel == 2:
                self.set_gain_ch2_1(gain_IA1[idx_gain])
                self.set_gain_ch2_2(gain_IA2[idx_gain])
        else:
            if verbose:
                print("WARNING: Wrong IA gain value. IA gain set to 1.")
            if channel == 1:
                self.set_gain_ch1_1(gain_IA1[0])
                self.set_gain_ch1_2(gain_IA2[0])
            if channel == 2:
                self.set_gain_ch2_1(gain_IA1[0])
                self.set_gain_ch2_2(gain_IA2[0])

    ################################
    ## BIMMS measurements methods ##
    ################################
    def set_config(self,send = True):
        """
        
        """
        if (self.config_mode == "MEASURE"):
            if self.config.wire_mode == "2" or self.config.wire_mode == "2_WIRE":
                self.set_2_wires_mode()
            else:   # 4
                self.set_4_wires_mode()
            self.set_exitation_config()
            self.set_recording_config()
        else :
            self.set_manual_config()

        # Send the configuration to set the relays
        if (send):
            if not (self.get_state()==cst.STM32_idle):
                self.set_STM32_idle()
                pass
            self.send_config()

    def reset_config(self):
        self.config_mode("MEASURE")
        self.config.reset()
        self.manual_config.reset()
        self.set_config(send = False)
        print("INFO: BIMMS config reset!")

    def set_exitation_config(self):
        """
        
        """
        if self.config.excitation_sources == "EXTERNAL":
            self.connect_external_AWG()
        else:
            self.connect_internal_AWG()

        if self.config.excitation_mode == "G_EIS":
            self.connect_Ipos_to_StimPos()
            self.disable_potentiostat()
            if self.config.G_EIS_gain == "LOW":
                self.set_low_gain_current_source()
            elif self.config.G_EIS_gain == "HIGH":
                self.set_high_gain_current_source()
            else:   # AUTO
                self.set_low_gain_current_source()  ### TO IMPLEMENT
                print("WARNING: AUTO CURRENT GAIN NOT IMPLEMENTED")
        else:   # P_EIS
            self.connect_Vpos_to_StimPos()
            # self.disable_current_source()			#need to be tested, bug with AD830?
            self.disable_potentiostat()

        if self.config.excitation_signaling_mode == "DIFF": 
            if self.config.excitation_mode == "G_EIS":
                self.connect_Ineg_to_StimNeg()
            else:   # P_EIS
                self.connect_Vneg_to_StimNeg()
        else:   # SE
            self.connect_GND_to_StimNeg()

        if self.config.excitation_coupling == "AC":
            self.set_Stim_AC_coupling()
        else:   # DC
            self.set_Stim_DC_coupling()

        if self.config.DC_feedback == True:
            self.enable_DC_feedback()
        else:   # False
            self.disable_DC_feedback()


    def set_recording_config(self):
        """
        
        """
        self.config.recording_signaling_mode_local = self.config.recording_signaling_mode
        if self.config.recording_signaling_mode == "AUTO":
            self.config.recording_signaling_mode_local = str(self.config.excitation_signaling_mode)

        if self.config.recording_mode == "I":
            self.set_I_recording()

        elif self.config.recording_mode == "V":
            self.set_V_recording()
        else: # BOTH
            self.set_I_recording()
            self.set_V_recording()

        if self.config.readout_coupling == "AC":
            self.set_CH1_AC_coupling()
            self.set_CH2_AC_coupling()
        else:   # DC
            self.set_CH1_DC_coupling()
            self.set_CH2_DC_coupling()

        self.set_gain_IA(channel=cst.IRO_channel, gain=int(self.config.IRO_gain))
        self.set_gain_IA(channel=cst.VRO_channel, gain=int(self.config.VRO_gain))

    def set_I_recording(self):

        if self.config.recording_mode == "I":
            self.disconnect_CH1_from_scope_1()
        self.connect_CH2_to_scope_2()
        self.connect_TIA_to_CH2()
        self.connect_TIA_to_StimNeg()
        if self.config.excitation_mode == "G_EIS":
            print("WARNING: I_recording signalling configuration forced.")
            if self.config.excitation_signaling_mode == "DIFF":
                self.connect_TIA_Neg_to_Ineg()  
                self.set_TIA_AC_coupling() #???????? 
            else:
                self.connect_TIA_Neg_to_ground()
        else:   # P_EIS
            if self.config.recording_signaling_mode_local == "DIFF":
                self.connect_TIA_Neg_to_Vneg()
            else:
                self.connect_TIA_Neg_to_ground()

    def set_V_recording(self):
        if self.config.recording_mode == "V":
            self.disconnect_CH2_from_scope_2()
            #self.disconnect_TIA_from_CH2() #BUG? 
        self.connect_CH1_to_scope_1()
        if self.config.excitation_mode == "G_EIS":
            if self.config.recording_signaling_mode_local == "SE" and self.config.excitation_signaling_mode == "DIFF":
                print("WARNING: Manual connection between V- and GND required!")

    #######################################
    ##  test config methods ##
    #######################################

    def set_manual_config(self):
        print("INFO: BIMMS set to test mode.")
        if self.manual_config.wire_mode == "2" or self.manual_config.wire_mode == "2_WIRE":
            self.set_2_wires_mode()
        else:   # 4
            self.set_4_wires_mode()

        self.set_test_excitation_config()
        self.set_test_readout_config()

    def set_test_excitation_config(self):
        if (self.manual_config.waveform_gen) == "INTERNAL":
            self.connect_internal_AWG()
        else:
            self.connect_external_AWG()

        self.set_test_excitation_source()
        if (self.manual_config.excitation_coupling == "DC"):
            self.set_Stim_DC_coupling()
        else:
            self.set_Stim_AC_coupling()
        
        if self.config.DC_feedback == True:
            self.enable_DC_feedback()
        else:   # False
            self.disable_DC_feedback()
        
        if (self.manual_config.Enable_Isource== True):
            self.enable_current_source()
        else:
            self.disable_current_source()


    def set_test_excitation_source(self):
        if (self.manual_config.excitation_source == "NONE"):
            self.disconnect_StimNeg()
            self.disconnect_StimPos()
        elif (self.manual_config.excitation_source == "CURRENT"):
            self.connect_Ipos_to_StimPos()
            if (self.manual_config.excitation_signaling_mode == "SE"):
                self.connect_GND_to_StimNeg()
            else:
                self.connect_Ineg_to_StimNeg()

            if (self.manual_config.I_source_gain == "LOW"):
                self.set_low_gain_current_source()
            else:
                self.set_high_gain_current_source()
        else: 
            self.connect_Vpos_to_StimPos()
            if (self.manual_config.excitation_signaling_mode == "SE"):
                self.connect_GND_to_StimNeg()
            else:
                self.connect_Vneg_to_StimNeg()
    
    def set_test_readout_config(self):
        self.set_test_CHx_to_SCOPEx()

        self.set_gain_IA(channel=1, gain=int(self.manual_config.CH1_gain))
        self.set_gain_IA(channel=2, gain=int(self.manual_config.CH2_gain))

        self.set_readout_coupling()
        self.connect_TIA()

    def connect_TIA(self):
        if (self.manual_config.connect_TIA== True):

            self.connect_TIA_to_StimNeg()

        if (self.manual_config.TIA_to_CH2==True):
            self.connect_TIA_to_CH2()
        else:
            self.disconnect_TIA_from_CH2()
        
        if (self.manual_config.TIA_NEG == "GND"):
            self.connect_TIA_Neg_to_ground()

        elif (self.manual_config.TIA_NEG == "Vneg"):
            self.connect_TIA_Neg_to_Vneg()
        
        else:
             self.connect_TIA_Neg_to_Ineg

    def set_test_CHx_to_SCOPEx(self):
        if (self.manual_config.CHx_to_Scopex == "NONE"):
            self.disconnect_CH2_from_scope_2()
            self.disconnect_CH1_from_scope_1()
        elif  (self.manual_config.CHx_to_Scopex == "CH1"):
            self.disconnect_CH2_from_scope_2()
            self.connect_CH1_to_scope_1()
        elif  (self.manual_config.CHx_to_Scopex == "CH2"):
            self.disconnect_CH1_from_scope_1()
            self.connect_CH2_to_scope_2()
        else:
            self.connect_CH2_to_scope_2()
            self.connect_CH1_to_scope_1()

    def set_readout_coupling(self):
        if (self.manual_config.CH1_coupling == "AC"):
            self.set_CH1_AC_coupling()
        else:
            self.set_CH1_DC_coupling()
        
        if (self.manual_config.CH2_coupling == "AC"):
            self.set_CH2_AC_coupling()
        else:
            self.set_CH2_DC_coupling()

        if (self.manual_config.TIA_coupling == "AC"):
            self.set_TIA_AC_coupling()
        else:
            self.set_TIA_DC_coupling()


       
    #######################################
    ##  Other methods ##
    #######################################
