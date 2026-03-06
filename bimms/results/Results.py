"""Results containers and post-processing utilities for BIMMS.

This module defines result objects returned by BIMMS measurements.

Design goals
------------
- **Lightweight serialization**: results inherit from
  :class:`~bimms.backend.BIMMS_Class.BIMMS_class` to leverage the same JSON
  save/load mechanism as other BIMMS objects.
- **Dict-like ergonomics**: results behave like dictionaries while also exposing
  their keys as attributes (synchronized view).
- **Reproducibility**: measurement configuration metadata is stored under the
  ``config`` key and raw acquisitions under ``raw_data``.

The main classes are:

- :class:`BIMMS_results`: base class (dict + BIMMS_class) with synchronized
  attribute/item storage.
- :class:`bode_results`: frequency-domain magnitude/phase results, used for Bode
  and EIS workflows.
- :class:`temporal_results`: time-domain samples plus basic FFT-based utilities.

Notes
-----
* Some post-processing methods in this module are marked as incomplete by design
  (see warning prints) and should be validated for your use case.
* The FFT utilities rely on :mod:`scipy.fftpack`.

Open Science recommendations
----------------------------
When saving and sharing results, consider including:

- Hardware revision, analog front-end configuration, and electrode/fixture info.
- Firmware/software versions (AD2, STM32, Python package version).
- Calibration state and calibration metadata.
- Environmental metadata (temperature, sample composition, etc.).
- Provenance of processing steps (filtering, cropping windows, FFT parameters).

Authors
-------
Florian Kolbl, Thomas Couppey, Louis Regnacq
"""
import numpy as np
from scipy.fftpack import fft, ifft

from ..backend.BIMMS_Class import BIMMS_class, abstractmethod, is_BIMMS_class

"""from ..system.BIMMScalibration import BIMMScalibration
from ..utils import constants as BIMMScst
import matplotlib.pyplot as plt"""


