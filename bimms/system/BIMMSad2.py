"""Analog Discovery 2 communication layer for BIMMS.

This module provides low-level wrappers around the Digilent Analog Discovery 2
through the :mod:`andi` package. It exposes digital I/O, SPI, analog input,
analog output, and trigger primitives required by the BIMMS instrumentation
stack.
"""
from abc import abstractmethod
import sys
import os
import andi as ai
import os
from warnings import warn

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from ..backend.BIMMS_Class import BIMMS_class
from ..utils.functions import convert
from ..utils import constants as cst


### verbosity of the verbosity
verbose = True

def set_bit(value, bit):
    """
    Set a bit in an integer bit field.

    Parameters
    ----------
    value : int
        Input integer.
    bit : int
        Bit position to set.

    Returns
    -------
    int
        Updated integer with the selected bit forced to ``1``.
    """
    return value | (1<<bit)

def clear_bit(value, bit):
    """
    Clear a bit in an integer bit field.

    Parameters
    ----------
    value : int
        Input integer.
    bit : int
        Bit position to clear.

    Returns
    -------
    int
        Updated integer with the selected bit forced to ``0``.
    """
    return value & ~(1<<bit)

def toggle_bit(value, bit):
    """
    Toggle a bit in an integer bit field.

    Parameters
    ----------
    value : int
        Input integer.
    bit : int
        Bit position to toggle.

    Returns
    -------
    int
        Updated integer with the selected bit inverted.
    """
    return(value ^  (1<<(bit)))


