Overview
========

BIMMS is a Python interface and instrumentation framework for bio-impedance
measurements and related electrochemical characterization workflows. It is
designed for biological tissue and electrode--tissue interface experiments, with
an emphasis on open hardware, portability, and reproducible measurement control.
The associated HardwareX publication describes BIMMS as a low-cost, compact,
open-source, USB-controlled platform for biological tissue and electrode--tissue
interface electrical measurements. It supports potentiostatic and galvanostatic
electrical impedance spectroscopy (EIS) up to 10 MHz, as well as cyclic
voltammetry, with voltage compliance of ±8 V and currents up to 2.4 mA while
respecting tissue-safety constraints. The acquisition and generation backbone is
based on the Digilent Analog Discovery 2 platform. [1]_

What BIMMS provides
-------------------

At the software level, the :mod:`bimms` package provides a high-level Python API
to configure the instrument, define measurement procedures, launch acquisitions,
and collect results in a programmatic workflow suitable for research code,
automation scripts, and data analysis pipelines.

At a practical level, BIMMS is intended to support tasks such as:

* electrical impedance spectroscopy on biological tissues,
* characterization of electrode--electrolyte or electrode--tissue interfaces,
* potentiostatic and galvanostatic interrogation strategies,
* multi-point measurement configurations, including 2-wire and 4-wire modes,
* electrochemical protocols such as cyclic voltammetry,
* post-processing and visualization in a standard scientific Python workflow.

The HardwareX article reports measurements in biologically relevant contexts,
including implanted neural stimulation electrodes and ex-vivo calf brain,
illustrating the intended application domain of the platform. [1]_

Measurement configurations
--------------------------

BIMMS is designed to operate with several electrode connection schemes depending
on the target experiment and the quantity of interest. In routine use, users may
encounter:

* 2-point measurements, where excitation and sensing share the same electrode
  pair,
* 3-electrode electrochemical configurations, typically involving working,
  reference, and counter electrodes,
* 4-point (tetrapolar) measurements, where current injection and voltage
  sensing are separated in order to reduce electrode-interface contributions to
  the measured impedance.

This flexibility is particularly important in bio-impedance and interface
characterization, where the optimal connection strategy depends on whether the
goal is to quantify bulk tissue properties, interface effects, or the global
response of the system under test. The underlying BIMMS hardware and software
stack were explicitly developed to address biological tissue and
electrode--tissue interface measurements in this broader sense. [1]_

Typical software workflow
-------------------------

A typical BIMMS session follows a small number of conceptual steps:

#. instantiate a :class:`bimms.system.BIMMS.BIMMS` controller,
#. configure the hardware and acquisition mode,
#. define a measurement object,
#. attach the measurement to the BIMMS controller,
#. run the acquisition,
#. inspect or post-process the returned results.

The example scripts distributed with the project illustrate this workflow for
both galvanostatic and potentiostatic EIS. In the galvanostatic example, the
excitation mode is configured as ``"G_EIS"`` and a current amplitude is set
before launching an :class:`bimms.measure.Measure.EIS` sweep. In the
potentiostatic example, the excitation mode is configured as ``"P_EIS"`` and a
voltage amplitude is set instead. In both cases, the returned result structure
contains at least frequency, impedance magnitude, and impedance phase, which are
then plotted in a standard scientific Python workflow. [2]_ [3]_

A minimal conceptual example is shown below:

.. code-block:: python

   import bimms as bm

   bs = bm.BIMMS()
   bs.config.excitation_mode("P_EIS")
   bs.config.wire_mode("2_WIRE")

   meas = bm.EIS(fmin=1e3, fmax=1e7, n_pts=101, settling_time=0.01, nperiods=8)
   bs.attach_measure(meas)
   results = bs.measure()

   freq = results["freq"]
   mag_z = results["mag_Z"]
   phase_z = results["phase_Z"]

The exact configuration parameters depend on the selected measurement mode,
electrode topology, gain settings, and excitation strategy.

Package structure
-----------------

The package is organized into several subpackages with distinct roles:

``bimms.system``
   Core system control, hardware abstraction, configuration primitives, and
   calibration-related system objects.

``bimms.measure``
   Measurement definitions and acquisition procedures.

``bimms.results``
   Result containers and related output handling.

``bimms.backend``
   Lower-level support code, shared classes, and file handling utilities.

``bimms.utils``
   Utility functions, constants, configuration helpers, and post-processing
   support.

``bimms.calibration``
   Calibration-related classes and scaffolding for measurement correction and
   calibration metadata management.

This documentation starts with installation and package overview, then provides
an API reference generated from the Python docstrings.

Research and citation
---------------------

If you use BIMMS in academic work, the associated HardwareX publication is the
primary reference because it documents the design objectives, hardware context,
measurement modes, validation strategy, and representative use cases of the
platform. [1]_

References
----------

.. [1] L. Regnacq, Y. Bornat, O. Romain, and F. Kölbl,
   *BIMMS: A versatile and portable system for biological tissue and
   electrode-tissue interface electrical characterization*,
   HardwareX, 2023. DOI: 10.1016/j.ohx.2022.e00387.
   Available from the publisher's article page.

.. [2] Example script: galvanostatic EIS workflow. :contentReference[oaicite:3]{index=3}

.. [3] Example script: potentiostatic EIS workflow. :contentReference[oaicite:4]{index=4}