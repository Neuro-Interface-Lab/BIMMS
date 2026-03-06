"""Configuration helper classes for BIMMS operating modes.

This module defines small container classes used to represent discrete or
range-constrained configuration states within the BIMMS software stack. These
objects are primarily intended to standardize the handling of instrument
settings, allowable operating modes, and parameter validation logic.

The implementation is built on top of :class:`..backend.BIMMS_Class.BIMMS_class`
and preserves the original dynamic behavior of the project codebase.
"""

from ..backend.BIMMS_Class import BIMMS_class
from ..backend.file_handler import json_load


def is_config_mode(obj):
    """Return whether an object is a :class:`config_mode` instance.

    Parameters
    ----------
    obj : object
        Object to be tested.

    Returns
    -------
    bool
        ``True`` when ``obj`` is an instance of :class:`config_mode`,
        otherwise ``False``.
    """
    return isinstance(obj, config_mode)


def is_config_mode_list(obj):
    """Return whether an object is a :class:`config_mode_list` instance.

    Parameters
    ----------
    obj : object
        Object to be tested.

    Returns
    -------
    bool
        ``True`` when ``obj`` is an instance of :class:`config_mode_list`,
        otherwise ``False``.
    """
    return isinstance(obj, config_mode_list)


def is_float_str(string):
    """Test whether a value can be converted to ``float``.

    Parameters
    ----------
    string : object
        Candidate value to evaluate.

    Returns
    -------
    bool
        ``True`` if ``float(string)`` succeeds, ``False`` when a
        :class:`ValueError` is raised. Other exceptions are printed by the
        original implementation.
    """
    try:
        float(string)
        return True
    except ValueError:
        return False
    except Exception as error:
        print("WARING: is_float_str: an exception occurred:", error)
    except Exception as error:
        print("WARING: is_float_str: an exception occurred:", error)


def is_int_str(string):
    """Test whether a value can be interpreted as an integer string.

    The original implementation identifies integer-like values by comparing the
    results of ``int(string)`` and ``float(string)``.

    Parameters
    ----------
    string : object
        Candidate value to evaluate.

    Returns
    -------
    bool
        ``True`` when the value is interpreted as an integer by the original
        comparison rule, otherwise ``False``.
    """
    try:
        return int(string) != float(string)
    except ValueError:
        return False
    except Exception as error:
    # handle the exception
        print("WARING: is_int_str: an exception occurred:", error)
    except Exception as error:
    # handle the exception
        print("WARING: is_int_str: an exception occurred:", error)

class config_mode(BIMMS_class):
    """Represent a discrete configuration parameter with allowed modes.

    The class stores a set of admissible textual modes and a currently selected
    value. Inputs are normalized to uppercase strings to simplify subsequent
    comparisons across the software stack.

    Parameters
    ----------
    *args
        Sequence of allowed mode values. Each value is converted to an
        uppercase string.
    **kwargs
        Optional keyword arguments. When ``default`` is provided, it is used as
        the initial selected mode.

    Attributes
    ----------
    modes : list of str
        List of allowed modes.
    value : str or None
        Currently selected mode.
    default : str or None
        Default mode restored by :meth:`reset`.
    """
    def __init__(self, *args, **kwargs):
        """Initialize the configuration mode container."""
        super().__init__(fixed_attr=False)

        self.modes = []
        self.value = None
        for a in args:
            self.modes += [str(a).upper()]
        
        if self.modes == []:
            self.value = None
        elif "default" in kwargs:
            self(kwargs["default"])
        else:
            self(self.modes[0])
        self.default = self.value
    
    def reset(self):
        """Restore the default mode value.

        Returns
        -------
        None
            The method updates :attr:`value` in place.
        """
        self.value = self.default

    def __call__(self, mode):
        """Set the current mode if the provided value is valid.

        Parameters
        ----------
        mode : object
            Candidate mode value.

        Returns
        -------
        None
            The method updates :attr:`value` in place. If the mode is invalid,
            the original implementation prints a warning and keeps the current
            state unchanged.
        """
        if self.is_mode(mode):
            self.value = str(mode).upper()
        else:
            print("Mode: " +str(self.value))
            print("Warning : mode not found, ", self.value, " mode kept")
            print("Possible modes are :", self.modes)

    def __eq__(self, obj):
        """Compare the current mode with another object.

        Parameters
        ----------
        obj : object
            Object compared after conversion to an uppercase string.

        Returns
        -------
        bool
            ``True`` when the normalized values are identical.
        """
        try:
            return self.value == str(obj).upper()
        except:
            return False

    def __str__(self):
        """Return the current mode as a string.

        Returns
        -------
        str or None
            Current mode value.
        """
        return self.value

    def __repr__(self):
        """Return a detailed string representation of the object.

        Returns
        -------
        str
            Representation including the selected mode and all admissible
            values.
        """
        modes_str = "["
        for mod in self.modes:
            modes_str += str(mod)
            modes_str += ", "
        modes_str = modes_str[:-2] + "]"
        return "['config_mode' : "+ self.value + " "+ modes_str + "]"

    def __int__(self):
        """Convert the current mode to an integer when possible.

        Returns
        -------
        int or None
            Integer-converted mode value when conversion succeeds. Otherwise,
            the original implementation prints a warning and returns ``None``.
        """
        if is_int_str(self.value):
            return int(self.value)
        elif is_float_str(self.value):
            #print('INFO:' + self.value + 'float is converted to int')
            return int(self.value)
        else:
            print("WARNING :", self.value, " cannot be converted to int")

    def __float__(self):
        """Convert the current mode to a floating-point value when possible.

        Returns
        -------
        float or None
            Floating-point-converted mode value when conversion succeeds.
            Otherwise, the original implementation prints a warning and returns
            ``None``.
        """
        if is_float_str(self.value):
            return float(self.value)
        else:
            print("WARNING :", self.value, " cannot be converted to float")


    def get_modes(self, verbose=True):
        """Return the list of allowed modes.

        Parameters
        ----------
        verbose : bool, optional
            If ``True``, print the mode list before returning it.

        Returns
        -------
        list of str
            Allowed modes stored in :attr:`modes`.
        """
        if verbose:
            print(self.modes)
        return self.modes

    def is_mode(self, obj):
        """Test whether an object matches one of the allowed modes.

        Parameters
        ----------
        obj : object
            Candidate mode value.

        Returns
        -------
        bool
            ``True`` if the uppercase string representation of ``obj`` belongs
            to :attr:`modes`.
        """
        return str(obj).upper() in self.modes