class BIMMS_results(BIMMS_class, dict):
    """
    Base results container for BIMMS.

    This class combines:

    - :class:`dict` behavior (items, update, serialization-friendly structure)
    - :class:`~bimms.backend.BIMMS_Class.BIMMS_class` behavior (save/load and
      BIMMS object tagging)

    The class maintains a synchronized representation where keys stored in the
    mapping are also accessible as object attributes (and vice versa).

    Parameters
    ----------
    config : dict or BIMMS_class, optional
        Configuration metadata associated with the measurement that produced the
        results. If a BIMMS object is provided, it is converted with ``save()``.
    raw_data : dict, optional
        Raw acquisition payload, typically arrays/lists of samples and metadata.
    ID : int, optional
        Reserved identifier for results objects (default is 0). The current
        implementation does not store/use it explicitly.

    Attributes
    ----------
    config : dict
        Configuration metadata stored under the ``"config"`` key.
    raw_data : dict
        Raw data stored under the ``"raw_data"`` key.

    Notes
    -----
    The internal ``__sync`` method updates the mapping from ``self.__dict__`` and
    removes the internal ``"__BIMMSObject__"`` marker from the public dictionary.

    See Also
    --------
    bode_results
        Frequency-domain results for Bode/EIS.
    temporal_results
        Time-domain results with FFT utilities.
    """

    def __init__(self, config=None, raw_data=None, ID=0):
        super().__init__()
        self.config = {}
        self.raw_data = {}

        self.__set_config(config)
        self.__set_raw_data(raw_data)
        self.__sync()

    def __set_config(self, config):
        """
        Normalize and store configuration metadata.

        Parameters
        ----------
        config : dict or BIMMS_class or None
            If ``None``, defaults to an empty dict. If a BIMMS object, it is
            serialized with ``save(save=False)`` and stored as a plain dict.

        Notes
        -----
        If the serialized configuration contains a ``"bimms_type"`` key, it is
        moved to ``"result_type"`` to avoid ambiguity with the results object
        type during later reconstruction.
        """
        if config is None:
            config = {}
        elif is_BIMMS_class(config):
            config = config.save(save=False)
        if "bimms_type" in config:
            config["result_type"] = config.pop("bimms_type")
        self.update({"config": config})

    def __set_raw_data(self, raw_data):
        """
        Store the raw acquisition payload.

        Parameters
        ----------
        raw_data : dict or None
            If ``None``, defaults to an empty dict.
        """
        if raw_data is None:
            raw_data = {}
        self.update({"raw_data": raw_data})

    def save(self, save=False, fname="bimms_save.json", blacklist=[], **kwargs):
        """
        Serialize results to a JSON-compatible dictionary (and optionally save).

        Parameters
        ----------
        save : bool, optional
            If True, write JSON to disk using the base class implementation.
        fname : str, optional
            Output JSON filename when ``save=True``.
        blacklist : list, optional
            Attributes/keys to exclude from the export. This method always adds
            ``"BIMMS"`` to the blacklist to avoid serializing live hardware
            handles stored in :class:`bode_results` and :class:`temporal_results`.
        **kwargs
            Forwarded to :meth:`~bimms.backend.BIMMS_Class.BIMMS_class.save`.

        Returns
        -------
        dict
            JSON-compatible representation of the results.
        """
        self.__sync()
        bl = [b for b in blacklist]
        bl += ["BIMMS"]
        return super().save(save, fname, bl, **kwargs)

    def load(self, data, blacklist=[], **kwargs):
        """
        Load results from a serialized dictionary or JSON file.

        Parameters
        ----------
        data : dict or str
            Dictionary content or JSON filename to load.
        blacklist : list, optional
            Keys/attributes to exclude from loading.
        **kwargs
            Forwarded to :meth:`~bimms.backend.BIMMS_Class.BIMMS_class.load`.

        Returns
        -------
        None
            The object is modified in place.
        """
        super().load(data, blacklist, **kwargs)
        self.__sync()

    def __setitem__(self, key, value):
        """
        Set a mapping item and mirror it to attributes.

        Parameters
        ----------
        key : hashable
            Mapping key.
        value : object
            Value to store.

        Notes
        -----
        The ``"bimms_type"`` key is handled specially by the BIMMS base classes.
        This override avoids mirroring that key into ``__dict__``.
        """
        if not key == "bimms_type":
            self.__dict__[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        """
        Delete a mapping item and mirror deletion to attributes.

        Parameters
        ----------
        key : hashable
            Mapping key.

        Notes
        -----
        The ``"bimms_type"`` key is not mirrored into attributes and is therefore
        ignored in ``__dict__`` deletion.
        """
        if not key == "bimms_type":
            del self.__dict__[key]
        super().__delitem__(key)

    def update(self, __m, **kwargs) -> None:
        """
        Update both the mapping and the instance attributes.

        Parameters
        ----------
        __m : mapping
            Items to merge into the result container.
        **kwargs
            Forwarded to the underlying dict update.

        Notes
        -----
        This overload ensures a consistent dual view (attribute + dict).
        """
        self.__dict__.update(__m, **kwargs)
        super().update(__m, **kwargs)

    def __sync(self):
        """
        Synchronize the mapping with ``self.__dict__``.

        Notes
        -----
        This method is used internally before saving and after loading to ensure
        the dict view matches the attribute view.
        """
        self.update(self.__dict__)
        self.pop("__BIMMSObject__")


class Results_test(BIMMS_results):
    """
    Minimal results subclass used for testing.

    Parameters
    ----------
    ID : int, optional
        Reserved identifier (default is 0).
    """
    def __init__(self, ID=0):
        super().__init__(ID=ID)


class bode_results(BIMMS_results):
    """
    Frequency-domain magnitude/phase results (Bode / EIS).

    Parameters
    ----------
    BIMMS : object, optional
        A BIMMS system/context instance exposing at least:
        ``config``, ``calibrated``, ``cal_ch1_gain``, ``cal_ch2_gain``,
        ``cal_TIA_gain``.
    data : dict, optional
        Raw bode payload with keys:
        ``"freq"``, ``"mag_ch1_raw"``, ``"mag_raw"``, ``"phase_raw"``.
    ID : int, optional
        Reserved identifier (default is 0).

    Stored Keys
    -----------
    freq : ndarray
        Frequency vector in Hz.
    mag_ch1_raw : ndarray
        Raw channel 1 magnitude.
    mag_ch2_raw : ndarray
        Derived raw channel 2 magnitude (``mag_ch1_raw / mag_raw``).
    phase_raw : ndarray
        Raw phase in degrees (as produced by the acquisition helper).
    V_readout : ndarray
        Channel 1 magnitude mapped to voltage readout (uncalibrated path).
    I_readout : ndarray
        Channel 2 magnitude mapped to current readout (uncalibrated path).

    Notes
    -----
    If ``BIMMS.calibrated`` is True, the current implementation leaves a ``pass``
    placeholder. Otherwise, it computes ``V_readout`` and ``I_readout`` using
    the calibration gains available on the BIMMS object.
    """

    def __init__(self, BIMMS=None, data=None, ID=0):
        super().__init__(config=BIMMS.config, raw_data=data, ID=ID)
        self.BIMMS = BIMMS
        self["freq"] = self.raw_data["freq"]
        self["mag_ch1_raw"] = self.raw_data["mag_ch1_raw"]
        self["mag_ch2_raw"] = self.raw_data["mag_ch1_raw"] / self.raw_data["mag_raw"]
        self["phase_raw"] = self.raw_data["phase_raw"]
        if self.BIMMS.calibrated:
            pass
        else:
            self["V_readout"] = self["mag_ch1_raw"] / self.BIMMS.cal_ch1_gain
            self["I_readout"] = self["mag_ch2_raw"] / (
                self.BIMMS.cal_ch2_gain * self.BIMMS.cal_TIA_gain
            )

    def update(self, __m, **kwargs) -> None:
        """
        Merge another :class:`bode_results` into this instance.

        Parameters
        ----------
        __m : bode_results or mapping
            If a :class:`bode_results` instance, arrays are concatenated or
            stacked depending on whether the incoming object contains a single
            frequency point. Otherwise, behaves like standard dict update.
        **kwargs
            Forwarded to base dict update when ``__m`` is not a :class:`bode_results`.

        Notes
        -----
        This method supports building multi-point datasets by accumulating single
        frequency measurements as a sweep.
        """
        if isinstance(__m, bode_results):
            if len(__m["freq"]) == 1:
                self["freq"] = np.concatenate([self["freq"], __m["freq"]])
                self["mag_ch1_raw"] = np.concatenate(
                    [self["mag_ch1_raw"], __m["mag_ch1_raw"]]
                )
                self["mag_ch2_raw"] = np.concatenate(
                    [self["mag_ch2_raw"], __m["mag_ch2_raw"]]
                )
                self["phase_raw"] = np.concatenate([self["phase_raw"], __m["phase_raw"]])
                self["V_readout"] = np.concatenate([self["V_readout"], __m["V_readout"]])
                self["I_readout"] = np.concatenate([self["I_readout"], __m["I_readout"]])

            else:
                self["mag_ch1_raw"] = np.vstack(
                    [self["mag_ch1_raw"], __m["mag_ch1_raw"]]
                )
                self["mag_ch2_raw"] = np.vstack(
                    [self["mag_ch2_raw"], __m["mag_ch2_raw"]]
                )
                self["phase_raw"] = np.vstack([self["phase_raw"], __m["phase_raw"]])
                self["V_readout"] = np.vstack([self["V_readout"], __m["V_readout"]])
                self["I_readout"] = np.vstack([self["I_readout"], __m["I_readout"]])
        else:
            super().update(__m, **kwargs)

    def EIS(self):
        """
        Compute impedance magnitude and phase from voltage and current readouts.

        Returns
        -------
        mag_Z : ndarray
            Impedance magnitude computed as ``V_readout / I_readout``.
        phase_Z : ndarray
            Impedance phase in degrees computed as ``phase_raw - 180``.

        Warnings
        --------
        Prints a warning indicating that EIS processing is not fully implemented.

        Notes
        -----
        This helper assumes that voltage and current readouts are already mapped
        into consistent units by the upstream calibration constants.
        """
        print("WARNING: EIS measure not fully implemented")
        self["mag_Z"] = self["V_readout"] / self["I_readout"]
        self["phase_Z"] = self["phase_raw"] - 180
        # results['mag'] = data['']
        return self["mag_Z"], self["phase_Z"]


class temporal_results(BIMMS_results):
    """
    Time-domain results with basic post-processing utilities.

    Parameters
    ----------
    BIMMS : object or dict, optional
        If not None, expected to provide a ``config`` attribute. If None, the
        provided value is used directly as the configuration dictionary.
    data : dict, optional
        Raw payload with keys: ``"t"``, ``"chan1"``, ``"chan2"``.
    ID : int, optional
        Reserved identifier (default is 0).

    Stored Keys
    -----------
    t_raw : ndarray
        Raw time vector.
    chan1_raw, chan2_raw : ndarray
        Raw channel sample arrays.
    dt : float
        Sampling interval derived from ``t_raw``.
    sample_rate : float
        Sampling frequency in Hz.
    n_sample : int
        Number of samples.
    single_meas : bool
        True for a single acquisition; False when multiple acquisitions have been
        stacked via :meth:`update`.

    Notes
    -----
    The class offers convenience methods for cropping and FFT-based filtering.
    """

    def __init__(self, BIMMS=None, data=None, ID=0):
        if BIMMS is not None:
            config = BIMMS.config
        else:
            config = BIMMS
        super().__init__(config=config, raw_data=data, ID=ID)
        self.BIMMS = BIMMS

        # print("WARNING: temporal post-processing measure not fully implemented")
        self["t_raw"] = np.array([])
        self["chan2_raw"] = np.array([])
        self["chan1_raw"] = np.array([])
        self["dt"] = 0
        self["sample_rate"] = 0
        self["n_sample"] = 0
        self.__set_data()

        self["single_meas"] = True

    def __set_data(self):
        """
        Initialize derived fields from ``raw_data`` if present.

        Notes
        -----
        Computes ``dt``, ``sample_rate``, and ``n_sample`` from the provided time
        vector.
        """
        if self.raw_data != {}:
            self["t_raw"] = np.array(self.raw_data["t"])
            self["chan2_raw"] = np.array(self.raw_data["chan2"])
            self["chan1_raw"] = np.array(self.raw_data["chan1"])
            self["dt"] = self.t_raw[1] - self.t_raw[0]
            self["sample_rate"] = 1 / self.dt
            self["n_sample"] = len(self.t_raw)

    def load(self, data, blacklist=[], **kwargs):
        """
        Load from serialized data and recompute derived fields.

        Parameters
        ----------
        data : dict or str
            Serialized dictionary or JSON filename.
        blacklist : list, optional
            Keys to exclude from loading.
        **kwargs
            Forwarded to base load.

        Returns
        -------
        None
        """
        super().load(data, blacklist, **kwargs)
        self.__set_data()


    def update(self, __m, **kwargs) -> None:
        """
        Merge another :class:`temporal_results` into this instance.

        Parameters
        ----------
        __m : temporal_results or mapping
            When merging another :class:`temporal_results`, data are stacked
            across acquisitions if the time vector lengths match.
        **kwargs
            Forwarded to base dict update when ``__m`` is not a :class:`temporal_results`.

        Notes
        -----
        After stacking, ``single_meas`` is set to False.
        """
        if isinstance(__m, temporal_results):
            if np.shape(self["t_raw"])[-1] == np.shape(__m["t_raw"])[-1]:
                # self['t'] = np.vstack((self['t'], __m['t']))
                self["chan2_raw"] = np.vstack((self["chan2_raw"], __m["chan2_raw"]))
                self["chan1_raw"] = np.vstack((self["chan1_raw"], __m["chan1_raw"]))
                self["single_meas"] = False
        else:
            super().update(__m, **kwargs)

    ######################################
    #######  post proc functions  ########
    ######################################

    def crop_time(self, t_start=None, t_stop=None):
        """
        Crop the time-domain data to a specified interval.

        Parameters
        ----------
        t_start : float, optional
            Start time (same units as ``t_raw``). Defaults to the first sample.
        t_stop : float, optional
            Stop time (same units as ``t_raw``). Defaults to the last sample.

        Notes
        -----
        Cropped vectors are stored under keys ``t``, ``chan1_t``, ``chan2_t``.
        For stacked acquisitions, the crop is applied along the last axis.
        """
        t1 = t_start or self["t_raw"][0]
        t2 = t_stop or self["t_raw"][-1]

        I = np.argwhere((self.t_raw >= t1) & (self.t_raw < t2))[:, 0]

        self["t"] = self["t_raw"][I]
        self["n_sample"] = len(I)
        if self.single_meas:
            self["chan1_t"] = self["chan1_raw"][I]
            self["chan2_t"] = self["chan2_raw"][I]
        else:
            self["chan1_t"] = self["chan1_raw"][:, I]
            self["chan2_t"] = self["chan2_raw"][:, I]

    def fft(self, t_start=None, t_stop=None):
        """
        Compute FFT of the cropped time-domain signals.

        Parameters
        ----------
        t_start : float, optional
            Crop start time passed to :meth:`crop_time`.
        t_stop : float, optional
            Crop stop time passed to :meth:`crop_time`.

        Notes
        -----
        - Frequency vector is stored under key ``f``.
        - FFT outputs are stored under keys ``chan1_f`` and ``chan2_f``.
        - The function prints the frequency vector (as in the original code).
        """
        self.crop_time(t_start=t_start, t_stop=t_stop)
        T = self["n_sample"] / (self["sample_rate"])
        self["f"] = np.arange(self["n_sample"]) / T
        print(self["f"])
        self["chan1_f"] = fft(self["chan1_t"])
        self["chan2_f"] = fft(self["chan2_t"])

    def ifft(self):
        """
        Compute inverse FFT to reconstruct time-domain signals.

        Notes
        -----
        The original code checks ``if "chan1_f":`` which is always True for
        non-empty strings. This docstring documents intent without changing
        runtime behavior.
        """
        if "chan1_f":
            self["chan1_t"] = ifft(self["chan1_f"])
            self["chan2_t"] = ifft(self["chan2_f"])

    def fft_filter(self, fmin=None, fmax=None):
        """
        Apply a simple band-pass filter in the frequency domain.

        Parameters
        ----------
        fmin : float, optional
            Lower cutoff frequency in Hz (default is 0).
        fmax : float, optional
            Upper cutoff frequency in Hz (default is infinity).

        Notes
        -----
        If FFT outputs are not present, :meth:`fft` is called automatically.
        """
        fmin = fmin or 0
        fmax = fmax or np.inf
        if "chan2_f" not in self:
            self.fft()
        I = np.where((self["f"] > fmin) & (self["f"] < fmax))
        self["chan1_f"][~I] *= 0
        self["chan2_f"][~I] *= 0
        self.ifft()

    def amp_freq(self, freq):
        """
        Estimate amplitude at a target frequency from the FFT.

        Parameters
        ----------
        freq : float
            Target frequency in Hz.

        Returns
        -------
        ndarray
            Estimated amplitude for channel 1. For stacked acquisitions, returns
            one value per acquisition.

        Notes
        -----
        The method selects frequency bins using :func:`numpy.isclose` with a
        relative tolerance of 0.1, then returns the maximum magnitude in the
        selected bins normalized by ``n_sample``.
        """
        I = np.isclose(self.f, freq, rtol=0.1)
        return np.abs(self["chan1_f"][:, I]).max(axis=1) / self["n_sample"]
