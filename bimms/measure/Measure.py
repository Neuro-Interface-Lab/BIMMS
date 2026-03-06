"""Measurement primitives for BIMMS.

This module defines the measurement API and a set of concrete measurement
implementations for the BIMMS platform.

In BIMMS, a *measurement* encapsulates a reproducible acquisition procedure that
can be executed on a configured system and returns structured results. The
central abstraction is :class:`Measure`, which is an abstract base class
inheriting from :class:`~bimms.backend.BIMMS_Class.BIMMS_class` to support JSON
serialization (open-science sharing and reproducibility).

The concrete measurements implemented here include:

- :class:`EIS`: Electrical impedance spectroscopy over a frequency sweep.
- :class:`Bode`: Magnitude/phase sweep (network-analyzer style).
- :class:`FrequentialSingleFrequency`: Single-frequency gain/phase point.
- :class:`TemporalSingleFrequency`: Time-domain acquisition at a given frequency
  (with either a generated sine or a user-provided custom waveform).
- :class:`Offset`: Offset (DC) estimation of acquisition channels.

All measurement routines operate on a
:class:`~bimms.system.BIMMScalibration.BIMMScalibration` instance, referred to as
``BS`` in the source.

Open Science & Reproducibility
------------------------------
For each measurement, it is good practice to record:

- The BIMMS hardware revision and analog front-end configuration.
- The firmware/driver versions (AD2, STM32, etc., as applicable).
- Calibration state (e.g., offsets) and the date/time of calibration.
- The exact measurement parameters (frequency, amplitude, sweep settings).
- Environmental and sample metadata (temperature, electrolyte composition, etc.).

Notes
-----
This file intentionally documents known quirks in the current implementation
(e.g., the `set_parameters` method uses `==` instead of assignment) without
modifying any executable code, per project constraints.

Authors
-------
Florian Kolbl, Thomas Couppey, Louis Regnacq
"""

import numpy as np

from ..backend.BIMMS_Class import BIMMS_class, abstractmethod
from ..system.BIMMScalibration import BIMMScalibration
from ..utils import constants as BIMMScst
from ..results.Results import temporal_results, bode_results


class Measure(BIMMS_class):
    """
    Abstract base class for BIMMS measurements.

    Subclasses define a reproducible acquisition protocol via :meth:`measure`.

    Parameters
    ----------
    ID : int, optional
        Identifier for the measurement instance (default is 0). This can be used
        to track multiple measurement steps in a pipeline.

    Attributes
    ----------
    ID : int
        Measurement identifier.

    See Also
    --------
    bimms.system.BIMMScalibration.BIMMScalibration
        System context passed to :meth:`measure`.
    """

    @abstractmethod
    def __init__(self, ID=0):
        """
        Initialize the measurement object.

        Parameters
        ----------
        ID : int, optional
            Measurement identifier.
        """
        super().__init__()
        self.ID = ID

    def set_parameters(self, **kawrgs):
        """
        Set measurement parameters from keyword arguments.

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
        ``dict``). This docstring documents intended behavior without changing
        runtime behavior.
        """
        for key in kawrgs:
            if key in self.__dict__:
                self.__dict__[key] == kawrgs[dict]

    def get_parameters(self):
        """
        Return current measurement parameters.

        Returns
        -------
        dict
            The measurement instance attribute dictionary (``self.__dict__``).

        Notes
        -----
        Returning ``self.__dict__`` provides a direct view of the measurement
        state. Downstream code should avoid mutating it in-place unless intended.
        """
        return self.__dict__

    def measure(self, BS: BIMMScalibration):
        """
        Execute the measurement (to be implemented by subclasses).

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            Configured BIMMS system context providing hardware access, calibration
            data, and acquisition settings.

        Returns
        -------
        object
            Concrete implementations return either a results object (e.g.,
            :class:`~bimms.results.Results.bode_results`) or a plain dict for
            lightweight outputs.

        Notes
        -----
        Implementations generally interact with ``BS.ad2`` (Analog Discovery 2)
        helpers and BIMMS acquisition utilities.
        """
        pass


