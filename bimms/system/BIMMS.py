"""High-level interface for configuring and operating the BIMMS platform.

This module defines the top-level :class:`BIMMS` object used to configure the
Bio Impedance Measurement System (BIMMS), attach measurement procedures, and
collect results. The implementation builds on the lower-level hardware,
configuration, and calibration layers to expose an application-facing API for
bio-impedance and electrode--tissue interface experiments.
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
    """
    Return whether an object is an instance of :class:`BIMMS`.

    Parameters
    ----------
    obj : object
        Object to be tested.

    Returns
    -------
    bool
        ``True`` if ``obj`` is a :class:`BIMMS` instance, otherwise ``False``.
    """
    return isinstance(obj, BIMMS)

##############################
## CLASS FOR BIMMS HANDLING ##
##############################
class BIMMS(BIMMScalibration):
    """
    High-level controller for BIMMS experiments.

    This class aggregates configuration, calibration, and measurement orchestration
    for the Bio Impedance Measurement System. It stores pending measurement objects,
    applies the active hardware configuration, and consolidates measurement results.
    """
    def __init__(self, bimms_id=None, serialnumber=None):
        """
        Initialize a BIMMS controller instance.

        Parameters
        ----------
        bimms_id : int, optional
            Integer identifier associated with a known BIMMS instrument.
        serialnumber : str, optional
            Explicit Analog Discovery 2 serial number. When provided, it overrides
            automatic device discovery.
        """
        super().__init__(bimms_id=bimms_id, serialnumber=serialnumber)
        self.measures = []
        self.is_setup = False
        self.results = BIMMS_results()
    
    def clear_results(self):
        """
        Reset the internal results container.

        Returns
        -------
        None
        """
        self.results = BIMMS_results()

    def attach_calibrator(self, calibrator):
        """
        Attach a calibration helper object to the instance.

        Parameters
        ----------
        calibrator : object
            External calibration object intended to provide calibrated coefficients or
            procedures.

        Notes
        -----
        This method is currently a placeholder and does not yet modify the object
        state.
        """
        pass

    def attach_measure(self, m : Measure):
        """
        Append a measurement object to the execution queue.

        Parameters
        ----------
        m : Measure
            Measurement object implementing the project-specific ``measure`` and
            ``save`` interfaces.

        Returns
        -------
        None
        """
        self.measures += [m]

    def clear_measures(self):
        """
        Remove all queued measurement objects.

        Returns
        -------
        None
        """
        self.measures = []

    def calibrate(self):
        """
        Run the platform calibration workflow.

        Notes
        -----
        This method is declared for API completeness but is not implemented in the
        current source version.
        """
        pass

    def check_measures_config():
        """
        Validate the consistency of queued measurement objects.

        Notes
        -----
        The method is presently a placeholder for future consistency checks across
        stacked measurements.
        """
        pass


    def setup_bimms(self):
        """
        Apply the active BIMMS configuration before acquisition.

        The method validates the current configuration, programs the hardware routing,
        waits for the configured settling delay, and derives excitation and recording
        gains needed for subsequent measurements.

        Returns
        -------
        None
        """
        if not self.is_setup:
            self.check_config()
            self.set_config()
            if float(self.config.config_settling):
                sleep(float(self.config.config_settling))
            self.get_awg_parameters()
            self.get_recording_gains()


    def measure(self, clear_mstack=True, overwrite=True):
        """
        Execute the queued measurement sequence.

        Parameters
        ----------
        clear_mstack : bool, optional
            If ``True``, clear the measurement stack after execution.
        overwrite : bool, optional
            If ``True``, replace previously stored results when only one measurement is
            queued.

        Returns
        -------
        BIMMS_results
            Results structure populated with the acquired data and serialized
            measurement metadata.
        """
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
        """
        Check whether the current configuration is valid.

        Returns
        -------
        bool
            ``True`` in the current implementation.
        """
        return True
