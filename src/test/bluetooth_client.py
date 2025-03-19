import os
import sys
import socket
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from lib.BluetoothModule import Bluetooth

bluetooth_module        = Bluetooth(bluetooth_port = 4, server_address = "XX:XX:XX:XX:XX:XX")
my_data = ""

def setup():
    bluetooth_module.connect_server()

def loop():
    try:
        while True:
            my_data = input("Enter data: ")
            if my_data:
                bluetooth_module.send_data(my_data)
                my_data = ""
    except(socket.error, OSError):
        print("CONNECTION LOST")
    finally:
        bluetooth_module.disconnect_server()

if __name__ == "__main__":
    setup()
    loop()
