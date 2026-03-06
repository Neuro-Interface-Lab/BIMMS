"""
Access and modify BIMMS Parameters.

This module defines the :class:`~bimms.backend.BIMMS_class.BIMMS_class` abstract base
class and helper utilities used across the BIMMS Python package to:

- Identify BIMMS objects and serialized BIMMS dictionaries.
- Serialize and deserialize BIMMS objects to/from JSON-compatible dictionaries.
- Provide generic context backup/restore via :meth:`BIMMS_class.save` and
  :meth:`BIMMS_class.load`.

The serialization model is designed for open-science workflows where experimental
contexts (hardware configuration, acquisition parameters, calibration state, etc.)
must be reproducibly exported and re-imported.

Notes
-----
* This file uses JSON I/O helpers from :mod:`bimms.backend.file_handler`.
* Object reconstruction in :func:`load_any` uses ``eval`` on the ``bimms`` module
  namespace. Only load data you trust.

Authors
-------
Florian Kolbl, Louis Regnacq, Thomas Couppey

"""
from abc import ABCMeta, abstractmethod
from copy import deepcopy

# sys used in an eval
import sys
import numpy as np
from numpy import iterable

from .file_handler import json_dump, json_load


debug = False
########################################
#           check object               #
########################################


def is_BIMMS_class(x):
    """
    Test whether an object is an instance of :class:`BIMMS_class`.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is an instance of :class:`BIMMS_class`, False otherwise.
    """
    return isinstance(x, BIMMS_class)


def is_BIMMS_class_list(x):
    """
    Test whether an iterable contains only :class:`BIMMS_class` instances.

    Parameters
    ----------
    x : object
        Object to test. If it is iterable, each element is checked.

    Returns
    -------
    bool
        True if ``x`` is iterable and every element is a :class:`BIMMS_class`
        instance. False otherwise.

    Notes
    -----
    Strings are considered iterable by NumPy; this function relies on
    :func:`numpy.iterable` and therefore treats strings as iterable. In BIMMS,
    lists/tuples/arrays are the intended use.
    """
    if iterable(x):
        for xi in x:
            if not is_BIMMS_class(xi):
                return False
        return True
    return False


def is_BIMMS_class_dict(x):
    """
    Test whether a dict contains only :class:`BIMMS_class` instances as values.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is a dict and every value is a :class:`BIMMS_class`
        instance. False otherwise.
    """
    if isinstance(x, dict):
        for xi in x.values():
            if not is_BIMMS_class(xi):
                return False
        return True
    return False


##########################################
#           check dictionaries           #
##########################################


def is_BIMMS_object_dict(x):
    """
    Test whether an object is a BIMMS serialized dictionary container.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is a BIMMS dict, a list of BIMMS dicts, or a dict of BIMMS
        dicts. False otherwise.

    See Also
    --------
    is_BIMMS_dict, is_BIMMS_dict_list, is_BIMMS_dict_dict
    """
    return is_BIMMS_dict(x) or is_BIMMS_dict_list(x) or is_BIMMS_dict_dict(x)


def is_BIMMS_dict(x):
    """
    Test whether an object is a BIMMS serialized dictionary.

    A BIMMS serialized dictionary is identified by the presence of the key
    ``"bimms_type"`` which stores the class name required for reconstruction.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is a dict with a ``"bimms_type"`` key, False otherwise.
    """
    if isinstance(x, dict):
        if "bimms_type" in x:
            return True
    return False


def is_BIMMS_dict_list(x):
    """
    Test whether an iterable is a list of BIMMS serialized dictionaries.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is iterable, non-empty, and every element satisfies
        :func:`is_BIMMS_dict`. False otherwise.
    """
    if iterable(x):
        if len(x) > 0:
            for xi in x:
                if not (is_BIMMS_dict(xi)):
                    return False
            return True
    return False