class EIS(Measure):
    """
    Electrical impedance spectroscopy (EIS) measurement over a frequency sweep.

    This measurement performs a frequency sweep using the AD2 network-analyzer
    configuration and returns a :class:`~bimms.results.Results.bode_results`
    instance, with additional EIS-specific processing applied via
    :meth:`bode_results.EIS`.

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
        Number of excitation periods per frequency point (default is 8).
    ID : int, optional
        Measurement identifier (default is 0).

    Returns
    -------
    bimms.results.Results.bode_results
        Processed Bode/EIS results object.
    """

    def __init__(
        self, fmin=1e3, fmax=1e7, n_pts=101, settling_time=0.001, nperiods=8, ID=0
    ):
        super().__init__(ID=ID)
        self.fmin = fmin
        self.fmax = fmax
        self.n_pts = n_pts
        self.settling_time = settling_time
        self.nperiods = nperiods

    def set_fmin(self, f):
        """Set the minimum frequency (Hz).

        Parameters
        ----------
        f: float
            minimum frequency of the measurement in Hz
        """
        self.set_parameters(fmin=f)

    def set_fmax(self, f):
        """Set the maximum frequency (Hz).

        Parameters
        ----------
        f: float
            maximum frequency of the measurement in Hz
        """
        self.set_parameters(fmax=f)

    def set_n_pts(self, N):
        """Set the number of frequency points.
        
        Parameters
        ----------
        n: int
            number of measurements points (or frequencies between fmin and fmax)
        """
        self.set_parameters(n_pts=N)

    def set_settling_time(self, t):
        """Set the settling time (s).
        
        Parameters
        ----------
        n: int
            settling time of the measure at a given frequency
        """
        self.set_parameters(settling_time=t)

    def set_nperiods(self, N):
        """Set the number of periods per frequency.
        
        Parameters
        ----------
        N: int
            number of periods at a given frequency for the measurement
        """
        self.set_parameters(nperiods=N)

    def measure(self, BS: BIMMScalibration):
        """
        Run the EIS sweep and return processed results.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Returns
        -------
        bimms.results.Results.bode_results
            Results object containing frequency vector and raw magnitude/phase,
            with EIS post-processing applied.

        Notes
        -----
        The raw quantities returned by the AD2 helper are stored under keys:
        ``mag_ch1_raw``, ``mag_raw``, ``phase_raw``.
        """
        BS.ad2.configure_network_analyser()  # need to be checked
        freq, gain_mes, phase_mes, gain_ch1 = BS.ad2.bode_measurement(
            self.fmin,
            self.fmax,
            n_points=self.n_pts,
            dB=False,
            offset=BS.awg_offset,
            deg=True,
            amp=BS.awg_amp,
            settling_time=self.settling_time,
            Nperiods=self.nperiods,
            verbose=BS.verbose,
        )
        bode_data = {
            "freq": freq,
            "mag_ch1_raw": gain_ch1,
            "mag_raw": gain_mes,
            "phase_raw": phase_mes,
        }
        results = bode_results(BS, bode_data)
        results.EIS()
        return results


class TemporalSingleFrequency(Measure):
    """
    Time-domain acquisition at a single frequency.

    This measurement generates a sine waveform (or uses a user-provided custom
    waveform) and records time-domain samples from two input channels.

    Parameters
    ----------
    freq : float, optional
        Excitation frequency in Hz (default is 1e3). Ignored if a custom waveform
        is provided via :meth:`set_signal`.
    phase : float, optional
        Phase in degrees for the sine generator (default is 0).
    symmetry : float, optional
        Waveform symmetry in percent (default is 50).
    nperiods : int, optional
        Number of periods in the acquisition buffer (default is 8).
    delay : float, optional
        Trigger delay (units as expected by :meth:`BS.Set_AWG_trigger`; default is 0).
    ID : int, optional
        Measurement identifier (default is 0).

    Attributes
    ----------
    signal : array_like or None
        Custom waveform samples (if provided).
    fs : float or None
        Sampling frequency associated with ``signal`` (if provided) or computed
        for sine generation.

    Returns
    -------
    bimms.results.Results.temporal_results
        Results object holding time vector and recorded channels.
    """

    def __init__(self, freq=1e3, phase=0, symmetry=50, nperiods=8, delay=0, ID=0):
        super().__init__(ID=ID)
        self.freq = freq
        self.phase = phase
        self.symmetry = symmetry
        self.nperiods = nperiods
        self.delay = delay

        self.signal = None
        self.fs = None

    @property
    def is_custom(self):
        """
        Whether a custom waveform is configured.

        Returns
        -------
        bool
            True if both ``signal`` and ``fs`` are defined; False otherwise.
        """
        return not(self.signal is None or self.fs is None)

    def set_signal(self, sig, fs):
        """
        Set a custom excitation waveform.

        Parameters
        ----------
        sig : array_like
            Samples of the excitation waveform.
        fs : float
            Sampling frequency in Hz for ``sig``.

        Notes
        -----
        When a custom waveform is set, :meth:`measure` uses ``BS.AWG_custom``.
        """
        self.signal=sig
        self.fs=fs

    def set_freq(self, f):
        """Set excitation frequency (Hz) for sine generation."""
        self.set_parameters(freq=f)

    def set_phase(self, phase):
        """Set excitation phase (degrees) for sine generation."""
        self.set_parameters(phase=phase)

    def set_symmetry(self, symmetry):
        """Set waveform symmetry (%) for sine generation."""
        self.set_parameters(symmetry=symmetry)

    def set_Nperiod(self, N):
        """Set number of periods in the acquisition buffer."""
        self.set_parameters(nperiods=N)

    def set_delay(self, delay):
        """Set trigger delay."""
        self.set_parameters(delay=delay)

    def measure(self, BS: BIMMScalibration):
        """
        Run the time-domain acquisition.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Returns
        -------
        bimms.results.Results.temporal_results
            Time-domain results.

        Notes
        -----
        The method computes an internal sampling frequency ``fs`` based on the
        buffer size and requested number of periods. If the resulting ``fs`` is
        above ``BS.AD2_input_Fs_max``, it decreases the number of points until
        the constraint is satisfied.
        """
        # set the generators
        Fs_max = BS.AD2_input_Fs_max
        Npts = BS.AD2_input_buffer_size
        if self.is_custom:
            if self.fs > Fs_max:
                print("Warning: fs is bigger than Fs_max")
            else:
                BS.AWG_custom(self.fs, self.signal)
        else:
            BS.AWG_sine(
                freq=self.freq,
                amp=BS.awg_amp,
                activate=False,
                offset=BS.awg_offset,
                phase=self.phase,
                symmetry=self.symmetry,
            )
            self.fs = self.freq * Npts / self.nperiods

            while self.fs > Fs_max:
                Npts -= 1
                self.fs = self.freq * Npts / self.nperiods
        # set the triger to triger source
        BS.Set_AWG_trigger(delay=self.delay)

        # set acquisition
        t = BS.set_acquistion(self.fs, Npts)

        # perform the generation/acquisition
        BS.AWG_enable(True)
        chan1, chan2 = BS.get_input_data()
        BS.AWG_enable(False)
        data = {"t": t, "chan1": chan1, "chan2": chan2}
        results = temporal_results(BS, data)
        return results


