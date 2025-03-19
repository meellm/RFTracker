import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lib.BluetoothModule import Bluetooth

bluetooth_module        = Bluetooth(bluetooth_port = 4, server_address = "XX:XX:XX:XX:XX:XX")

def setup():
    bluetooth_module.start_server()

def loop():
    try:
        while True:
            data = bluetooth_module.receive_data()
            if data:
                print(data)
    except (OSError, KeyboardInterrupt):
        print("CONNECTION LOST")
    finally:
        bluetooth_module.close_server()

if __name__ == "__main__":
    setup()
    loop()