def is_BIMMS_dict_dict(x):
    """
    Test whether a dict is a mapping of BIMMS serialized dictionaries.

    Parameters
    ----------
    x : object
        Object to test.

    Returns
    -------
    bool
        True if ``x`` is a dict and every value satisfies :func:`is_BIMMS_dict`.
        False otherwise.
    """
    if isinstance(x, dict):
        for key in x:
            if not (is_BIMMS_dict(x[key])):
                return False
        return True
    return False


class BIMMS_class(metaclass=ABCMeta):
    """
    Abstract base class for BIMMS objects supporting JSON serialization.

    All BIMMS classes are expected to inherit from this base class to enable:

    - Recursive export of an object state to a JSON-compatible dictionary via
      :meth:`save`.
    - Recursive reconstruction (in-place) of an object state from a dictionary or
      JSON file via :meth:`load`.

    The pattern is intentionally lightweight: subclasses typically populate
    instance attributes in ``__init__`` and rely on the base class for
    persistence.

    Parameters
    ----------
    fixed_attr : bool, optional
        If True (default), only attributes already present on the instance will
        be loaded by :meth:`load`. If False, missing attributes in the serialized
        data may be created dynamically before loading.

    Attributes
    ----------
    __BIMMSObject__ : bool
        Internal flag marking the instance as a BIMMS object.
    verbose : bool
        Optional verbosity flag (subclasses may use it).
    bimms_type : str
        Name of the concrete class (used in serialization dictionaries).
    __fixed_attr : bool
        Controls attribute creation during loading.

    Notes
    -----
    * The base class stores ``bimms_type`` as ``self.__class__.__name__``.
    * When ``debug`` is True, object creation/destruction messages are printed.

    See Also
    --------
    load_any : Reconstruction helper for BIMMS dictionaries.
    """

    @abstractmethod
    def __init__(self,fixed_attr=True):
        """
        Initialize a BIMMS object.

        Parameters
        ----------
        fixed_attr : bool, optional
            See :class:`BIMMS_class` documentation.
        """
        self.__BIMMSObject__ = True
        self.verbose = True
        self.bimms_type = self.__class__.__name__
        self.__fixed_attr = fixed_attr
        if debug:
            print("DEBUG: ", self.bimms_type, " initialized")

    def __del__(self):
        """
        Destructor for BIMMS objects (debug only).

        Notes
        -----
        Python object finalization is not deterministic. This method is used
        solely for optional debug logging when ``debug`` is True.
        """
        if debug:
            print("DEBUG: ", self.bimms_type, " deleted")

    def save(self, save=False, fname="bimms_save.json", blacklist=[], **kwargs):
        """
        Export the object state as a JSON-compatible dictionary.

        The method recursively walks through ``self.__dict__`` and handles nested
        BIMMS objects, lists of BIMMS objects, and dicts of BIMMS objects by
        calling their respective :meth:`save` methods. Other values are deep-copied.

        Parameters
        ----------
        save : bool, optional
            If True, the exported dictionary is written to ``fname`` using
            :func:`bimms.backend.file_handler.json_dump`.
        fname : str, optional
            Output JSON filename (only used when ``save=True``).
        blacklist : list, optional
            List of attribute names (keys in ``self.__dict__``) to exclude from
            the export.
        **kwargs
            Forwarded to nested BIMMS objects' :meth:`save` calls.

        Returns
        -------
        dict
            JSON-compatible representation of the object.

        Notes
        -----
        ``blacklist`` defaults to an empty list in the original code; keep in
        mind that mutable defaults can be surprising in general Python usage.
        Here it is preserved to avoid any API change.
        """
        key_dic = {}
        for key in self.__dict__:
            if key not in blacklist:
                if is_BIMMS_class(self.__dict__[key]):
                    #print(key)
                    key_dic[key] = self.__dict__[key].save(**kwargs)
                elif is_BIMMS_class_list(self.__dict__[key]):
                    key_dic[key] = []
                    for i in range(len(self.__dict__[key])):
                        key_dic[key] += [self.__dict__[key][i].save(**kwargs)]
                elif is_BIMMS_class_dict(self.__dict__[key]):
                    key_dic[key] = {}
                    for i in self.__dict__[key]:
                        key_dic[key][i] = self.__dict__[key][i].save(**kwargs)
                else:
                    key_dic[key] = deepcopy(self.__dict__[key])
        if save:
            json_dump(key_dic, fname)
        return key_dic

    def load(self, data, blacklist={}, **kwargs):
        """
        Load an object state from a dictionary or a JSON file.

        Parameters
        ----------
        data : dict or str
            If a dict, it is interpreted as a BIMMS serialized dictionary.
            If a str, it is interpreted as a JSON filename and read with
            :func:`bimms.backend.file_handler.json_load`.
        blacklist : dict or list, optional
            Keys (attribute names) to exclude from loading. The original code
            uses a dict default; it is preserved to avoid any API change.
        **kwargs
            Forwarded to :func:`load_any` for nested object reconstruction.

        Returns
        -------
        None
            The object is modified in place.

        Notes
        -----
        - If ``self.__fixed_attr`` is False, missing attributes present in
          ``data`` may be created on the instance prior to assignment.
        - NumPy arrays are reconstructed when the current attribute value is an
          ``np.ndarray`` instance.
        """
        if isinstance(data, str):
            key_dic = json_load(data)
        else:
            key_dic = data
        if not self.__fixed_attr:
            for key in key_dic:
                if  key not in self.__dict__ and key not in blacklist:
                    self.__dict__[key] = None
        for key in self.__dict__:
            if key in key_dic and key not in blacklist:
                if is_BIMMS_object_dict(key_dic[key]):
                    self.__dict__[key] = load_any(key_dic[key], **kwargs)
                elif isinstance(self.__dict__[key], np.ndarray):
                    self.__dict__[key] = np.array(key_dic[key])
                elif isinstance(self.__dict__[key], dict) and key_dic[key] == []:
                    self.__dict__[key] = {}
                else:
                    self.__dict__[key] = key_dic[key]