class config_range(config_mode):
    """Represent a configuration parameter constrained to a numeric interval.

    This subclass extends :class:`config_mode` by replacing discrete membership
    with interval validation. The two positional arguments define the lower and
    upper bounds of the admissible range.

    Parameters
    ----------
    *args
        Lower and upper bound of the interval. If omitted, the default range is
        ``[0, 1]``.
    **kwargs
        Optional keyword arguments passed to :class:`config_mode`.

    Attributes
    ----------
    valuetype : {'int', 'float'}
        Numeric type inferred from the input bounds.
    min : int or float
        Lower bound of the admissible interval.
    max : int or float
        Upper bound of the admissible interval.
    """
    def __init__(self, *args, **kwargs):
        """Initialize the range-constrained configuration object."""
        if len(args) == 0:
            args = [0, 1]
        else:
            assert(len(args)==2)
        if is_int_str(args[0]) and is_int_str(args[1]):
            self.valuetype = "int"
        elif is_float_str(args[0]) and is_float_str(args[1]):
            self.valuetype = "float"
        else:
            print("ERROR: config_range argument should be cinvertible in float or int")
            exit()
        self.min = min(self.__convert_val(args[0]), self.__convert_val(args[1]))
        self.max = max(self.__convert_val(args[0]), self.__convert_val(args[1]))
        super().__init__(*args, **kwargs)

    def __convert_val(self, value):
        """Convert a value to the inferred numeric type.

        Parameters
        ----------
        value : object
            Value to convert.

        Returns
        -------
        int or float
            Converted numeric value.
        """
        return eval(self.valuetype + "(" + str(value) + ")")

    def is_mode(self, obj):
        """Test whether a value lies within the configured numeric interval.

        Parameters
        ----------
        obj : object
            Candidate value.

        Returns
        -------
        bool
            ``True`` when the converted value belongs to the interval
            ``[min, max]``, otherwise ``False``.
        """
        obj_str = str(obj).upper()
        try:
            val = self.__convert_val(obj_str)
            return val >= self.min and val <= self.max
        except:
            return False


class config_mode_list(BIMMS_class):
    """Container storing several named configuration mode objects.

    The class behaves as a lightweight registry that exposes each inserted mode
    object as a dynamic attribute while preserving insertion order in the
    internal :attr:`list` attribute.

    Parameters
    ----------
    data : object, optional
        Reserved parameter kept for API compatibility. It is not used by the
        current implementation.

    Attributes
    ----------
    list : list of str
        Ordered list of registered configuration names.
    N_list : int
        Number of registered configuration entries.
    """
    def __init__(self, data=None):
        """Initialize an empty configuration mode registry."""
        super().__init__(fixed_attr=False)
        self.list = []
        self.N_list = 0


    def add_mode(self, name, mode):
        """Insert a configuration mode object into the registry.

        Parameters
        ----------
        name : str
            Attribute name associated with the mode.
        mode : config_mode or object
            Mode object to store.

        Returns
        -------
        None
            The registry is updated in place. If the name already exists, the
            original implementation emits a warning and overwrites the entry.
        """
        name = str(name)
        if name in self.__dict__:
            self.N_list -= 1
            print("WARNING: config mode already in list")
        self.list += [name]
        self.__dict__[name] = mode
        self.N_list += 1

    def reset(self):
        """Reset all registered mode objects to their default values.

        Returns
        -------
        None
            Each stored configuration object is reset in place.
        """
        for c in self.list:
            self.__dict__[c].reset()

    def __str__(self) -> str:
        """Return a human-readable summary of stored configuration values.

        Returns
        -------
        str
            Multiline summary with one ``name: value`` pair per line.
        """
        string = ""
        for c in self.list:
            string += c + ": " + str(self.__dict__[c]) + "\n"
        return string

    def __eq__(self, __value: object) -> bool:
        """Compare two configuration mode registries.

        Parameters
        ----------
        __value : object
            Object compared against the current registry.

        Returns
        -------
        bool
            ``True`` when both objects are configuration registries containing
            the same ordered names and equal associated values.
        """
        if not is_config_mode_list(__value):
            return False
        if not self.list == __value.list:
            return False
        for c in self.__dict__:
            if not self.__dict__[c] == __value.__dict__[c]:
                return False
        return True