##############################
## CLASS FOR BIMMS HANDLING ##
##############################
class BIMMSad2(BIMMS_class):
    """
    Abstract Analog Discovery 2 backend for BIMMS.

    This class encapsulates communication with the Digilent Analog Discovery 2 and
    provides the low-level digital, SPI, acquisition, and waveform-generation
    operations required by the BIMMS hardware stack.
    """
    @abstractmethod
    def __init__(self, bimms_id=None, serialnumber=None):
        """
        Open the Analog Discovery 2 and initialize BIMMS I/O resources.

        Parameters
        ----------
        bimms_id : int, optional
            BIMMS board identifier associated with a registered instrument serial
            number.
        serialnumber : str, optional
            Explicit Analog Discovery 2 serial number.

        Notes
        -----
        The constructor initializes digital I/O, queries analog-input capabilities, and
        sets a conservative default input range with averaging enabled.
        """
        super().__init__()
        # To maintain connection use keep_on
        self.switch_off = True
        self.ad2_on = False
        
        self.__start_ad2(bimms_id=bimms_id, serialnumber=serialnumber)
        self.__DIO_init()
        
        self.AD2_input_Fs_max = self.ad2.in_frequency_info()[-1]        #Maximum input sampling frequency
        self.AD2_input_buffer_size = self.ad2.in_buffer_size_info()[-1] #Maximum input buffer size 
        available_ranges = self.AD2_get_input_ranges()
        self.AD2_input_range = min(available_ranges)                    #Both AD2 Input range are set to min by default (should be about 2.0V)
        self.AD2_set_input_range(-1,self.AD2_input_range)
        self.AD2_input_average_filter()


    def __start_ad2(self, bimms_id, serialnumber):
        """
        Create the :mod:`andi` device handle.

        Parameters
        ----------
        bimms_id : int or None
            Registered BIMMS identifier.
        serialnumber : str or None
            Serial number used to select a specific Analog Discovery 2.

        Returns
        -------
        None
        """
        selected = False
        if isinstance(bimms_id, int):
            if bimms_id in cst.BimmsSerialNumbers:
                self.serialnumber = cst.BimmsSerialNumbers[bimms_id]
                selected = True
            else:
                print(
                    "warning 'bimms_id' not referentced: first device will be selected"
                )
                exit()
        elif isinstance(serialnumber, str):
            if serialnumber in cst.BimmsSerialNumbers.values():
                self.serialnumber = serialnumber
                selected = True
            else:
                print(
                    "warning 'serialnumber' not referentced: first device will be selected"
                )
                exit()

        if selected:
            self.ad2 = ai.Andi(self.serialnumber)
        else:
            self.ad2 = ai.Andi()
            self.serialnumber = self.ad2.serialnumber
        self.ad2_on = True
        if verbose:
            print("ad2 device opened")
        self.ID = 0

        
    def __del__(self):
        """
        Close the Analog Discovery 2 on object destruction when allowed.
        """
        if self.switch_off and self.ad2_on:
            self.close()


    def close(self):
        """
        Close the active Analog Discovery 2 session.

        Returns
        -------
        None
        """
        self.ad2.close()
        self.ad2_on = False
        if verbose:
            print("ad2 device closed")

    def keep_on(self):
        """
        Disable automatic device shutdown on object deletion.
        """
        self.switch_off = False

    def keep_off(self):
        """
        Enable automatic device shutdown on object deletion.
        """
        self.switch_off = True


    #################################
    ## SPI communitation methods ##
    #################################
    def SPI_init(self, clk, clk_p, mosi_p, miso_p, cs_p):
        """
        Initialize an SPI bus on the Analog Discovery 2.

        Parameters
        ----------
        clk : float
            SPI clock frequency.
        clk_p : int
            Digital pin used as SPI clock.
        mosi_p : int
            Digital pin used as MOSI.
        miso_p : int
            Digital pin used as MISO.
        cs_p : int
            Digital pin used as chip select.

        Returns
        -------
        None
        """
        self.ad2.SPI_reset()
        self.ad2.set_SPI_frequency(clk)
        self.ad2.set_SPI_Clock_channel(clk_p)
        self.ad2.set_SPI_Data_channel(ai.SPIDataIdx["DQ0_MOSI_SISO"], mosi_p)
        self.ad2.set_SPI_Data_channel(ai.SPIDataIdx["DQ1_MISO"], miso_p)
        self.ad2.set_SPI_mode(ai.SPIMode["CPOL_1_CPA_1"])
        self.ad2.set_SPI_MSB_first()
        self.ad2.set_SPI_CS(cs_p, ai.LogicLevel["H"])  

    def SPI_write_32(self, cs_p, value):
        """
        Transmit a 32-bit word over SPI.

        Parameters
        ----------
        cs_p : int
            Chip-select pin used for the transaction.
        value : int
            Unsigned 32-bit value to transmit.

        Returns
        -------
        None
        """
        tx_8bvalues = convert(value)
        self.ad2.set_SPI_CS(cs_p, ai.LogicLevel["H"])  #required if an other CS pin is also used (ex: tomoBIMMS)
        self.ad2.SPI_select(cs_p, ai.LogicLevel["L"])
        for k in tx_8bvalues:
            self.ad2.SPI_write_one(ai.SPI_cDQ["MOSI/MISO"], 8, k)
        self.ad2.SPI_select(cs_p, ai.LogicLevel["H"])

    def SPI_read_32(self, cs_p):
        """
        Read a 32-bit word over SPI.

        Parameters
        ----------
        cs_p : int
            Chip-select pin used for the transaction.

        Returns
        -------
        int
            Unsigned 32-bit value assembled from four successive 8-bit reads.
        """
        offsets = [2**24, 2**16, 2**8, 2**0]
        value = 0
        self.ad2.set_SPI_CS(cs_p, ai.LogicLevel["H"])  #required if an other CS pin is also used (ex: tomoBIMMS)
        self.ad2.SPI_select(cs_p, ai.LogicLevel["L"])
        for k in offsets:
            rx = self.ad2.SPI_read_one(ai.SPI_cDQ["MOSI/MISO"], 8)
            value += rx * k
        self.ad2.SPI_select(cs_p, ai.LogicLevel["H"])
        return value

    ############################
    ## AD2 Digital IO methods ##
    ############################
    def __DIO_init(self):
        """
        Initialize the digital I/O subsystem of the Analog Discovery 2.
        """
        self.ad2.configure_digitalIO()

    def set_IO(self,IO_pin,state):
        """
        Write a digital output state on a selected pin.

        Parameters
        ----------
        IO_pin : int
            Digital I/O pin index.
        state : int
            Logic state, typically ``0`` or ``1``.

        Returns
        -------
        None
        """
        IO = self.ad2.digitalIO_read_outputs()
        if(state==1):
            IO = set_bit(IO,IO_pin)
        else:
            IO = clear_bit(IO,IO_pin)
        self.ad2.digitalIO_output(IO)

    def toggle_IO(self,IO_pin):
        """
        Toggle the current logic state of a selected digital output pin.

        Parameters
        ----------
        IO_pin : int
            Digital I/O pin index.

        Returns
        -------
        None
        """
        IO = self.ad2.digitalIO_read_outputs()
        IO = toggle_bit(IO,IO_pin)
        self.ad2.digitalIO_output(IO)

    ###################
    ## AD2 Analog IN ##
    ###################

    def AD2_get_input_ranges(self):
        """
        Return the supported analog-input ranges.

        Returns
        -------
        tuple or list
            Range values reported by the Analog Discovery 2 backend.
        """
        return(self.ad2.in_channel_range_info(-1))

    def AD2_set_input_range(self,channel,range):
        """
        Set the analog-input voltage range.

        Parameters
        ----------
        channel : int
            Input channel index. A negative value may be used by the backend to target
            all channels.
        range : float
            Full-scale input range in volts.

        Returns
        -------
        None
        """
        self.ad2.in_channel_range_set(channel,range)

    def AD2_input_decimate_filter(self):
        """
        Select the decimation filter mode for analog acquisition.
        """
        self.ad2.in_decimate_filter_mode(-1)

    def AD2_input_average_filter(self):
        """
        Select the averaging filter mode for analog acquisition.
        """
        self.ad2.in_average_filter_mode(-1)

    def set_acquistion(self,fs,size):
        """
        Configure the acquisition engine.

        Parameters
        ----------
        fs : float
            Sampling frequency in samples per second.
        size : int
            Number of samples to acquire.

        Returns
        -------
        object
            Backend-specific acquisition configuration result.
        """
        return(self.ad2.set_acq(freq=fs, samples=size))

    def get_input_fs (self):
        """
        Get the active analog-input sampling frequency.

        Returns
        -------
        float
            Sampling frequency in samples per second.
        """
        return(self.ad2.in_sampling_freq_get())
    
    def get_input_data(self):
        """
        Acquire data from the two analog input channels.

        Returns
        -------
        tuple
            Two-channel acquisition returned by the Analog Discovery 2 backend.
        """
        chan1, chan2 = self.ad2.acq()
        return(chan1,chan2)


    ####################
    ## AD2 Analog OUT ##
    ####################

    def AWG_sine(self,freq, amp ,offset=0, phase=0 ,symmetry=50,activate = False):
        """
        Configure a sinusoidal excitation waveform.

        Parameters
        ----------
        freq : float
            Waveform frequency in hertz.
        amp : float
            Waveform amplitude.
        offset : float, optional
            DC offset applied to the waveform.
        phase : float, optional
            Initial phase of the waveform.
        symmetry : float, optional
            Symmetry parameter forwarded to the backend.
        activate : bool, optional
            Requested activation state.

        Returns
        -------
        None
        """
        self.ad2.sine(channel=cst.AD2_AWG_ch, freq=freq, amp=amp,activate = False,offset = offset, phase = phase,
                        symmetry = symmetry)

    def AWG_custom(self, fs, data):
        """
        Configure a custom arbitrary waveform.

        Parameters
        ----------
        fs : float
            Arbitrary waveform sample rate.
        data : array_like
            Sequence of waveform samples.

        Returns
        -------
        None
        """
        self.ad2.custom(channel=cst.AD2_AWG_ch, fs=fs, data=data)
        
    def AWG_enable(self,enable):
        """
        Enable or disable the active analog output channel.

        Parameters
        ----------
        enable : bool
            Desired output state.

        Returns
        -------
        None
        """
        if (enable == True):
            self.ad2.out_channel_on(cst.AD2_AWG_ch)
        else:
            self.ad2.out_channel_off(cst.AD2_AWG_ch)
            


    ####################
    ## AD2 Triggers   ##
    ####################

    def Set_AWG_trigger(self,type="Rising",ref="left border", delay=0):
        """
        Configure the trigger condition for the waveform generator.

        Parameters
        ----------
        type : str, optional
            Trigger edge or type identifier.
        ref : str, optional
            Trigger reference position.
        delay : float, optional
            Trigger position or delay parameter.

        Returns
        -------
        None
        """
        self.ad2.set_AWG_trigger(cst.AD2_AWG_ch,type="Rising",ref="left border", position=delay)
    
    
    def Set_AUTO_trigger(self,timeout=0.1, type="Rising", ref="center"):
        """
        Configure an automatic analog-input trigger.

        Parameters
        ----------
        timeout : float, optional
            Trigger timeout in seconds.
        type : str, optional
            Trigger edge or type identifier.
        ref : str, optional
            Trigger reference position.

        Returns
        -------
        None
        """
        self.ad2.set_Auto_chan_trigger(0, timeout=0.1, type="Rising", ref="center")

