import os
import sys
import time
import threading
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lib.SDRModule import SDRModule
from lib.BluetoothModule import Bluetooth

sdr_module          = SDRModule(sample_rate = 2.4e6, center_freq = 4333e5, gain = 10, default_sample_number = 256)
bluetooth_module    = Bluetooth(bluetooth_port = 4, server_address = "XX:XX:XX:XX:XX:XX")

bluetooth_input = None
bluetooth_output = None
bluetooth_send_flag = False
sdr_save_signal_flag = False

def setup():
    # Start Bluetooth Server
    bluetooth_module.start_server()
    # Start Threads
    bluetooth_receive_handler = threading.Thread(target = bluetooth_receive_handler_thread, daemon = True)
    bluetooth_receive_handler.start()
    bluetooth_send_handler = threading.Thread(target = bluetooth_send_handler_thread, daemon = True)
    bluetooth_send_handler.start()
    sdr_receive_signal_handler = threading.Thread(target = sdr_receive_signal_handler_thread, daemon = True)
    sdr_receive_signal_handler.start()

def loop():
    global sdr_save_signal_flag, bluetooth_input
    while True:
        if bluetooth_input:
            sdr_save_signal_flag = True
            while sdr_save_signal_flag:
                pass
            bluetooth_input = None

def bluetooth_receive_handler_thread():
    global bluetooth_module, bluetooth_input, system_enable
    while True:
        if bluetooth_module.connection_flag:
            data = bluetooth_module.receive_data()
            if data:
                bluetooth_input = data
        time.sleep(0.1)

def bluetooth_send_handler_thread():
    global bluetooth_module, bluetooth_output, bluetooth_send_flag
    while True:
        if bluetooth_module.connection_flag and bluetooth_send_flag:
            bluetooth_module.send_data(bluetooth_output)
            bluetooth_send_flag = False
        time.sleep(0.1)

def sdr_receive_signal_handler_thread():
    global sdr_save_signal_flag, system_enable, signal_buffer, bluetooth_output, bluetooth_send_flag
    while True:
        if sdr_save_signal_flag:
            signal = sdr_module.signal_receive(2560)
            bluetooth_output = sdr_module.find_signal_power(signal)
            sdr_save_signal_flag = False
            bluetooth_send_flag = True
        time.sleep(0.1)

if __name__ == "__main__":
    setup()
    loop()