class Offset(Measure):
    """
    Estimate acquisition channel DC offsets.

    The procedure runs a dummy waveform with zero amplitude, acquires samples,
    and estimates the mean value (optionally averaged across multiple repeats).
    The offsets are then mapped to the calibration domain via
    :meth:`BS.Scope2calibration`.

    Parameters
    ----------
    acq_duration : float, optional
        Acquisition duration in seconds (default is 1).
    Navg : int, optional
        Number of acquisitions to average (default is 0; see Notes).
    ID : int, optional
        Measurement identifier (default is 0).

    Returns
    -------
    dict
        Dictionary with keys ``"ch1_offset"`` and ``"ch2_offset"`` (units depend
        on :meth:`BS.Scope2calibration`).

    Notes
    -----
    - The loop is ``for n in range(self.Navg)``. If ``Navg`` is 0, the loop body
      is skipped and later indexing ``ch1_offset[0]`` will raise an error. This
      docstring documents expected intent (Navg >= 1) without modifying code.
    """

    def __init__(self, acq_duration=1, Navg=0, ID=0):
        super().__init__(ID=ID)
        self.acq_duration = acq_duration
        self.Navg = Navg

    def set_acq_duration(self, acq_duration):
        """Set acquisition duration (s)."""
        self.set_parameters(acq_duration=acq_duration)

    def set_Navg(self, Navg):
        """Set number of averages (integer)."""
        self.set_parameters(Navg=Navg)

    def measure(self, BS: BIMMScalibration):
        """
        Acquire and compute DC offsets for both channels.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Returns
        -------
        dict
            Offsets for channel 1 and 2 after calibration mapping.
        """
        BS.AWG_sine(freq=1e3, amp=0, activate=True)  # Dummy sine waveform
        BS.Set_AUTO_trigger()

        Npts = BS.AD2_input_buffer_size
        fs = Npts / self.acq_duration
        t = BS.set_acquistion(fs=fs, size=Npts)
        ch1_offset = []
        ch2_offset = []
        if BS.verbose:
            print("Measuring Offset...")
        for n in range(self.Navg):
            ch1, ch2 = BS.get_input_data()
            ch1_offset.append(np.mean(ch1))
            ch2_offset.append(np.mean(ch2))

        if BS.verbose:
            print("Done!")
        if self.Navg > 1:
            ch1_offset = np.mean(ch1_offset)
            ch2_offset = np.mean(ch2_offset)
        else:
            ch1_offset = ch1_offset[0]
            ch2_offset = ch2_offset[0]

        ch1_offset, ch2_offset = BS.Scope2calibration(ch1_offset, ch2_offset, [0])

        results = {"ch1_offset": ch1_offset, "ch2_offset": ch2_offset}
        return results


