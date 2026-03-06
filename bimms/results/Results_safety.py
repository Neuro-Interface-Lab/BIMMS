import numpy as np
from scipy.fftpack import fft, ifft

from ..backend.BIMMS_Class import BIMMS_class, abstractmethod, is_BIMMS_class

"""from ..system.BIMMScalibration import BIMMScalibration
from ..utils import constants as BIMMScst
import matplotlib.pyplot as plt"""


class BIMMS_results(BIMMS_class, dict):
    """
    Results class for BIMMS
    """

    def __init__(self, config=None, raw_data=None, ID=0):
        super().__init__()
        self.config = {}
        self.raw_data = {}

        self.__set_config(config)
        self.__set_raw_data(raw_data)
        self.__sync()

    def __set_config(self, config):
        if config is None:
            config = {}
        elif is_BIMMS_class(config):
            config = config.save(save=False)
        if "bimms_type" in config:
            config["result_type"] = config.pop("bimms_type")
        self.update({"config": config})

    def __set_raw_data(self, raw_data):
        if raw_data is None:
            raw_data = {}
        self.update({"raw_data": raw_data})

    def save(self, save=False, fname="bimms_save.json", blacklist=[], **kwargs):
        self.__sync()
        bl = [b for b in blacklist]
        bl += ["BIMMS"]
        return super().save(save, fname, bl, **kwargs)

    def load(self, data, blacklist=[], **kwargs):
        super().load(data, blacklist, **kwargs)
        self.__sync()

    def __setitem__(self, key, value):
        if not key == "bimms_type":
            self.__dict__[key] = value
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if not key == "bimms_type":
            del self.__dict__[key]
        super().__delitem__(key)

    def update(self, __m, **kwargs) -> None:
        """
        overload of dict update method to update both attibute and items
        """
        self.__dict__.update(__m, **kwargs)
        super().update(__m, **kwargs)

    def __sync(self):
        self.update(self.__dict__)
        self.pop("__BIMMSObject__")


class Results_test(BIMMS_results):
    def __init__(self, ID=0):
        super().__init__(ID=ID)


class bode_results(BIMMS_results):
    """ """

    def __init__(self, BIMMS=None, data=None, ID=0):
        super().__init__(config=BIMMS.config, raw_data=data, ID=ID)
        self.BIMMS = BIMMS
        self["freq"] = self.raw_data["freq"]
        self["mag_ch1_raw"] = self.raw_data["mag_ch1_raw"]
        self["mag_ch2_raw"] = self.raw_data["mag_ch1_raw"] / self.raw_data["mag_raw"]
        self["phase_raw"] = self.raw_data["phase_raw"]
        if self.BIMMS.calibrated:
            pass
        else:
            self["V_readout"] = self["mag_ch1_raw"] / self.BIMMS.cal_ch1_gain
            self["I_readout"] = self["mag_ch2_raw"] / (
                self.BIMMS.cal_ch2_gain * self.BIMMS.cal_TIA_gain
            )

    def update(self, __m, **kwargs) -> None:
        if isinstance(__m, bode_results):
            if len(__m["freq"]) == 1:
                self["freq"] = np.concatenate([self["freq"], __m["freq"]])
                self["mag_ch1_raw"] = np.concatenate(
                    [self["mag_ch1_raw"], __m["mag_ch1_raw"]]
                )
                self["mag_ch2_raw"] = np.concatenate(
                    [self["mag_ch2_raw"], __m["mag_ch2_raw"]]
                )
                self["phase_raw"] = np.concatenate([self["phase_raw"], __m["phase_raw"]])
                self["V_readout"] = np.concatenate([self["V_readout"], __m["V_readout"]])
                self["I_readout"] = np.concatenate([self["I_readout"], __m["I_readout"]])

            else:
                self["mag_ch1_raw"] = np.vstack(
                    [self["mag_ch1_raw"], __m["mag_ch1_raw"]]
                )
                self["mag_ch2_raw"] = np.vstack(
                    [self["mag_ch2_raw"], __m["mag_ch2_raw"]]
                )
                self["phase_raw"] = np.vstack([self["phase_raw"], __m["phase_raw"]])
                self["V_readout"] = np.vstack([self["V_readout"], __m["V_readout"]])
                self["I_readout"] = np.vstack([self["I_readout"], __m["I_readout"]])
        else:
            super().update(__m, **kwargs)

    def EIS(self):
        print("WARNING: EIS measure not fully implemented")
        self["mag_Z"] = self["V_readout"] / self["I_readout"]
        self["phase_Z"] = self["phase_raw"] - 180
        # results['mag'] = data['']
        return self["mag_Z"], self["phase_Z"]


