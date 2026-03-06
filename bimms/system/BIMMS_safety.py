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
import json
from scipy.signal import butter, lfilter
from time import sleep

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from .BIMMScalibration import BIMMScalibration
from ..measure.Measure import Measure
from ..results.Results import BIMMS_results

### for debug
faulthandler.enable()
### verbosity of the verbosity
verbose = True

def is_BIMMS(obj):
    return isinstance(obj, BIMMS)

##############################
## CLASS FOR BIMMS HANDLING ##
##############################
class BIMMS(BIMMScalibration):
    def __init__(self, bimms_id=None, serialnumber=None):
        super().__init__(bimms_id=bimms_id, serialnumber=serialnumber)
        self.measures = []
        self.is_setup = False
        self.results = BIMMS_results()
    
    def clear_results(self):
        self.results = BIMMS_results()

    def attach_calibrator(self, calibrator):
        pass

    def attach_measure(self, m : Measure):
        self.measures += [m]

    def clear_measures(self):
        self.measures = []

    def calibrate(self):
        pass

    def check_measures_config():
        pass


    def setup_bimms(self):
        if not self.is_setup:
            self.check_config()
            self.set_config()
            if float(self.config.config_settling):
                sleep(float(self.config.config_settling))
            self.get_awg_parameters()
            self.get_recording_gains()


    def measure(self, clear_mstack=True, overwrite=True):
        self.setup_bimms()
        if len(self.measures) == 1:
            m = self.measures[0]
            if overwrite or self.results == BIMMS_results():
                self.results = m.measure(self)
                self.results["measure"] = m.save(save=False)
            else:
                self.results.update(m.measure(self))
        else:
            for m in self.measures:
                if m.ID not in self.results:
                    self.results[m.ID] = m.measure(self)
                    self.results["measure"] = m.save(save=False)
                else:
                    self.results[m.ID].update(m.measure(self))
        if (clear_mstack):
            self.clear_measures()
        return self.results

    def check_config(self):
        return True