class FrequentialSingleFrequency(Measure):
    """
    Single-frequency magnitude and phase measurement.

    This measurement configures the AD2 network-analyzer mode once per BIMMS
    system instance (tracked via a cached BIMMS ID), then queries a single
    frequency point.

    Parameters
    ----------
    freq : float, optional
        Frequency in Hz (default is 1e3).
    settling_time : float, optional
        Settling time in seconds (default is 0.001 s).
    nperiods : int, optional
        Number of periods used by the network-analyzer acquisition (default is 8).
    ID : int, optional
        Measurement identifier (default is 0).

    Returns
    -------
    bimms.results.Results.bode_results
        Results object with single-point arrays for frequency, magnitude, and phase.
    """

    def __init__(self, freq=1e3, settling_time=0.001, nperiods=8, ID=0):
        super().__init__(ID=ID)
        self.freq = freq
        self.settling_time = settling_time
        self.nperiods = nperiods

        self.__setup_BIMMS_ID = None

    def set_freq(self, f):
        """Set the measurement frequency (Hz)."""
        self.set_parameters(freq=f)

    def set_settling_time(self, t):
        """Set settling time (s)."""
        self.set_parameters(settling_time=t)

    def set_nperiods(self, N):
        """Set number of periods."""
        self.set_parameters(nperiods=N)

    def setup(self, BS: BIMMScalibration):
        """
        Configure the network analyzer if needed.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Notes
        -----
        The method configures the AD2 network analyzer only when the cached BIMMS
        ID differs from ``BS.ID``.
        """
        if self.__setup_BIMMS_ID != BS.ID:
            BS.ad2.configure_network_analyser(BS.awg_amp,BS.awg_offset,self.nperiods)
            self.__setup_BIMMS_ID = BS.ID
            print("setup ok")

    def measure(self, BS: BIMMScalibration):
        """
        Measure magnitude/phase at a single frequency point.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Returns
        -------
        bimms.results.Results.bode_results
            Results object wrapping the raw magnitude and phase values as arrays.
        """
        self.setup(BS=BS)
        mag_raw, phase_raw, mag_ch1_raw = BS.ad2.single_frequency_gain_phase(
            frequency=self.freq,
            dB = False,
            deg = True,
            settling_time=self.settling_time,
        )
        bode_data = {
            "freq": np.array([self.freq]),
            "mag_ch1_raw": np.array([mag_ch1_raw]),
            "mag_raw": np.array([mag_raw]),
            "phase_raw": np.array([phase_raw]),
        }
        results = bode_results(BS, bode_data)
        return results


class Bode(Measure):
    """
    Bode magnitude/phase sweep measurement.

    This measurement performs a frequency sweep in network-analyzer mode and
    returns a :class:`~bimms.results.Results.bode_results` object.

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
        Number of excitation periods per frequency point (default is 8).
    ID : int, optional
        Measurement identifier (default is 0).

    Returns
    -------
    bimms.results.Results.bode_results
        Results object containing frequency vector and raw magnitude/phase.
    """

    def __init__(
        self, fmin=1e3, fmax=1e7, n_pts=101, settling_time=0.001, nperiods=8, ID=0
    ):
        super().__init__(ID=ID)
        self.fmin = fmin
        self.fmax = fmax
        self.n_pts = n_pts
        self.settling_time = settling_time
        self.nperiods = nperiods

    def set_fmin(self, f):
        """Set the minimum frequency (Hz)."""
        self.set_parameters(fmin=f)

    def set_fmax(self, f):
        """Set the maximum frequency (Hz)."""
        self.set_parameters(fmax=f)

    def set_n_pts(self, N):
        """Set the number of frequency points."""
        self.set_parameters(n_pts=N)

    def set_settling_time(self, t):
        """Set the settling time (s)."""
        self.set_parameters(settling_time=t)

    def set_nperiods(self, N):
        """Set the number of periods per frequency."""
        self.set_parameters(nperiods=N)

    def measure(self, BS: BIMMScalibration):
        """
        Run the Bode sweep and return results.

        Parameters
        ----------
        BS : bimms.system.BIMMScalibration.BIMMScalibration
            BIMMS system context.

        Returns
        -------
        bimms.results.Results.bode_results
            Results object containing frequency vector and raw magnitude/phase.

        Notes
        -----
        The AD2 helper returns raw quantities (magnitudes and phase) that are
        stored under keys: ``mag_ch1_raw``, ``mag_raw``, ``phase_raw``.
        """
        BS.ad2.configure_network_analyser()  # need to be checked
        freq, mag_raw, phase_raw, mag_ch1_raw = BS.ad2.bode_measurement(
            self.fmin,
            self.fmax,
            n_points=self.n_pts,
            dB=False,
            offset=BS.awg_offset,
            deg=True,
            amp=BS.awg_amp,
            settling_time=self.settling_time,
            Nperiods=self.nperiods,
            verbose=BS.verbose,
        )

        bode_data = {
            "freq": freq,
            "mag_ch1_raw": mag_ch1_raw,
            "mag_raw": mag_raw,
            "phase_raw": phase_raw,
        }
        results = bode_results(BS, bode_data)
        return results
