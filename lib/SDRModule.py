from rtlsdr import RtlSdr
import numpy as np

class SDRModule:
    def __init__(self, sample_rate, center_freq, gain, default_sample_number):
        try:
            self.sdr = RtlSdr()
        except:
            print("SDR not FOUND")

        self.sdr.gain = gain
        self.sdr.sample_rate = sample_rate
        self.sdr.center_freq = center_freq
        self.default_sample_number = default_sample_number

    def signal_receive(self, sample_number=None):
        if sample_number is None:
            return self.sdr.read_samples(self.default_sample_number * 1024)

        return self.sdr.read_samples(sample_number * 1024)

    def find_signal_power(self, signal):
        power = np.abs(signal) ** 2
        filtered_power = self.filter_signal_power(power, threshold = 2)
        average_power = np.mean(filtered_power) if filtered_power.size > 0 else np.mean(power)

        return average_power

    def filter_signal_power(self, signal_power, threshold=1):
        median_val = np.median(signal_power)
        std_val = np.std(signal_power)
        filtered_power = signal_power[(signal_power > median_val - threshold * std_val) & (signal_power < median_val + threshold * std_val)]
        if filtered_power.size == 0:
            return signal_power

        return filtered_power

    def signal_power_to_dbm(self, signal, impedance=50):
        average_power = self.find_signal_power(signal)
        if average_power <= 0:
            average_dbm = -np.inf
        else:
            average_watts = average_power / impedance
            average_dbm = 10 * np.log10(average_watts * 1000.0)

        return average_dbm
