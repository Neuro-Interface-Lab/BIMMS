
import numpy as np

from ..backend.BIMMS_Class import BIMMS_class, abstractmethod
from ..system.BIMMScalibration import BIMMScalibration
from ..utils import constants as BIMMScst
import matplotlib.pyplot as plt

class Calibrator(BIMMS_class):
    """
    A generic class of calibrator from wchich every calibrator type should inherit
    """
    @abstractmethod
    def __init__(self, ID=0):
        super().__init__()
        self.ID = ID
        self.raw = False

    def set_parameters(self,**kawrgs):
        for key in kawrgs:
            if key in self.__dict__:
                self.__dict__[key] == kawrgs[dict]

    def get_parameters(self):
        return self.__dict__


    def calibrate(self, BS: BIMMScalibration):
        pass


class Offsets(Calibrator):
    """
    
    """
    def __init__(self, fmin=1e3, fmax=1e7, n_pts=101, settling_time=0.001, nperiods=8, ID=0):
        super().__init__(ID=ID)
        self.fmin = fmin
        self.fmax = fmax
        self.n_pts = n_pts
        self.settling_time = settling_time
        self.nperiods = nperiods