def load_any(data, **kwargs):
    """
    Load (reconstruct) a BIMMS object, list, or mapping from serialized data.

    This helper is used by :meth:`BIMMS_class.load` to reconstruct nested BIMMS
    structures stored as JSON-compatible dictionaries.

    Parameters
    ----------
    data : dict or str
        Serialized representation to load. If a string is provided, it is treated
        as a JSON filename and loaded with :func:`bimms.backend.file_handler.json_load`.
    **kwargs
        Forwarded to the reconstructed object's :meth:`load` method.

    Returns
    -------
    object
        Reconstructed object. One of:
        - A BIMMS object instance.
        - A list of reconstructed objects.
        - A dict mapping to reconstructed objects.

    Notes
    -----
    Reconstruction of BIMMS objects uses the ``bimms_type`` field and evaluates a
    constructor call in the ``bimms`` module namespace::

        eval('sys.modules["bimms"].' + bimms_type)()

    Only load data from trusted sources.
    """
    if isinstance(data, str):
        key_dic = json_load(data)
    else:
        key_dic = data
    # test if BIMMS class
    if is_BIMMS_class(key_dic) or is_BIMMS_class_list(key_dic):
        bimms_obj = key_dic
    # test if BIMMS dict
    elif is_BIMMS_dict(key_dic):
        bimms_type = key_dic["bimms_type"]
        bimms_obj = eval('sys.modules["bimms"].' + bimms_type)()
        bimms_obj.load(key_dic, **kwargs)
    elif is_BIMMS_dict_dict(key_dic):
        bimms_obj = {}
        for key in key_dic:
            bimms_obj[key] = load_any(key_dic[key], **kwargs)
    elif is_BIMMS_dict_list(key_dic):
        bimms_obj = []
        for i in key_dic:
            bimms_obj += [load_any(i, **kwargs)]
    return bimms_obj
