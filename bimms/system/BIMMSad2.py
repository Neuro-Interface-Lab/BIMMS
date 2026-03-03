"""
    Python library to use BIMMS measurement setup
    Authors: Florian Kolbl / Louis Regnacq
    (c) ETIS - University Cergy-Pontoise
        IMS - University of Bordeaux
        CNRS

    Requires:
        Python 3.6 or higher
        Analysis_Instrument - class handling Analog Discovery 2 (Digilent)

    Dev notes:
        - LR: in BIMMS_constants, IO15 change with IO7 because hardware issue.  
        - LR: TIA relay modified too

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
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def toggle_bit(value, bit):
    return(value ^  (1<<(bit)))


##############################
## CLASS FOR BIMMS HANDLING ##
##############################
class BIMMSad2(BIMMS_class):
    @abstractmethod
    def __init__(self, bimms_id=None, serialnumber=None):
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
        if self.switch_off and self.ad2_on:
            self.close()


    def close(self):
        self.ad2.close()
        self.ad2_on = False
        if verbose:
            print("ad2 device closed")

    def keep_on(self):
        self.switch_off = False

    def keep_off(self):
        self.switch_off = True


    #################################
    ## SPI communitation methods ##
    #################################
    def SPI_init(self, clk, clk_p, mosi_p, miso_p, cs_p):
        """
        init an spi communication
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
        """ """
        tx_8bvalues = convert(value)
        self.ad2.set_SPI_CS(cs_p, ai.LogicLevel["H"])  #required if an other CS pin is also used (ex: tomoBIMMS)
        self.ad2.SPI_select(cs_p, ai.LogicLevel["L"])
        for k in tx_8bvalues:
            self.ad2.SPI_write_one(ai.SPI_cDQ["MOSI/MISO"], 8, k)
        self.ad2.SPI_select(cs_p, ai.LogicLevel["H"])

    def SPI_read_32(self, cs_p):
        """ """
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
        self.ad2.configure_digitalIO()

    def set_IO(self,IO_pin,state):
        IO = self.ad2.digitalIO_read_outputs()
        if(state==1):
            IO = set_bit(IO,IO_pin)
        else:
            IO = clear_bit(IO,IO_pin)
        self.ad2.digitalIO_output(IO)

    def toggle_IO(self,IO_pin):
        IO = self.ad2.digitalIO_read_outputs()
        IO = toggle_bit(IO,IO_pin)
        self.ad2.digitalIO_output(IO)

    ###################
    ## AD2 Analog IN ##
    ###################

    def AD2_get_input_ranges(self):
        return(self.ad2.in_channel_range_info(-1))

    def AD2_set_input_range(self,channel,range):
        self.ad2.in_channel_range_set(channel,range)

    def AD2_input_decimate_filter(self):
        self.ad2.in_decimate_filter_mode(-1)

    def AD2_input_average_filter(self):
        self.ad2.in_average_filter_mode(-1)

    def set_acquistion(self,fs,size):
        return(self.ad2.set_acq(freq=fs, samples=size))

    def get_input_fs (self):
        return(self.ad2.in_sampling_freq_get())
    
    def get_input_data(self):
        chan1, chan2 = self.ad2.acq()
        return(chan1,chan2)


    ####################
    ## AD2 Analog OUT ##
    ####################

    def AWG_sine(self,freq, amp ,offset=0, phase=0 ,symmetry=50,activate = False):
        self.ad2.sine(channel=cst.AD2_AWG_ch, freq=freq, amp=amp,activate = False,offset = offset, phase = phase,
                        symmetry = symmetry)

    def AWG_custom(self, fs, data):
        self.ad2.custom(channel=cst.AD2_AWG_ch, fs=fs, data=data)
        
    def AWG_enable(self,enable):
        if (enable == True):
            self.ad2.out_channel_on(cst.AD2_AWG_ch)
        else:
            self.ad2.out_channel_off(cst.AD2_AWG_ch)
            


    ####################
    ## AD2 Triggers   ##
    ####################

    def Set_AWG_trigger(self,type="Rising",ref="left border", delay=0):
        self.ad2.set_AWG_trigger(cst.AD2_AWG_ch,type="Rising",ref="left border", position=delay)
    
    
    def Set_AUTO_trigger(self,timeout=0.1, type="Rising", ref="center"):
        self.ad2.set_Auto_chan_trigger(0, timeout=0.1, type="Rising", ref="center")

