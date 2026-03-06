Installation
============

The :mod:`bimms` package is distributed on PyPI and can be installed with
``pip``. The current PyPI project metadata identifies BIMMS as a Python API for
the BIMMS platform and reports support for Python ``>=3.6``. [1]_

Prerequisites
-------------

Before installing or using the Python package, make sure the host system is
prepared for communication with the underlying measurement hardware.

In particular, the project repository states that Digilent WaveForms must be
installed before using the BIMMS Python API. This requirement is important
because BIMMS relies on the Analog Discovery 2 ecosystem for data acquisition
and waveform generation. [2]_

A practical first-install checklist is therefore:

* install a supported Python environment,
* install Digilent WaveForms on the host machine,
* connect and verify access to the measurement hardware,
* install the :mod:`bimms` Python package,
* run a minimal acquisition script.

The PyPI metadata lists operating-system classifiers for Linux, macOS, and
Windows, which is consistent with cross-platform scientific Python usage, though
the actual success of a setup naturally also depends on hardware drivers and the
third-party acquisition software stack. [1]_

Install from PyPI
-----------------

For a standard installation, use:

.. code-block:: bash

   pip install bimms

This is the recommended first step for most users because it installs the
published package directly from PyPI. [1]_

It is often preferable to work inside a dedicated virtual environment. For
example:

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install bimms

On Windows, activate the environment with the appropriate shell-specific command
before running ``pip install bimms``.

Optional scientific Python environment
--------------------------------------

Although BIMMS itself is installed through PyPI, many practical workflows also
use the usual scientific Python stack for plotting and analysis, for example
NumPy and Matplotlib. This is visible in the example scripts distributed with
the project, which import :mod:`numpy` and :mod:`matplotlib.pyplot` to inspect
and visualize impedance spectra. [3]_ [4]_

A typical working environment for exploratory use therefore includes:

* NumPy for numerical manipulation,
* Matplotlib for plotting spectra and trends,
* SciPy where advanced numerical post-processing is required.

Repository README information
-----------------------------

The project repository indicates that BIMMS was developed for Python 3 and lists
the following required or associated packages in the README:

* ``numpy``
* ``scipy``
* ``matplotlib``
* ``andi-py``

The same README also reiterates that WaveForms must be installed before the
BIMMS Python API is used. [2]_

Because packaging and dependency declarations can evolve over time, it is good
practice to consult both the repository metadata and the installed environment
when preparing a reproducible setup. [1]_ [2]_

Verify the installation
-----------------------

After installation, check that the package can be imported:

.. code-block:: bash

   python -c "import bimms; print('BIMMS import OK')"

If the import succeeds, the next step is to verify the complete acquisition
stack in a real measurement context.

A minimal functional workflow is:

#. instantiate the BIMMS controller,
#. choose the excitation mode,
#. configure wiring and gain parameters,
#. define an EIS measurement,
#. run the acquisition,
#. inspect the returned arrays.

For example, the provided usage scripts configure either galvanostatic EIS or
potentiostatic EIS, set gain values for current and voltage readout, define the
frequency range, and retrieve ``freq``, ``mag_Z``, and ``phase_Z`` from the
measurement result object. [3]_ [4]_

Example: potentiostatic EIS
---------------------------

The following shortened example shows the structure of a potentiostatic EIS
measurement session adapted from the project examples:

.. code-block:: python

   import bimms as bm

   bs = bm.BIMMS()

   bs.config.excitation_mode("P_EIS")
   bs.config.wire_mode("2_WIRE")
   bs.config.excitation_signaling_mode("SE")
   bs.config.excitation_coupling("DC")

   bs.config.IRO_gain(20)
   bs.config.VRO_gain(20)
   bs.config.V_amplitude = 100

   meas = bm.EIS(
       fmin=1e3,
       fmax=1e7,
       n_pts=101,
       settling_time=0.01,
       nperiods=8,
   )

   bs.attach_measure(meas)
   results = bs.measure()

This pattern is directly aligned with the distributed example scripts. [3]_ [4]_

Troubleshooting
---------------

If the package installs but acquisition does not work as expected, the most
common first points to check are:

* whether Digilent WaveForms is installed correctly,
* whether the Analog Discovery 2 and any BIMMS-specific hardware are connected
  and recognized by the host system,
* whether the Python environment contains the expected scientific dependencies,
* whether the selected measurement mode matches the physical wiring,
* whether gain and excitation settings are within the intended operating range.

If Sphinx documentation builds are part of your development workflow, remember
that autodoc imports Python modules during the build. In practice, import-time
hardware calls, plotting backends, or optional dependencies can therefore show
up as documentation build errors even when the package itself is otherwise
usable.

Development installation
------------------------

If you are working from the source repository rather than the PyPI release,
installing in editable mode is convenient:

.. code-block:: bash

   pip install -e .

This approach is especially useful when developing the package, editing
docstrings, or building the Sphinx documentation locally.

Next steps
----------

Once installation is complete, a good next step is to read the overview page and
then explore the API reference for the :mod:`bimms.system`,
:mod:`bimms.measure`, and :mod:`bimms.results` modules. A later section of this
documentation will also describe how to build a BIMMS system from the open
hardware resources and embedded firmware associated with the project.

References
----------

.. [1] PyPI project page for ``bimms``. :contentReference[oaicite:5]{index=5}

.. [2] BIMMS repository README and installation notes. :contentReference[oaicite:6]{index=6}

.. [3] Example script: galvanostatic EIS usage. :contentReference[oaicite:7]{index=7}

.. [4] Example script: potentiostatic EIS usage. :contentReference[oaicite:8]{index=8}