"""
BIMMS I/O file handling utilities.

This module provides small helper functions used throughout BIMMS for:

- Checking iterability of objects (with special handling for strings).
- Manipulating filenames (e.g., removing extensions).
- Creating folders with controlled access rights.
- Saving/loading JSON files with support for NumPy scalar/array types.

The JSON utilities are designed for open-science data sharing: they produce
portable, human-readable artifacts that can be stored alongside experimental
results and hardware configurations.

Authors
-------
Florian Kolbl, Thomas Couppey, Louis Regnacq

Copyright
---------
(c) ETIS - University Cergy-Pontoise - CNRS
"""
import json
import os

import numpy as np



#################
# Miscalleneous #
#################
def is_iterable(some_stuff):
    """
    Check whether an object is iterable (excluding strings).

    Parameters
    ----------
    some_stuff : object
        Object to test.

    Returns
    -------
    bool
        False for numbers and strings; True for iterables such as lists, tuples,
        dicts, generators, and NumPy arrays.

    Notes
    -----
    The implementation attempts to create a generator over the input. This is a
    pragmatic check used by BIMMS I/O helpers and is not intended to be a strict
    iterator protocol validator.
    """
    try:
        _ = (a for a in some_stuff)
        if isinstance(some_stuff, str):
            flag = False
        else:
            flag = True
    except TypeError:
        flag = False
    return flag


def rmv_ext(fname):
    """
    Remove a filename extension.

    Parameters
    ----------
    fname : str
        File name, with or without extension.

    Returns
    -------
    str
        File name without extension. If ``fname`` is not a string, it is returned
        unchanged.
    """
    if isinstance(fname, str):
        i = fname.rfind(".")
        if i > 0:
            fname = fname[:i]
    return fname


#####################################
## Folder and archive related code ##
#####################################
def create_folder(foldername, access_rights=0o755):
    """
    Create a folder with controlled access rights.

    Parameters
    ----------
    foldername : str
        Name of the folder to create.
    access_rights : int, optional
        Unix-like permissions (default is ``0o755``).

    Notes
    -----
    If the folder already exists, a warning is printed and the function returns
    without raising.
    """
    try:
        os.mkdir(foldername, access_rights)
    except OSError:
        print("WARNING:", 
            "Creation of the directory %s failed, this folder may already exist"
            % foldername
        )


#######################
## JSON related code ##
#######################
def check_json_fname(fname):
    """
    Ensure a JSON filename has the ``.json`` extension and exists on disk.

    Parameters
    ----------
    fname : str
        File name or path.

    Returns
    -------
    str
        File name guaranteed to end with ``.json``.

    Notes
    -----
    This function mirrors the current behavior of BIMMS: if the file does not
    exist, an error message is printed and the process exits.

    Warnings
    --------
    Because this function calls :func:`exit` on missing files, it is intended for
    CLI / script usage rather than library-grade error handling.
    """
    if fname[-5:] != ".json":
        fname += ".json"
    if os.path.isfile(fname):
        return fname
    else:
        print("ERROR:", fname + " not found cannot be load")
        exit()


def json_dump(results, filename):
    """
    Save Python objects as a JSON file with NumPy support.

    Parameters
    ----------
    results : object
        Object to serialize. Must be JSON-serializable, potentially including
        NumPy scalars/arrays which are handled by :class:`BIMMS_Encoder`.
    filename : str
        Output filename.

    Returns
    -------
    None
        Writes ``filename`` to disk.

    See Also
    --------
    json_load, BIMMS_Encoder
    """
    with open(filename, "w") as file_to_save:
        json.dump(results, file_to_save, cls=BIMMS_Encoder)


def json_load(filename):
    """
    Load Python objects from a JSON file.

    Parameters
    ----------
    filename : str
        Name of the file where results are stored. The ``.json`` extension is
        added if missing.

    Returns
    -------
    dict
        Deserialized JSON content.

    See Also
    --------
    check_json_fname, json_dump
    """
    with open(check_json_fname(filename), "r") as file_to_read:
        results = json.load(file_to_read)
    return results


class BIMMS_Encoder(json.JSONEncoder):
    """
    JSON encoder that converts common NumPy types into built-in Python types.

    This prevents ``TypeError: Object of type ... is not JSON serializable`` when
    saving results that include:

    - ``numpy.integer`` -> ``int``
    - ``numpy.floating`` -> ``float``
    - ``numpy.ndarray`` -> ``list`` via ``tolist()``

    Notes
    -----
    All other objects are delegated to :class:`json.JSONEncoder`.

    References
    ----------
    The approach is commonly used in Python serialization examples and was
    adopted in BIMMS to keep JSON exports lightweight and interoperable.
    """

    def default(self, obj):
        # If the object is a numpy array
        if isinstance(obj, np.integer):
            result = int(obj)
        elif isinstance(obj, np.floating):
            result = float(obj)
        elif isinstance(obj, np.ndarray):
            result = obj.tolist()
        else:
            # Let the base class Encoder handle the object
            result = json.JSONEncoder.default(self, obj)
        return result