class temporal_results(BIMMS_results):
    """ """

    def __init__(self, BIMMS=None, data=None, ID=0):
        if BIMMS is not None:
            config = BIMMS.config
        else:
            config = BIMMS
        super().__init__(config=config, raw_data=data, ID=ID)
        self.BIMMS = BIMMS

        # print("WARNING: temporal post-processing measure not fully implemented")
        self["t_raw"] = np.array([])
        self["chan2_raw"] = np.array([])
        self["chan1_raw"] = np.array([])
        self["dt"] = 0
        self["sample_rate"] = 0
        self["n_sample"] = 0
        self.__set_data()

        self["single_meas"] = True

    def __set_data(self):
        if self.raw_data != {}:
            self["t_raw"] = np.array(self.raw_data["t"])
            self["chan2_raw"] = np.array(self.raw_data["chan2"])
            self["chan1_raw"] = np.array(self.raw_data["chan1"])
            self["dt"] = self.t_raw[1] - self.t_raw[0]
            self["sample_rate"] = 1 / self.dt
            self["n_sample"] = len(self.t_raw)

    def load(self, data, blacklist=[], **kwargs):
        super().load(data, blacklist, **kwargs)
        self.__set_data()


    def update(self, __m, **kwargs) -> None:
        if isinstance(__m, temporal_results):
            if np.shape(self["t_raw"])[-1] == np.shape(__m["t_raw"])[-1]:
                # self['t'] = np.vstack((self['t'], __m['t']))
                self["chan2_raw"] = np.vstack((self["chan2_raw"], __m["chan2_raw"]))
                self["chan1_raw"] = np.vstack((self["chan1_raw"], __m["chan1_raw"]))
                self["single_meas"] = False
        else:
            super().update(__m, **kwargs)

    ######################################
    #######  post proc functions  ########
    ######################################

    def crop_time(self, t_start=None, t_stop=None):
        t1 = t_start or self["t_raw"][0]
        t2 = t_stop or self["t_raw"][-1]

        I = np.argwhere((self.t_raw >= t1) & (self.t_raw < t2))[:, 0]

        self["t"] = self["t_raw"][I]
        self["n_sample"] = len(I)
        if self.single_meas:
            self["chan1_t"] = self["chan1_raw"][I]
            self["chan2_t"] = self["chan2_raw"][I]
        else:
            self["chan1_t"] = self["chan1_raw"][:, I]
            self["chan2_t"] = self["chan2_raw"][:, I]

    def fft(self, t_start=None, t_stop=None):
        self.crop_time(t_start=t_start, t_stop=t_stop)
        T = self["n_sample"] / (self["sample_rate"])
        self["f"] = np.arange(self["n_sample"]) / T
        print(self["f"])
        self["chan1_f"] = fft(self["chan1_t"])
        self["chan2_f"] = fft(self["chan2_t"])

    def ifft(self):
        if "chan1_f":
            self["chan1_t"] = ifft(self["chan1_f"])
            self["chan2_t"] = ifft(self["chan2_f"])

    def fft_filter(self, fmin=None, fmax=None):
        fmin = fmin or 0
        fmax = fmax or np.inf
        if "chan2_f" not in self:
            self.fft()
        I = np.where((self["f"] > fmin) & (self["f"] < fmax))
        self["chan1_f"][~I] *= 0
        self["chan2_f"][~I] *= 0
        self.ifft()

    def amp_freq(self, freq):
        I = np.isclose(self.f, freq, rtol=0.1)
        return np.abs(self["chan1_f"][:, I]).max(axis=1) / self["n_sample"]
