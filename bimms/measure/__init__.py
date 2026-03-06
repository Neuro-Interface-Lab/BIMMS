"""BIMMS measurement subpackage.

This subpackage contains measurement *recipes* executed by a BIMMS system.

A measurement in BIMMS is represented as a subclass of
:class:`~bimms.measure.Measure.Measure` and is typically run against a
:class:`~bimms.system.BIMMScalibration.BIMMScalibration` context (which bundles
hardware handles, configuration, and calibration constants).

The design goal is to provide reusable, serializable, open-science-friendly
measurement definitions:

- Parameter containers are regular Python attributes that can be exported via
  :meth:`bimms.backend.BIMMS_Class.BIMMS_class.save`.
- Measurement methods return result objects (e.g., Bode/EIS results) that can be
  post-processed and plotted.

Notes
-----
The original file contained two top-level string literals. They are preserved as
top-level literals to avoid any behavioral change while improving their content.
"""
"""measurement library (subpackage marker)."""
