"""BIMMS calibration subpackage.

This subpackage contains calibration-related primitives used by BIMMS to correct
systematic measurement errors and to attach calibration metadata to acquisitions.

The calibration workflow in BIMMS typically involves:

1. Selecting a calibrator implementation (subclass of :class:`~bimms.calibration.calibration.Calibrator`).
2. Running the calibrator against a :class:`~bimms.system.BIMMScalibration.BIMMScalibration` context.
3. Persisting calibration parameters through the generic BIMMS JSON
   serialization mechanisms (see :class:`bimms.backend.BIMMS_Class.BIMMS_class`).

The current repository snapshot contains a minimal scaffold (base class and an
``Offsets`` parameter container) that is expected to be extended with concrete
calibration routines.

Notes
-----
The strings in this file are intentionally kept as top-level literals to avoid
any behavioral changes relative to the original code while improving the
documentation content.
"""
"""calibration library (subpackage marker)."""