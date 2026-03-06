"""Calibration primitives for BIMMS.

This module defines the base calibrator API and initial scaffolding for
calibration parameter containers.

In the BIMMS ecosystem, a *calibrator* is responsible for estimating correction
parameters (e.g., offsets, gain/phase corrections, fixture parasitics) from
calibration measurements and storing them into a
:class:`~bimms.system.BIMMScalibration.BIMMScalibration` object.


Notes
-----
- This module currently provides a generic interface (:class:`Calibrator`) and a
  simple parameter holder (:class:`Offsets`). Concrete calibration algorithms
  should implement :meth:`Calibrator.calibrate`.

See Also
--------
bimms.system.BIMMScalibration.BIMMScalibration
    Calibration context container used across BIMMS.
bimms.backend.BIMMS_Class.BIMMS_class
    Base class providing JSON-friendly save/load behavior.
"""

import numpy as np

from ..backend.BIMMS_Class import BIMMS_class, abstractmethod
from ..system.BIMMScalibration import BIMMScalibration
from ..utils import constants as BIMMScst
import matplotlib.pyplot as plt

class Calibrator(BIMMS_class):
    """
    Abstract base class for BIMMS calibrators.

    A calibrator estimates correction parameters from calibration measurements
    and applies them to a BIMMS calibration context (typically a
    :class:`~bimms.system.BIMMScalibration.BIMMScalibration` instance).

    Subclasses should implement :meth:`calibrate` and may expose configuration
    attributes (frequency range, number of points, settling times, etc.) that are
    then serializable through :class:`~bimms.backend.BIMMS_Class.BIMMS_class`.

    Parameters
    ----------
    ID : int, optional
        Identifier for the calibrator instance (default is 0). This can be used
        to track multiple calibration steps or versions.

    Attributes
    ----------
    ID : int
        Calibrator identifier.
    raw : bool
        Flag indicating whether the calibrator should operate on raw (uncorrected)
        data. The semantic meaning depends on the concrete implementation.

    Notes
    -----
    This class inherits from :class:`~bimms.backend.BIMMS_Class.BIMMS_class`,
    therefore it can be serialized with :meth:`BIMMS_class.save` and restored
    with :meth:`BIMMS_class.load`.
    """
    @abstractmethod
    def __init__(self, ID=0):
        """
        Initialize the calibrator.

        Parameters
        ----------
        ID : int, optional
            Calibrator identifier.
        """
        super().__init__()
        self.ID = ID
        self.raw = False

    def set_parameters(self,**kawrgs):
        """
        Set calibrator parameters from keyword arguments.

        Parameters
        ----------
        **kawrgs
            Keyword arguments whose keys are matched against existing instance
            attributes. Only keys already present in ``self.__dict__`` are
            considered.

        Notes
        -----
        The current implementation mirrors the original source and contains
        assignment-related issues (it uses ``==`` and indexes ``kawrgs`` with
        ``dict``). This docstring documents intended behavior without modifying
        the executable code, per project constraints.
        """
        for key in kawrgs:
            if key in self.__dict__:
                self.__dict__[key] == kawrgs[dict]

    def get_parameters(self):
        """
        Return current calibrator parameters.

        Returns
        -------
        dict
            The calibrator instance attribute dictionary (``self.__dict__``).

        Notes
        -----
        Returning ``self.__dict__`` provides a direct view of the calibrator state.
        Downstream code should avoid mutating it in-place unless that is intended.
        """
        return self.__dict__


    def calibrate(self, BS: BIMMScalibration):
        """
        Run the calibration routine (to be implemented by subclasses).

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS calibration context that will be read/updated by the calibrator.

        Returns
        -------
        None
            Concrete implementations typically modify ``BS`` in place and/or
            populate calibrator attributes.

        See Also
        --------
        Offsets
            Example of a calibrator-derived class carrying calibration parameters.
        """
        pass


class Offsets(Calibrator):
    """
    Parameter container for frequency-dependent offset calibration.

    This class currently stores common configuration parameters for an offset
    calibration over a frequency range. It does not yet implement a concrete
    calibration algorithm (i.e., it does not override :meth:`Calibrator.calibrate`).

    Parameters
    ----------
    fmin : float, optional
        Minimum frequency in Hz (default is 1e3).
    fmax : float, optional
        Maximum frequency in Hz (default is 1e7).
    n_pts : int, optional
        Number of frequency points (default is 101).
    settling_time : float, optional
        Settling time in seconds before sampling at each frequency (default is
        0.001 s).
    nperiods : int, optional
        Number of excitation periods to acquire/average per frequency (default is 8).
    ID : int, optional
        Calibrator identifier (default is 0).

    Attributes
    ----------
    fmin, fmax : float
        Frequency range in Hz.
    n_pts : int
        Number of points in the sweep.
    settling_time : float
        Settling time in seconds.
    nperiods : int
        Number of periods per frequency.

    Notes
    -----
    For reproducibility, consider recording:
    - the exact firmware version used during calibration,
    - electrode/fixture details,
    - temperature and solution composition (if applicable),
    - measurement mode settings (see :mod:`bimms.utils.constants`).

    Future Work
    -----------
    A complete implementation would typically:
    - perform a frequency sweep using a :class:`~bimms.system.BIMMS.BIMMS` system,
    - estimate complex offsets and potentially frequency-dependent errors,
    - store the results into the provided :class:`~bimms.system.BIMMScalibration.BIMMScalibration`.
    """
    def __init__(self, fmin=1e3, fmax=1e7, n_pts=101, settling_time=0.001, nperiods=8, ID=0):
        """
        Initialize an offset calibration parameter set.

        Parameters
        ----------
        fmin, fmax, n_pts, settling_time, nperiods, ID
            See :class:`Offsets`.
        """
        super().__init__(ID=ID)
        self.fmin = fmin
        self.fmax = fmax
        self.n_pts = n_pts
        self.settling_time = settling_time
        self.nperiods = nperiods


